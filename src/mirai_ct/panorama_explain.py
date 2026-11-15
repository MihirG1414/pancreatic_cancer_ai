"""GPU-only continuation: explain a completed run without changing its predictions."""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

from mirai_ct.occlusion import calculate_effects, partition_bounds
from mirai_ct.panorama_io import read_aligned_mha, sha256_file, simpleitk
from mirai_ct.panorama_runtime import (
    BASELINE_REV,
    NNUNET_REV,
    STAGES,
    _versions,
    configure_inference_environment,
    preflight,
    require_crop_memory,
    validate_baseline_source,
    validate_crop,
    validate_models,
    validate_stage_grid,
)


def _explain_run(root: Path, baseline: Path, run_dir: Path, input_dir: Path, output: Path) -> Path:
    """Reuse saved crop/checkpoints; all five folds, default TTA and fixed target."""
    if sys.platform != "linux":
        raise ValueError("Run this continuation in the existing Colab NVIDIA environment.")
    configure_inference_environment()
    preflight(root)
    versions = _versions()
    validate_baseline_source(baseline)
    bundle = run_dir / "bundle"
    run_path = bundle / "run.json"
    record = json.loads(run_path.read_text())
    if (
        record.get("status") != "success"
        or record.get("execution_kind") != "pretrained-inference"
        or record.get("baseline_revision") != BASELINE_REV
        or record.get("nnunet_revision") != NNUNET_REV
        or record.get("folds") != [0, 1, 2, 3, 4]
        or record.get("model_outputs") is None
        or record.get("weights", {}).get("permission_confirmed_by_operator") is not True
    ):
        raise ValueError("A successful source-pinned run with genuine model products is required.")
    models = validate_models(root / "models")
    if models != record.get("model_sha256") or versions != record.get("versions"):
        raise ValueError("Model weights or numerical environment differ from original inference.")
    from mirai_ct.panorama import MAP_NAME
    from mirai_ct.panorama_outputs import MODEL_FILES

    names = [
        MAP_NAME,
        *MODEL_FILES.values(),
        "pdac-likelihood.json",
        "input-provenance.json",
        "WEIGHTS-LICENSE.txt",
    ]
    for name in names:
        if sha256_file(bundle / name) != record["output_sha256"].get(name):
            raise ValueError("Original bundle checksum mismatch: " + name)
    sitk = simpleitk()
    crop_path = run_dir / "input_fullres/scan_0000.nii.gz"
    labels_path = run_dir / "output_fullres/scan.nii.gz"
    probability_path = run_dir / "output_fullres/scan.npz"
    provenance = json.loads((bundle / "input-provenance.json").read_text())
    if provenance != json.loads((input_dir / "input-provenance.json").read_text()) or sha256_file(
        input_dir / "ct.mha"
    ) != record.get("input_mha_sha256"):
        raise ValueError("Original CT export differs from completed run.")
    size = provenance["geometry"]["shape_ijk"]
    coordinates = record["crop_coordinates_ijk_exclusive_finish"]
    start = [coordinates[f"{axis}_start"] for axis in "xyz"]
    finish = [coordinates[f"{axis}_finish"] for axis in "xyz"]
    expected_shape = [b - a for a, b in zip(start, finish, strict=True)]
    validate_crop(coordinates, size, expected_shape)
    require_crop_memory(tuple(size), tuple(expected_shape))
    crop = sitk.ReadImage(str(crop_path))
    labels = sitk.ReadImage(str(labels_path))
    validate_stage_grid(labels, crop.GetSize(), crop)
    # Verify crop placement against the original declared native grid.
    grid = provenance["geometry"]
    direction = np.asarray(grid["direction_lps_row_major"]).reshape(3, 3)
    origin = np.asarray(grid["origin_lps_mm"]) + direction @ (
        np.asarray(start) * grid["spacing_mm"]
    )
    if list(crop.GetSize()) != expected_shape or not np.allclose(
        crop.GetOrigin(), origin, atol=1e-4, rtol=0
    ):
        raise ValueError("Saved crop geometry differs from original CT/crop coordinates.")
    if not np.allclose(crop.GetSpacing(), grid["spacing_mm"], atol=1e-4, rtol=0) or not np.allclose(
        crop.GetDirection(), grid["direction_lps_row_major"], atol=1e-4, rtol=0
    ):
        raise ValueError("Saved crop spacing/direction differs.")
    values = sitk.GetArrayViewFromImage(labels)
    if not np.isin(values, range(7)).all():
        raise ValueError("Saved multiclass segmentation has unexpected labels.")
    target = values == 1
    if not target.any():
        raise ValueError("No predicted class-1 target; no lesion explanation can be generated.")
    data = sitk.GetArrayFromImage(crop).astype(np.float32)
    source = read_aligned_mha(input_dir / "ct.mha", grid)
    source_crop = sitk.RegionOfInterest(source, expected_shape, start)
    if not np.array_equal(sitk.GetArrayViewFromImage(source_crop), data):
        raise ValueError("Saved crop values differ from original CT.")
    del source_crop, source
    with np.load(probability_path, allow_pickle=False) as saved:
        probabilities = np.asarray(saved["probabilities"], dtype=np.float32)
        if probabilities.shape != (7, *data.shape):
            raise ValueError("Expected seven native-crop probability channels.")
        reference = probabilities[1].copy()
        del probabilities
    for kind, expected in [("segmentation", target), ("probability", reference)]:
        source = read_aligned_mha(bundle / MODEL_FILES[kind], grid)
        cropped = sitk.RegionOfInterest(source, expected_shape, start)
        if not np.array_equal(sitk.GetArrayViewFromImage(cropped), expected):
            raise ValueError("Saved crop output differs from bundled native model product.")
        del cropped, source
    locations = np.argwhere(target)
    margin_kji = np.ceil(10 / np.asarray(crop.GetSpacing()[::-1])).astype(int)
    lo = np.maximum(0, locations.min(axis=0) - margin_kji)
    hi = np.minimum(data.shape, locations.max(axis=0) + 1 + margin_kji)
    blocks = partition_bounds([int(v) for v in lo[::-1]], [int(v) for v in hi[::-1]])
    identity = {
        "run_sha256": sha256_file(run_path),
        "source_sha256": record["source_sha256"],
        "baseline_revision": BASELINE_REV,
        "nnunet_revision": NNUNET_REV,
        "model_sha256": models,
        "folds": [0, 1, 2, 3, 4],
        "versions": versions,
        "crop_start_ijk": start,
        "target_voxel_count": int(target.sum()),
        "saved_crop_sha256": sha256_file(crop_path),
        "saved_labels_sha256": sha256_file(labels_path),
        "saved_probabilities_sha256": sha256_file(probability_path),
        "runner_sha256": sha256_file(Path(__file__)),
    }
    os.environ.update(
        nnUNet_results=str(root / "models"),
        nnUNet_raw=str(root / "raw"),
        nnUNet_preprocessed=str(root / "preprocessed"),
        nnUNet_compile="false",
    )
    import torch
    from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

    if not torch.cuda.is_available():
        raise ValueError("CUDA is unavailable in this environment.")
    predictor = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,
        device=torch.device("cuda"),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=False,
    )
    stage = STAGES[1]
    model_dir = root / "models" / stage["dataset"] / f"{stage['trainer']}__nnUNetPlans__3d_fullres"
    predictor.initialize_from_trained_model_folder(
        str(model_dir), use_folds=(0, 1, 2, 3, 4), checkpoint_name=stage["checkpoint"]
    )

    def predict(array):
        _, probability = predictor.predict_single_npy_array(
            array[np.newaxis],
            {"spacing": tuple(crop.GetSpacing()[::-1])},
            save_or_return_probabilities=True,
        )
        return np.asarray(probability[1], dtype=np.float32)

    journal = output / "explanation.json"
    calculate_effects(
        data,
        target,
        reference,
        blocks,
        predict,
        journal=journal,
        fill_value=50.0,
        identity=identity,
    )
    return journal


def explain_run(root: Path, baseline: Path, run_dir: Path, input_dir: Path, output: Path) -> Path:
    if sys.platform != "linux":
        raise ValueError("Run this continuation in the existing Colab NVIDIA environment.")
    import fcntl

    output.mkdir(parents=True, exist_ok=True)
    # Kernel-released lock survives browser reconnects without a stale-PID bypass.
    with (output / "active.lock").open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(
                "This explanation is already running; keep its process intact."
            ) from exc
        return _explain_run(root, baseline, run_dir, input_dir, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "baseline", "run-dir", "input", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        print(
            explain_run(
                args.root.resolve(),
                args.baseline.resolve(),
                args.run_dir.resolve(),
                args.input.resolve(),
                args.output.resolve(),
            )
        )
    except (OSError, ValueError, RuntimeError, MemoryError) as exc:
        print(f"Explanation stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
