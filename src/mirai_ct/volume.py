"""Lazy NIfTI loading, native geometry checks and bounded slice reads."""

import math
import warnings
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import psutil
from numpy.typing import NDArray

Volume = nib.Nifti1Image | nib.Nifti2Image
MIB = 1024**2


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
    if not qcode and not scode:
        issues.append("No coded qform/sform; using NiBabel fallback geometry.")
    if qcode and scode and not np.allclose(qform, sform, rtol=0, atol=1e-3):
        issues.append("Coded qform and sform disagree; NiBabel selects sform.")
    if image.header.get_xyzt_units()[0] == "unknown":
        issues.append("Spatial units are unknown.")
    if not np.allclose(
        image.header.get_zooms()[:3], nib.affines.voxel_sizes(image.affine), rtol=0, atol=1e-4
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
    if not np.allclose(scan.header.get_zooms()[:3], mask.header.get_zooms()[:3], rtol=0, atol=1e-4):
        problems.append("Voxel spacing mismatch.")
    if not np.allclose(scan.affine, mask.affine, rtol=0, atol=1e-3):
        problems.append("Voxel-to-world affine mismatch (position/direction/spacing).")
    if problems:
        raise ValueError("Cannot overlay: geometry check failed. " + " ".join(problems))


def read_slice(image: Volume, axis: int, index: int) -> NDArray[np.float32]:
    """Read a single native plane with NIfTI intensity scaling, without caching."""
    if axis not in (0, 1, 2) or not isinstance(axis, int):
        raise ValueError("Slice axis must be 0, 1 or 2.")
    if not isinstance(index, int) or not 0 <= index < image.shape[axis]:
        raise ValueError(f"Slice index must be between 0 and {image.shape[axis] - 1}.")
    pixels = math.prod(size for i, size in enumerate(image.shape) if i != axis)
    available = psutil.virtual_memory().available
    # Allow for float64 scaling intermediates and plotting buffers, all 2D.
    if pixels * 32 > min(64 * MIB, available // 4):
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
        plane = np.asarray(image.dataobj[tuple(selection)], dtype=np.float32)
    except (OSError, ValueError, EOFError) as exc:
        raise ValueError("Cannot read slice; file may be truncated or corrupt.") from exc
    if not np.isfinite(plane).all():
        raise ValueError("Slice contains non-finite intensity values.")
    return plane
