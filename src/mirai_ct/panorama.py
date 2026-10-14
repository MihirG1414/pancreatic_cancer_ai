"""Validate/import PANORAMA's actual candidate map and scalar score contract."""

import argparse
import json
import math
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np

from mirai_ct.cases import Case
from mirai_ct.panorama_io import (
    geometry,
    read_aligned_mha,
    require_memory,
    select_case,
    sha256_file,
    simpleitk,
    validate_alignment,
    write_json,
)
from mirai_ct.panorama_runtime import BASELINE_REV, NNUNET_REV
from mirai_ct.volume import Volume, check_geometry, load_volume, read_slice

MAP_NAME = "images/pdac-detection-map/detection_map.mha"


def _json(path: Path) -> Any:
    if path.stat().st_size > 2 * 1024**2:
        raise ValueError("Provenance/score JSON exceeds 2 MiB budget.")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_score(path: Path) -> float:
    """Official pdac-likelihood.json is a number, not an object or percentage."""
    try:
        value = _json(path)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("wrong type")
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("wrong range")
        return float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(
            "Invalid uncalibrated model score: expected one finite JSON number in [0,1]."
        ) from exc


def _validate_run(run: dict) -> None:
    if not isinstance(run, dict) or run.get("schema_version") != 1:
        raise ValueError("Unsupported run provenance schema.")
    if run.get("status") != "success" or run.get("execution_kind") != "pretrained-inference":
        raise ValueError("No completed pretrained inference run in this bundle.")
    if run.get("baseline_revision") != BASELINE_REV or run.get("nnunet_revision") != NNUNET_REV:
        raise ValueError("Model source revisions differ from the reviewed pilot.")
    if run.get("folds") != [0, 1, 2, 3, 4]:
        raise ValueError("Bundle does not record the full five-fold baseline.")


