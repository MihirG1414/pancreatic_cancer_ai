"""Lazy NIfTI loading, native geometry checks and bounded slice reads."""

import math
import warnings
import zlib
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import psutil
from numpy.typing import NDArray

Volume = nib.Nifti1Image | nib.Nifti2Image
MIB = 1024**2


def _millimetre_factor(image: Volume) -> float:
    return {"meter": 1000.0, "mm": 1.0, "micron": 0.001}.get(image.header.get_xyzt_units()[0], 1.0)


def _affine_mm(image: Volume) -> NDArray[np.float64]:
    affine = image.affine.copy()
    affine[:3] *= _millimetre_factor(image)
    return affine


def memory_status() -> dict[str, float]:
    """Current process working set and system memory, in MiB (not peak use)."""
    memory = psutil.virtual_memory()
    return {
        "process_rss_mib": round(psutil.Process().memory_info().rss / MIB, 1),
        "available_mib": round(memory.available / MIB, 1),
        "total_mib": round(memory.total / MIB, 1),
    }


def load_volume(path: str | Path) -> Volume:
    """Read header/proxy only; preserve the file's native affine and voxels."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Scan/label file not found: {path}")
    if not path.name.lower().endswith((".nii", ".nii.gz")):
        raise ValueError("Expected a NIfTI .nii or .nii.gz file.")
    try:
        image = nib.load(path, mmap="r", keep_file_open=False)
    except (OSError, ValueError, nib.filebasedimages.ImageFileError) as exc:
        raise ValueError("Cannot read NIfTI header; check file integrity and format.") from exc
    if not isinstance(image, (nib.Nifti1Image, nib.Nifti2Image)):
        raise ValueError("Expected a NIfTI image.")
    if len(image.shape) != 3 or any(size <= 0 for size in image.shape):
        raise ValueError(f"Expected one 3D volume; found shape {image.shape}.")
    affine = image.affine
    if (
        not np.isfinite(affine).all()
        or np.linalg.matrix_rank(affine[:3, :3]) < 3
        or not np.allclose(affine[3], [0, 0, 0, 1])
    ):
        raise ValueError("Invalid or singular voxel-to-world affine.")
    if image.get_data_dtype().kind not in "iuf":
        raise ValueError("Expected real numeric CT or label voxels.")
    return image


def geometry_warnings(image: Volume) -> list[str]:
    """Report ambiguous header geometry without changing or repairing it."""
    issues = []
    qform, qcode = image.get_qform(coded=True)
    sform, scode = image.get_sform(coded=True)
    factor = _millimetre_factor(image)
    if not qcode and not scode:
        issues.append("No coded qform/sform; using NiBabel fallback geometry.")
    if (
        qcode
        and scode
        and not np.allclose(qform[:3] * factor, sform[:3] * factor, rtol=0, atol=1e-3)
    ):
        issues.append("Coded qform and sform disagree; NiBabel selects sform.")
    if image.header.get_xyzt_units()[0] == "unknown":
        issues.append("Spatial units are unknown.")
    if not np.allclose(
        np.asarray(image.header.get_zooms()[:3]) * factor,
        nib.affines.voxel_sizes(image.affine) * factor,
        rtol=0,
        atol=1e-4,
    ):
        issues.append("Header voxel spacing and selected affine spacing disagree.")
    return issues


def metadata(image: Volume) -> dict[str, Any]:
    """Return geometry only: deliberately omit identifying free-text headers."""
    count = math.prod(image.shape)
    return {
        "shape": list(image.shape),
        "spacing": [float(x) for x in image.header.get_zooms()[:3]],
        "affine_spacing": nib.affines.voxel_sizes(image.affine).tolist(),
        "spatial_units": image.header.get_xyzt_units()[0],
        "orientation": list(nib.aff2axcodes(image.affine)),
        "affine": image.affine.tolist(),
        "qform_code": int(image.header["qform_code"]),
        "sform_code": int(image.header["sform_code"]),
        "obliquity_degrees": np.rad2deg(nib.affines.obliquity(image.affine)).tolist(),
        "stored_dtype": str(image.get_data_dtype()),
        "estimated_full_float32_mib": round(count * 4 / MIB, 1),
        "full_volume_cached": image.in_memory,
        "warnings": geometry_warnings(image),
    }


def check_geometry(scan: Volume, mask: Volume) -> None:
    """Refuse unsafe overlays; equal array dimensions alone are insufficient."""
    problems = geometry_warnings(scan) + geometry_warnings(mask)
    if scan.shape != mask.shape:
        problems.append("Shape mismatch.")
    if scan.header.get_xyzt_units()[0] != mask.header.get_xyzt_units()[0]:
        problems.append("Spatial units mismatch.")
    if not np.allclose(
        np.asarray(scan.header.get_zooms()[:3]) * _millimetre_factor(scan),
        np.asarray(mask.header.get_zooms()[:3]) * _millimetre_factor(mask),
        rtol=0,
        atol=1e-4,
    ):
        problems.append("Voxel spacing mismatch.")
    if not np.allclose(_affine_mm(scan), _affine_mm(mask), rtol=0, atol=1e-3):
        problems.append("Voxel-to-world affine mismatch (position/direction/spacing).")
    if problems:
        raise ValueError("Cannot overlay: geometry check failed. " + " ".join(problems))


def _read_proxy_slice(image: Volume, axis: int, index: int) -> NDArray[np.float32]:
    """Stream contiguous 2D slabs to avoid full-volume proxy slice read-ahead.

    Other native planes are assembled from one row/column per storage slab using
    a sequential file handle. Public proxy metadata retains endian/order/scaling.
    """
    proxy = image.dataobj
    storage_axis = 2 if proxy.order == "F" else 0
    slab_axes = [i for i in range(3) if i != storage_axis]
    slab_shape = tuple(image.shape[i] for i in slab_axes)
    slab_bytes = math.prod(slab_shape) * proxy.dtype.itemsize
    output_axes = [i for i in range(3) if i != axis]
    plane = np.empty(tuple(image.shape[i] for i in output_axes), dtype=np.float32)
    slabs = [index] if axis == storage_axis else range(image.shape[storage_axis])
    with nib.openers.ImageOpener(proxy.file_like, mode="rb") as source:
        for slab_index in slabs:
            source.seek(proxy.offset + slab_index * slab_bytes)
            raw = source.read(slab_bytes)
            if len(raw) != slab_bytes:
                raise ValueError("Incomplete voxel payload")
            slab = np.ndarray(slab_shape, dtype=proxy.dtype, buffer=raw, order=proxy.order)
            if axis == storage_axis:
                plane[:] = nib.volumeutils.apply_read_scaling(slab, proxy.slope, proxy.inter)
            else:
                selected = np.take(slab, index, axis=slab_axes.index(axis))
                target = [slice(None), slice(None)]
                target[output_axes.index(storage_axis)] = slab_index
                plane[tuple(target)] = nib.volumeutils.apply_read_scaling(
                    selected, proxy.slope, proxy.inter
                )
            del slab, raw
    return plane


def read_slice(image: Volume, axis: int, index: int) -> NDArray[np.float32]:
    """Read a single native plane with NIfTI intensity scaling, without caching."""
    if axis not in (0, 1, 2) or not isinstance(axis, int):
        raise ValueError("Slice axis must be 0, 1 or 2.")
    if not isinstance(index, int) or not 0 <= index < image.shape[axis]:
        raise ValueError(f"Slice index must be between 0 and {image.shape[axis] - 1}.")
    pixels = math.prod(size for i, size in enumerate(image.shape) if i != axis)
    available = psutil.virtual_memory().available
    # Bound output, one raw storage slab, scaling intermediates and plotting buffers.
    slab_bytes = 0
    if nib.is_proxy(image.dataobj):
        storage_axis = 2 if image.dataobj.order == "F" else 0
        slab_bytes = math.prod(s for i, s in enumerate(image.shape) if i != storage_axis)
        slab_bytes *= image.get_data_dtype().itemsize
    if pixels * 32 + slab_bytes * 2 > min(64 * MIB, available // 4):
        raise MemoryError("Insufficient memory budget for this slice; close other apps.")
    if available < 512 * MIB:
        warnings.warn(
            "Less than 512 MiB available; close unused apps before plotting.",
            UserWarning,
            stacklevel=2,
        )
    selection = [slice(None)] * 3
    selection[axis] = index
    try:
        if nib.is_proxy(image.dataobj):
            plane = _read_proxy_slice(image, axis, index)
        else:
            plane = np.asarray(image.dataobj[tuple(selection)], dtype=np.float32)
    except (OSError, ValueError, EOFError, zlib.error) as exc:
        raise ValueError("Cannot read slice; file may be truncated or corrupt.") from exc
    if not np.isfinite(plane).all():
        raise ValueError("Slice contains non-finite intensity values.")
    return plane
