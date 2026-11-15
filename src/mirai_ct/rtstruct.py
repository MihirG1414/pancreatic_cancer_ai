"""Explicit source RTSTRUCT ROI to native-grid reference; never model inference."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import psutil
from numpy.typing import NDArray

from mirai_ct.panorama_io import geometry, sha256_file, write_json
from mirai_ct.volume import check_geometry, load_volume, read_slice

CT_SOP = "1.2.840.10008.5.1.4.1.1.2"
RT_SOP = "1.2.840.10008.5.1.4.1.1.481.3"


def _pydicom() -> Any:
    try:
        import pydicom
    except ImportError as exc:
        raise ValueError(
            "Install optional requirements-reference-io.txt for RTSTRUCT parsing."
        ) from exc
    return pydicom


def polygon_mask(points: NDArray, shape: tuple[int, int]) -> NDArray[np.bool_]:
    """Even-odd polygon interior at native integer centers, including boundary."""
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or not 3 <= len(p) <= 10000 or not np.isfinite(p).all():
        raise ValueError("Invalid finite polygon points.")
    if len(shape) != 2 or any(type(n) is not int or not 1 <= n <= 2048 for n in shape):
        raise ValueError("Unsupported reference plane dimensions.")
    if (p < -0.5).any() or (p > np.asarray(shape) - 0.5).any():
        raise ValueError("Reference contour extends outside the native CT grid.")
    q = np.roll(p, -1, axis=0)
    if abs(np.sum(p[:, 0] * q[:, 1] - q[:, 0] * p[:, 1])) < 1e-8:
        raise ValueError("Degenerate contour has no enclosed area.")
    lo = np.maximum(np.ceil(p.min(axis=0) - 1e-7).astype(int), 0)
    hi = np.minimum(np.floor(p.max(axis=0) + 1e-7).astype(int), np.asarray(shape) - 1)
    result = np.zeros(shape, dtype=bool)
    if (hi < lo).any():
        return result
    x, y = np.ogrid[lo[0] : hi[0] + 1, lo[1] : hi[1] + 1]
    inside = np.zeros(tuple(hi - lo + 1), dtype=bool)
    boundary = np.zeros_like(inside)
    for a, b in zip(p, q, strict=True):
        dx, dy = b - a
        length = float(np.hypot(dx, dy))
        if length < 1e-12:
            continue
        on_line = np.abs(dx * (y - a[1]) - dy * (x - a[0])) <= 1e-7 * length
        boundary |= (
            on_line
            & (x >= min(a[0], b[0]) - 1e-7)
            & (x <= max(a[0], b[0]) + 1e-7)
            & (y >= min(a[1], b[1]) - 1e-7)
            & (y <= max(a[1], b[1]) + 1e-7)
        )
        if dy != 0:
            inside ^= ((a[1] > y) != (b[1] > y)) & (x < a[0] + (y - a[1]) * dx / dy)
    result[lo[0] : hi[0] + 1, lo[1] : hi[1] + 1] = inside | boundary
    return result


def _source_images(
    scan: Any, directory: Path, conversion: dict, inverse_lps: NDArray
) -> tuple[dict[str, int], str, str, str]:
    """Verify native CT provenance and independently bind SOP UIDs to native k."""
    pydicom = _pydicom()
    hashes = conversion.get("source_dicom_sha256")
    if not isinstance(hashes, dict) or len(hashes) != scan.shape[2]:
        raise ValueError("Conversion does not identify every source CT slice.")
    grid = geometry(scan)
    affine_lps = np.asarray(grid["affine_lps_mm"])
    directions = affine_lps[:3, :3] / np.asarray(grid["spacing_mm"])
    images, slices = {}, set()
    identity = None
    for name, digest in hashes.items():
        if Path(name).name != name or ":" in name or "\\" in name:
            raise ValueError("Unsafe source DICOM provenance filename.")
        path = directory / name
        if sha256_file(path) != digest:
            raise ValueError("Source DICOM checksum mismatch.")
        d = pydicom.dcmread(path, stop_before_pixels=True)
        current = (str(d.SeriesInstanceUID), str(d.StudyInstanceUID), str(d.FrameOfReferenceUID))
        if (
            d.Modality != "CT"
            or str(d.SOPClassUID) != CT_SOP
            or int(getattr(d, "NumberOfFrames", 1)) != 1
        ):
            raise ValueError("Reference requires conventional single-frame CT.")
        if identity is not None and current != identity:
            raise ValueError("Source CT identity/frame changes between slices.")
        identity = current
        if current[0] != conversion.get("series_uid"):
            raise ValueError("Source CT series differs from conversion provenance.")
        position = np.asarray(d.ImagePositionPatient, dtype=float)
        index = inverse_lps @ np.r_[position, 1]
        if not np.isfinite(index).all():
            raise ValueError("Invalid source CT slice position.")
        k = int(round(index[2]))
        if not 0 <= k < scan.shape[2] or not np.allclose(index[:3], [0, 0, k], atol=1e-3, rtol=0):
            raise ValueError("Source CT slice position differs from native NIfTI grid.")
        expected_orientation = np.r_[directions[:, 0], directions[:, 1]]
        if (
            [int(d.Columns), int(d.Rows)] != list(scan.shape[:2])
            or not np.allclose(d.ImageOrientationPatient, expected_orientation, atol=1e-5, rtol=0)
            or not np.allclose(
                d.PixelSpacing, np.asarray(grid["spacing_mm"])[[1, 0]], atol=1e-5, rtol=0
            )
        ):
            raise ValueError("Source CT plane geometry differs from native grid.")
        sop = str(d.SOPInstanceUID)
        if sop in images or k in slices:
            raise ValueError("Duplicate CT SOP UID or native slice.")
        images[sop] = k
        slices.add(k)
    if slices != set(range(scan.shape[2])) or identity is None:
        raise ValueError("Incomplete native CT source coverage.")
    return images, *identity


def convert_rtstruct(
    scan_path: Path,
    dicom_directory: Path,
    rtstruct: Path,
    conversion_path: Path,
    output: Path,
    *,
    roi_number: int,
    description: str,
) -> Path:
    """Rasterize one explicitly selected source ROI; preserve physical geometry."""
    if output.exists():
        raise ValueError("Reference output directory already exists; preserve prior results.")
    if type(roi_number) is not int or roi_number < 1 or not description.strip():
        raise ValueError("Explicit positive ROI number and reference description are required.")
    if rtstruct.stat().st_size > 16 * 1024**2 or conversion_path.stat().st_size > 1024**2:
        raise ValueError("Reference/provenance exceeds bounded input size.")
    conversion = json.loads(conversion_path.read_text(encoding="utf-8"))
    source_hash = sha256_file(scan_path)
    if conversion.get("schema_version") != 1 or conversion.get("nifti_sha256") != source_hash:
        raise ValueError("Native CT checksum differs from verified conversion.")
    scan = load_volume(scan_path)
    grid = geometry(scan)
    if math.prod(scan.shape) * 3 + 32 * 1024**2 > psutil.virtual_memory().available // 2:
        raise MemoryError("Insufficient available RAM for bounded reference conversion.")
    inverse_lps = np.linalg.inv(np.asarray(grid["affine_lps_mm"]))
    images, series, study, frame = _source_images(scan, dicom_directory, conversion, inverse_lps)
    ds = _pydicom().dcmread(rtstruct, stop_before_pixels=True)
    if ds.Modality != "RTSTRUCT" or str(ds.SOPClassUID) != RT_SOP:
        raise ValueError("Expected a source DICOM RT Structure Set.")
    definitions = [r for r in ds.StructureSetROISequence if int(r.ROINumber) == roi_number]
    regions = [r for r in ds.ROIContourSequence if int(r.ReferencedROINumber) == roi_number]
    if len(definitions) != 1 or len(regions) != 1:
        raise ValueError("Explicit ROI number is missing or ambiguous.")
    if str(definitions[0].ReferencedFrameOfReferenceUID) != frame:
        raise ValueError("Selected ROI FrameOfReferenceUID differs from the source CT.")
    frames, studies, series_refs = set(), set(), set()
    for f in ds.ReferencedFrameOfReferenceSequence:
        frames.add(str(f.FrameOfReferenceUID))
        for st in f.RTReferencedStudySequence:
            studies.add(str(st.ReferencedSOPInstanceUID))
            for se in st.RTReferencedSeriesSequence:
                series_refs.add(str(se.SeriesInstanceUID))
    if frames != {frame} or studies != {study} or series_refs != {series}:
        raise ValueError("RTSTRUCT CT frame/study/series references do not match the source.")
    contours = regions[0].ContourSequence
    if not 1 <= len(contours) <= 4096:
        raise ValueError("Unsupported reference contour count.")
    types = {str(c.ContourGeometricType) for c in contours}
    if types not in ({"CLOSED_PLANAR"}, {"CLOSEDPLANAR_XOR"}):
        raise ValueError(
            "Only consistent closed planar or closed planar XOR contours are supported."
        )
    validated = []
    for c in contours:
        if hasattr(c, "ContourSlabThickness") or hasattr(c, "ContourOffsetVector"):
            raise ValueError("Contour slab/offset semantics are unsupported; no guessing.")
        count = int(c.NumberOfContourPoints)
        data = np.asarray(c.ContourData, dtype=float)
        if not 3 <= count <= 10000 or data.size != 3 * count or not np.isfinite(data).all():
            raise ValueError("Invalid finite reference contour points.")
        refs = c.ContourImageSequence
        if len(refs) != 1 or str(refs[0].ReferencedSOPClassUID) != CT_SOP:
            raise ValueError("Each contour must reference exactly one conventional CT image.")
        sop = str(refs[0].ReferencedSOPInstanceUID)
        if sop not in images:
            raise ValueError("Contour references a CT image outside the selected source series.")
        ijk = np.c_[data.reshape(-1, 3), np.ones(count)] @ inverse_lps.T
        k = images[sop]
        if not np.allclose(ijk[:, 2], k, atol=1e-3, rtol=0):
            raise ValueError("Contour points do not lie on the referenced native CT plane.")
        # Validate geometry and coverage before allocating/writing the 3D mask.
        polygon_mask(ijk[:, :2], scan.shape[:2])
        validated.append((k, ijk[:, :2]))
    mask = np.zeros(scan.shape, dtype=np.uint8)
    for k, points in validated:
        plane = polygon_mask(points, scan.shape[:2])
        if types == {"CLOSEDPLANAR_XOR"}:
            mask[:, :, k] ^= plane
        else:
            mask[:, :, k] |= plane
    count = int(np.count_nonzero(mask))
    if count == 0:
        raise ValueError(
            "Selected reference contains no native voxel centers; do not infer absence."
        )
    header = scan.header.copy()
    header.set_data_dtype(np.uint8)
    result = type(scan)(mask, scan.affine, header=header)
    result.header.set_slope_inter(1, 0)
    output.mkdir(parents=True)
    path = output / "reference.nii.gz"
    nib.save(result, path)
    saved = load_volume(path)
    check_geometry(scan, saved)
    for k in range(scan.shape[2]):
        if not np.array_equal(read_slice(saved, 2, k), mask[:, :, k]):
            raise ValueError("Saved native reference voxels differ from the derived mask.")
    write_json(
        output / "reference.json",
        {
            "schema_version": 1,
            "source_ct_sha256": source_hash,
            "source_rtstruct_sha256": sha256_file(rtstruct),
            "source_conversion_sha256": sha256_file(conversion_path),
            "reference_sha256": sha256_file(path),
            "roi_number": roi_number,
            "roi_name": str(definitions[0].ROIName),
            "description": description,
            "label_id": 1,
            "contour_count": len(contours),
            "native_slices": sorted({k for k, _ in validated}),
            "voxel_count": count,
            "reference_volume_ml": count
            * abs(float(np.linalg.det(np.asarray(grid["affine_lps_mm"])[:3, :3])))
            / 1000,
            "rasterization": "Native voxel centers; boundary included; no slice interpolation",
            "contour_combination": next(iter(types)),
            "source_image_references_checked": True,
            "all_saved_planes_verified": True,
            "clinical_mask_validation": "not established",
            "pdac_diagnosis": "not inferred from ROI",
            "inference_executed": False,
            "pydicom_version": _pydicom().__version__,
        },
    )
    return path


def load_reference_provenance(scan_path: Path, mask_path: Path | None, path: Path) -> dict:
    """Bind optional report label semantics to the exact source CT and raster."""
    if mask_path is None or path.stat().st_size > 1024**2:
        raise ValueError("Reference provenance requires a mask and bounded metadata.")
    info = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(info, dict)
        or info.get("schema_version") != 1
        or info.get("source_ct_sha256") != sha256_file(scan_path)
        or info.get("reference_sha256") != sha256_file(mask_path)
        or info.get("inference_executed") is not False
        or info.get("label_id") != 1
        or type(info.get("roi_number")) is not int
        or info["roi_number"] < 1
        or any(
            not isinstance(info.get(k), str) or not info[k].strip()
            for k in ("description", "roi_name", "rasterization")
        )
    ):
        raise ValueError("Reference provenance schema, semantics or checksum mismatch.")
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--dicom-dir", type=Path, required=True)
    parser.add_argument("--rtstruct", type=Path, required=True)
    parser.add_argument("--ct-conversion", type=Path, required=True)
    parser.add_argument("--roi-number", type=int, required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(
            convert_rtstruct(
                args.scan,
                args.dicom_dir,
                args.rtstruct,
                args.ct_conversion,
                args.output,
                roi_number=args.roi_number,
                description=args.description,
            )
        )
    except (OSError, ValueError, AttributeError, KeyError, MemoryError) as exc:
        print(f"Reference conversion stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