def import_predictions(case: Case, input_export: Path, bundle: Path, output: Path) -> Path:
    """Import a declared completed run; hashes give traceability, not authenticity."""
    if output.exists():
        raise ValueError("Import output directory already exists; choose a new path.")
    scan = load_volume(case.scan_path)
    grid = geometry(scan)
    require_memory(scan.shape)
    info = _json(input_export / "input-provenance.json")
    run = _json(bundle / "run.json")
    _validate_run(run)
    if (
        not isinstance(info, dict)
        or info.get("schema_version") != 1
        or info.get("annotation_used") is not False
    ):
        raise ValueError("Input export provenance is unsupported or not CT-only.")
    if info.get("case_id") != case.case_id:
        raise ValueError("Case ID mismatch in input provenance.")
    source_hash = sha256_file(case.scan_path)
    if source_hash != info.get("source_sha256") or source_hash != run.get("source_sha256"):
        raise ValueError("Source CT checksum mismatch: output belongs to a different input.")
    mha_hash = sha256_file(input_export / "ct.mha")
    if mha_hash != info.get("mha_sha256") or mha_hash != run.get("input_mha_sha256"):
        raise ValueError("Exported input MHA checksum mismatch.")
    expected_hashes = run.get("output_sha256")
    if not isinstance(expected_hashes, dict):
        raise ValueError("Output checksums missing from run provenance.")
    for name in (MAP_NAME, "pdac-likelihood.json", "input-provenance.json"):
        if sha256_file(bundle / name) != expected_hashes.get(name):
            raise ValueError("Bundle output checksum mismatch: " + name)
    if _json(bundle / "input-provenance.json") != info:
        raise ValueError("Bundle input provenance differs from the original export.")
    ct_copy = read_aligned_mha(input_export / "ct.mha", grid)
    validate_alignment(ct_copy, info["geometry"])
    del ct_copy
    detection = read_aligned_mha(bundle / MAP_NAME, grid)
    sitk = simpleitk()
    values = sitk.GetArrayViewFromImage(detection)
    # Validate plane by plane; avoid volume-sized boolean temporary arrays.
    maximum = 0.0
    for plane in values:
        if not np.isfinite(plane).all() or plane.min() < 0 or plane.max() > 1:
            raise ValueError("Candidate detection map must contain finite values in [0,1].")
        maximum = max(maximum, float(plane.max()))
    score = parse_score(bundle / "pdac-likelihood.json")
    if not np.isclose(score, maximum, atol=1e-6, rtol=0):
        raise ValueError("Patient-level score differs from detection-map maximum.")
    parent = output.resolve().parent
    while not parent.exists():
        parent = parent.parent
    if shutil.disk_usage(parent).free < math.prod(scan.shape) * 4 + 16 * 1024**2:
        raise ValueError("Insufficient disk space for imported detection map.")
    header = scan.header.copy()
    header.set_data_dtype(np.float32)
    # SimpleITK array is kji; original NIfTI is ijk. Voxel order is preserved.
    nifti = type(scan)(values.transpose(2, 1, 0), scan.affine, header=header)
    nifti.header.set_slope_inter(1, 0)
    output.mkdir(parents=True)
    destination = output / "detection.nii.gz"
    nib.save(nifti, destination)
    restored = load_volume(destination)
    check_geometry(scan, restored)
    for k in sorted({0, scan.shape[2] // 2, scan.shape[2] - 1}):
        if not np.array_equal(read_slice(restored, 2, k), values[k].T):
            raise ValueError("Imported detection voxels differ after NIfTI restoration.")
    if sha256_file(case.scan_path) != source_hash:
        raise ValueError("Source CT changed during import.")
    shutil.copyfile(bundle / "run.json", output / "run.json")
    shutil.copyfile(bundle / "input-provenance.json", output / "input-provenance.json")
    shutil.copyfile(bundle / "pdac-likelihood.json", output / "pdac-likelihood.json")
    write_json(
        output / "import.json",
        {
            "schema_version": 1,
            "case_id": case.case_id,
            "source_sha256": source_hash,
            "detection_sha256": sha256_file(destination),
            "score": score,
            "run_sha256": sha256_file(output / "run.json"),
            "input_provenance_sha256": sha256_file(output / "input-provenance.json"),
            "imported_utc": datetime.now(UTC).isoformat(),
            "meaning": "PANORAMA candidate detection map; uncalibrated model score",
            "geometry_validation": "same native ijk grid; LPS-to-RAS checked; no resampling",
        },
    )
    return output


def load_predictions(case: Case, directory: Path) -> tuple[Volume, dict]:
    """Load only locally validated imports; reporting needs no SimpleITK."""
    info = _json(directory / "import.json")
    if not isinstance(info, dict) or info.get("schema_version") != 1:
        raise ValueError("Unsupported prediction import schema.")
    if info.get("case_id") != case.case_id or info.get("source_sha256") != sha256_file(
        case.scan_path
    ):
        raise ValueError("Prediction import source CT checksum/case mismatch.")
    for name, key in (
        ("detection.nii.gz", "detection_sha256"),
        ("run.json", "run_sha256"),
        ("input-provenance.json", "input_provenance_sha256"),
    ):
        if sha256_file(directory / name) != info.get(key):
            raise ValueError("Imported prediction checksum mismatch: " + name)
    run = _json(directory / "run.json")
    _validate_run(run)
    if run.get("source_sha256") != info["source_sha256"]:
        raise ValueError("Imported run source checksum differs from the CT.")
    score = info.get("score")
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0 <= score <= 1
    ):
        raise ValueError("Imported model score is invalid.")
    score_path = directory / "pdac-likelihood.json"
    if sha256_file(score_path) != run.get("output_sha256", {}).get("pdac-likelihood.json"):
        raise ValueError("Imported model score checksum mismatch.")
    if score != parse_score(score_path):
        raise ValueError("Imported model score differs from baseline JSON.")
    prediction = load_volume(directory / "detection.nii.gz")
    check_geometry(load_volume(case.scan_path), prediction)
    return prediction, {**info, "run": run, "input": _json(directory / "input-provenance.json")}


def prediction_focus(prediction: Volume) -> list[int]:
    """Find a displayed peak in bounded native planes; no annotation dependence."""
    peak, location = 0.0, [size // 2 for size in prediction.shape]
    for k in range(prediction.shape[2]):
        plane = read_slice(prediction, 2, k)
        if plane.min() < 0 or plane.max() > 1:
            raise ValueError("Candidate detection values outside [0,1].")
        if float(plane.max()) > peak:
            peak = float(plane.max())
            i, j = np.unravel_index(plane.argmax(), plane.shape)
            location = [int(i), int(j), k]
    return location


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a completed PANORAMA candidate-map bundle")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--input-export", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path, help="Extracted Colab output bundle")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = import_predictions(
            select_case(args.manifest, args.case_id), args.input_export, args.bundle, args.output
        )
        print(
            json.dumps(
                {"import": str(output), "kind": "PANORAMA candidate map; uncalibrated score"}
            )
        )
        return 0
    except (OSError, ValueError, MemoryError, RuntimeError, KeyError, TypeError) as exc:
        print(f"Prediction import failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
