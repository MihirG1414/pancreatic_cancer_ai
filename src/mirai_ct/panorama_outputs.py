"""Optional model products with explicit native-grid and crop semantics."""

import math
import shutil
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np

from mirai_ct.panorama_io import (
    read_aligned_mha,
    require_memory,
    sha256_file,
    simpleitk,
    sitk_affine_lps,
)
from mirai_ct.volume import Volume, check_geometry, load_volume, read_slice

MODEL_FILES = {
    "segmentation": "images/pdac-segmentation/segmentation.mha",
    "probability": "images/pdac-probability-map/probability.mha",
}
MODEL_SEMANTICS = {
    "segmentation": "stage-2 predicted class 1; unvalidated model segmentation",
    "probability": "raw stage-2 class-1 probability; uncalibrated, not attribution",
    "outside_crop": "zero padding means outside the evaluated crop, not absence of disease",
}


def export_model_outputs(
    reference: Any, coordinates: dict, labels: Any, probability: np.ndarray, output: Path
) -> dict[str, str]:
    """Paste original crop values into native indices without resampling."""
    from mirai_ct.panorama_runtime import validate_crop

    sitk = simpleitk()
    start = [coordinates[f"{axis}_start"] for axis in "xyz"]
    validate_crop(coordinates, reference.GetSize(), labels.GetSize())
    expected = sitk_affine_lps(reference)
    expected[:3, 3] = reference.TransformIndexToPhysicalPoint(start)
    if not np.allclose(sitk_affine_lps(labels), expected, atol=1e-4, rtol=0):
        raise ValueError("Model crop physical grid mismatch.")
    values = sitk.GetArrayViewFromImage(labels)
    if (
        probability.shape != values.shape
        or probability.ndim != 3
        or not np.isfinite(probability).all()
        or probability.min() < 0
        or probability.max() > 1
    ):
        raise ValueError("Raw model probability shape/range is invalid.")
    if (
        not np.isfinite(values).all()
        or values.min() < 0
        or values.max() > 6
        or not np.equal(values, np.floor(values)).all()
    ):
        raise ValueError("Stage-2 segmentation labels must be integers in [0,6].")
    require_memory(tuple(reference.GetSize()))
    if any((output / name).exists() for name in MODEL_FILES.values()):
        raise ValueError("Model output exists; choose a fresh bundle.")
    parent = output.resolve()
    while not parent.exists():
        parent = parent.parent
    if shutil.disk_usage(parent).free < math.prod(reference.GetSize()) * 5 + 16 * 1024**2:
        raise ValueError("Insufficient disk space for native model products.")
    hashes = {}
    for name, array in (
        ("segmentation", (values == 1).astype(np.uint8)),
        ("probability", probability.astype(np.float32)),
    ):
        cropped = sitk.GetImageFromArray(array)
        full = sitk.Image(reference.GetSize(), cropped.GetPixelID())
        full.CopyInformation(reference)
        full = sitk.Paste(full, cropped, cropped.GetSize(), destinationIndex=start)
        path = output / MODEL_FILES[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        sitk.WriteImage(full, str(path))
        restored = sitk.ReadImage(str(path))
        if not np.allclose(
            sitk_affine_lps(restored), sitk_affine_lps(reference), atol=1e-4
        ) or not np.array_equal(
            sitk.GetArrayViewFromImage(full), sitk.GetArrayViewFromImage(restored)
        ):
            raise ValueError("Saved native model output differs from its source crop.")
        hashes[MODEL_FILES[name]] = sha256_file(path)
    return hashes


def import_model_outputs(scan: Volume, grid: dict, bundle: Path, output: Path, run: dict) -> dict:
    """Old bundles have no extras; declared extras require a complete checked pair."""
    declared = run.get("model_outputs")
    recorded = run.get("output_sha256", {})
    present = [
        name for name in MODEL_FILES.values() if (bundle / name).exists() or name in recorded
    ]
    if declared is None:
        if present:
            raise ValueError("Model outputs present without their declared semantics.")
        return {}
    if declared != MODEL_SEMANTICS or len(present) != 2:
        raise ValueError("Incomplete or unsupported model outputs declaration.")
    hashes = {}
    for kind, name in MODEL_FILES.items():
        if sha256_file(bundle / name) != recorded.get(name):
            raise ValueError("Model output checksum mismatch: " + name)
        image = read_aligned_mha(bundle / name, grid)
        values = simpleitk().GetArrayViewFromImage(image)
        for plane in values:
            if not np.isfinite(plane).all() or plane.min() < 0 or plane.max() > 1:
                raise ValueError("Model output contains invalid values.")
            if kind == "segmentation" and not np.equal(plane, np.floor(plane)).all():
                raise ValueError("Model segmentation must be binary.")
        header = scan.header.copy()
        header.set_data_dtype(np.float32)
        restored = type(scan)(values.transpose(2, 1, 0), scan.affine, header=header)
        restored.header.set_slope_inter(1, 0)
        path = output / f"{kind}.nii.gz"
        nib.save(restored, path)
        native = load_volume(path)
        check_geometry(scan, native)
        for k in range(scan.shape[2]):
            if not np.array_equal(read_slice(native, 2, k), values[k].T):
                raise ValueError("Native model-output voxels changed during import.")
        hashes[path.name] = sha256_file(path)
    return hashes


def load_model_outputs(scan: Volume, directory: Path, info: dict) -> dict[str, Volume]:
    """Validate derived products every time they are displayed."""
    hashes = info.get("model_output_sha256", {})
    run = info["run"]
    if run.get("model_outputs") is None and not hashes:
        return {}
    if run.get("model_outputs") != MODEL_SEMANTICS or set(hashes) != {
        "segmentation.nii.gz",
        "probability.nii.gz",
    }:
        raise ValueError("Missing imported model-output pair.")
    result = {}
    for kind in MODEL_FILES:
        path = directory / f"{kind}.nii.gz"
        if sha256_file(path) != hashes.get(path.name):
            raise ValueError("Imported model output checksum mismatch.")
        image = load_volume(path)
        check_geometry(scan, image)
        result[kind] = image
    return result
