"""Conventional single-frame CT series to native NIfTI; no resampling/inference."""

from __future__ import annotations

import argparse
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import psutil

from mirai_ct.panorama_io import sha256_file, simpleitk, write_json
from mirai_ct.volume import load_volume, read_slice


def validate_stack(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Reject irregular, tilted, duplicate and inconsistent conventional CT slices."""
    if not 2 <= len(records) <= 2048:
        raise ValueError("Expected 2–2048 conventional CT slices.")
    first = records[0]
    orientation = np.asarray(first["orientation"], dtype=float)
    if orientation.shape != (6,) or not np.isfinite(orientation).all():
        raise ValueError("Invalid DICOM orientation.")
    x, y = orientation[:3], orientation[3:]
    normal = np.cross(x, y)
    basis = np.column_stack((x, y, normal))
    if not np.allclose(basis.T @ basis, np.eye(3), atol=1e-5, rtol=0):
        raise ValueError("DICOM axes are not orthonormal.")
    spacing = np.asarray(first["pixel_spacing"], dtype=float)
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or (spacing <= 0).any():
        raise ValueError("Invalid DICOM pixel spacing.")
    if any(
        type(first[key]) is not int or not 1 <= first[key] <= 2048 for key in ("rows", "columns")
    ):
        raise ValueError("Unsupported CT plane size.")
    positions, uids = [], set()
    for row in records:
        if row["modality"] != "CT" or row["frames"] != 1:
            raise ValueError("Only conventional single-frame CT is supported.")
        if not row["sop_uid"] or row["sop_uid"] in uids:
            raise ValueError("Missing or duplicate DICOM SOP instance UID.")
        uids.add(row["sop_uid"])
        if any(row[key] != first[key] for key in ("rows", "columns", "slope", "intercept")):
            raise ValueError("Inconsistent CT dimensions or intensity scaling.")
        if (
            not math.isfinite(row["slope"])
            or row["slope"] <= 0
            or not math.isfinite(row["intercept"])
        ):
            raise ValueError("Invalid DICOM intensity scaling.")
        if not np.allclose(row["orientation"], orientation, atol=1e-5, rtol=0):
            raise ValueError("Slice orientation changes within the series.")
        if not np.allclose(row["pixel_spacing"], spacing, atol=1e-5, rtol=0):
            raise ValueError("Pixel spacing changes within the series.")
        position = np.asarray(row["position"], dtype=float)
        if position.shape != (3,) or not np.isfinite(position).all():
            raise ValueError("Invalid DICOM position.")
        positions.append(position)
    positions = np.asarray(positions)
    steps = np.diff(positions, axis=0)
    dz = float(steps[0] @ normal)
    if dz <= 0 or not np.allclose(steps, normal * dz, rtol=0, atol=1e-3):
        raise ValueError(
            "Irregular spacing, duplicate positions or gantry tilt; refusing resampling."
        )
    return {
        "size": [first["columns"], first["rows"], len(records)],
        "spacing": [float(spacing[1]), float(spacing[0]), dz],
        "origin_lps": positions[0].tolist(),
        "direction_lps": basis.ravel().tolist(),
        "hu_calibration": (
            "DICOM rescale type HU; physical calibration unverified"
            if all(row["rescale_type"].upper() == "HU" for row in records)
            else "unknown"
        ),
    }


def _record(path: str) -> dict[str, Any]:
    reader = simpleitk().ImageFileReader()
    reader.SetFileName(path)
    reader.ReadImageInformation()

    def tag(key: str, default: str | None = None) -> str:
        if reader.HasMetaDataKey(key):
            return reader.GetMetaData(key).strip()
        if default is not None:
            return default
        raise ValueError(f"Required DICOM tag missing: {key}")

    return {
        "modality": tag("0008|0060"),
        "sop_uid": tag("0008|0018"),
        "frames": int(tag("0028|0008", "1")),
        "position": [float(v) for v in tag("0020|0032").split("\\")],
        "orientation": [float(v) for v in tag("0020|0037").split("\\")],
        "pixel_spacing": [float(v) for v in tag("0028|0030").split("\\")],
        "rows": int(tag("0028|0010")),
        "columns": int(tag("0028|0011")),
        "slope": float(tag("0028|1053")),
        "intercept": float(tag("0028|1052")),
        "rescale_type": tag("0028|1054", "unknown"),
    }


def convert_series(directory: Path, output: Path, *, expected_series_uid: str) -> Path:
    """Preserve physical grid and GDCM-rescaled intensities; verify every plane."""
    if output.exists():
        raise ValueError("Output directory already exists; preserve the prior conversion.")
    sitk = simpleitk()
    ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(directory))
    if not ids or len(ids) != 1 or ids[0] != expected_series_uid:
        raise ValueError("Expected exactly the explicitly selected DICOM series.")
    files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(directory), expected_series_uid)
    grid = validate_stack([_record(path) for path in files])
    voxels = math.prod(grid["size"])
    budget = voxels * 12 + 32 * 1024**2
    if budget > min(1024**3, psutil.virtual_memory().available // 2):
        raise MemoryError(
            "Insufficient RAM for bounded native DICOM conversion; close unused apps."
        )
    if shutil.disk_usage(directory).free < voxels * 8 + 32 * 1024**2:
        raise OSError("Insufficient disk for native conversion.")
    hashes = {Path(path).name: sha256_file(Path(path)) for path in files}
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    reader.SetNumberOfWorkUnits(1)
    image = reader.Execute()
    for actual, expected in (
        (image.GetSize(), grid["size"]),
        (image.GetSpacing(), grid["spacing"]),
        (image.GetOrigin(), grid["origin_lps"]),
        (image.GetDirection(), grid["direction_lps"]),
    ):
        if not np.allclose(actual, expected, atol=1e-4, rtol=0):
            raise ValueError("GDCM assembled geometry differs from the DICOM slice positions.")
    values = sitk.GetArrayViewFromImage(image)
    for k, path in enumerate(files):
        single = sitk.ReadImage(path)
        if not np.array_equal(
            values[k], sitk.GetArrayViewFromImage(single).reshape(values[k].shape)
        ):
            raise ValueError("Series intensity values differ from independently read source slice.")
    output.mkdir(parents=True)
    destination = output / "ct.nii.gz"
    sitk.WriteImage(image, str(destination), True)
    native = load_volume(destination)
    expected_ras = np.eye(4)
    expected_ras[:3, :3] = (
        np.diag([-1, -1, 1])
        @ np.asarray(grid["direction_lps"]).reshape(3, 3)
        @ np.diag(grid["spacing"])
    )
    expected_ras[:3, 3] = np.diag([-1, -1, 1]) @ np.asarray(grid["origin_lps"])
    if native.shape != tuple(grid["size"]) or not np.allclose(
        native.affine, expected_ras, atol=1e-3, rtol=0
    ):
        raise ValueError("NIfTI native RAS geometry differs from source DICOM LPS geometry.")
    for k in range(native.shape[2]):
        if not np.array_equal(read_slice(native, 2, k), values[k].T):
            raise ValueError("NIfTI conversion changed rescaled CT intensities.")
    write_json(
        output / "conversion.json",
        {
            "schema_version": 1,
            "conversion_kind": "native DICOM CT to NIfTI; no resampling",
            "series_uid": expected_series_uid,
            "source_dicom_sha256": hashes,
            "nifti_sha256": sha256_file(destination),
            "geometry": grid,
            "all_source_planes_verified": True,
            "all_nifti_planes_verified": True,
            "contrast_phase": "unknown; series-description hint requires separate verification",
            "annotation_used": False,
            "inference_executed": False,
        },
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dicom-dir", type=Path, required=True)
    parser.add_argument("--series-uid", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(convert_series(args.dicom_dir, args.output, expected_series_uid=args.series_uid))
    except (OSError, ValueError, RuntimeError, MemoryError) as exc:
        print(f"DICOM intake stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
