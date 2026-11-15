"""Geometry of retained candidate support; no diagnosis or anatomical partition."""

from typing import Any

import numpy as np

from mirai_ct.panorama_io import geometry, require_memory, simpleitk
from mirai_ct.volume import Volume, iter_slices


def segmentation_measurements(segmentation: Volume) -> dict[str, Any]:
    """Measure all positive binary model voxels; no clinical diameter inference."""
    grid = geometry(segmentation)
    count = 0
    sums = np.zeros(3, dtype=np.float64)
    minimum = np.asarray(segmentation.shape, dtype=np.int64)
    maximum = np.full(3, -1, dtype=np.int64)
    for k, plane in enumerate(iter_slices(segmentation)):
        if not np.isfinite(plane).all() or not ((plane == 0) | (plane == 1)).all():
            raise ValueError("Model measurements require a finite binary segmentation.")
        i, j = np.nonzero(plane)
        if not len(i):
            continue
        count += len(i)
        sums += [int(i.sum()), int(j.sum()), len(i) * k]
        minimum = np.minimum(minimum, [int(i.min()), int(j.min()), k])
        maximum = np.maximum(maximum, [int(i.max()), int(j.max()), k])
    ras = np.asarray(grid["affine_ras_mm"])
    centroid = (ras @ np.r_[sums / count, 1])[:3].tolist() if count else None
    return {
        "definition": "All positive stage-2 class-1 model voxels, including disconnected parts",
        "voxel_count": count,
        "volume_ml": count * abs(float(np.linalg.det(ras[:3, :3]))) / 1000,
        "bounds_ijk_inclusive": [minimum.tolist(), maximum.tolist()] if count else None,
        "extent_mm_native_axes": (
            ((maximum - minimum + 1) * np.asarray(grid["spacing_mm"])).tolist() if count else None
        ),
        "centroid_ras_mm": centroid,
        "anatomical_subregion": "unassigned",
        "interpretation": "Unvalidated model-mask measurements; box extent is not tumor diameter",
        "outside_crop": "Zero padding means not evaluated; no disease absence is established",
    }


def findings_summary(
    prediction_info: dict | None,
    regions: list[dict] | None,
    model_measurements: dict | None,
    *,
    anatomy: dict | None = None,
    explanation: dict | None = None,
) -> dict[str, Any]:
    """Deterministic research wording grounded only in available imported products."""
    sentences = []
    if prediction_info is None:
        sentences.append(
            "No PANORAMA prediction was supplied. This report shows CT/reference data only."
        )
    else:
        sentences.append(f"PANORAMA uncalibrated scan score: {prediction_info['score']:.6g}.")
        if regions is not None:
            sentences.append(f"Measured retained candidate support regions: {len(regions)}.")
        else:
            sentences.append("Candidate-region measurements were not requested.")
        if model_measurements is None:
            sentences.append("Model segmentation is unavailable in this imported result.")
        else:
            sentences.append(
                f"Predicted mask volume: {model_measurements['volume_ml']:.4f} mL "
                f"({model_measurements['voxel_count']:,} voxels); unvalidated model measurement."
            )
    sentences.append("No validated screening cutoff or clinical diagnosis is established.")
    if anatomy is None and explanation is None:
        sentences.append("Head/body/tail and decision attribution remain unavailable.")
    else:
        sentences.append(
            "External subregion-mask overlap: " + anatomy["assignment"] + "."
            if anatomy
            else "Head/body/tail remains unassigned."
        )
        sentences.append(
            "Signed input-occlusion sensitivity is available for a fixed stage-2 lesion target."
            if explanation
            else "Decision attribution remains unavailable."
        )
    return {
        "sentences": sentences,
        "candidate_region_count": len(regions) if regions is not None else None,
        "model_segmentation_measured": model_measurements is not None,
        "clinical_diagnosis": "not established",
        "anatomical_subregion": anatomy["assignment"] if anatomy else "unassigned",
    }


def candidate_regions(prediction: Volume) -> list[dict[str, Any]]:
    """Describe 26-connected nonzero support, not authoritative tumor boundaries."""
    require_memory(prediction.shape)
    grid = geometry(prediction)
    support = np.empty(prediction.shape[::-1], dtype=np.uint8)
    for k, plane in enumerate(iter_slices(prediction)):
        if plane.min() < 0 or plane.max() > 1:
            raise ValueError("Candidate values must be in [0,1].")
        support[k] = (plane > 0).T
    sitk = simpleitk()
    image = sitk.GetImageFromArray(support)
    image.SetSpacing(grid["spacing_mm"])
    image.SetOrigin(grid["origin_lps_mm"])
    image.SetDirection(grid["direction_lps_row_major"])
    del support
    components = sitk.ConnectedComponentImageFilter()
    components.SetFullyConnected(True)
    components.SetNumberOfWorkUnits(1)
    labeled = components.Execute(image)
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.SetNumberOfWorkUnits(1)
    stats.Execute(labeled)
    ids = sitk.GetArrayViewFromImage(labeled)
    peaks = {int(label): 0.0 for label in stats.GetLabels()}
    for k, plane in enumerate(iter_slices(prediction)):
        values = plane.T
        for label in np.unique(ids[k][ids[k] > 0]):
            peaks[int(label)] = max(peaks[int(label)], float(values[ids[k] == label].max()))
    findings = []
    for label in stats.GetLabels():
        box = stats.GetBoundingBox(label)
        lo, size = list(box[:3]), list(box[3:])
        hi = [a + b - 1 for a, b in zip(lo, size, strict=True)]
        lps = list(stats.GetCentroid(label))
        findings.append(
            {
                "region_id": int(label),
                "definition": "26-connected positive candidate support; not validated tumor extent",
                "score_max": peaks[int(label)],
                "voxel_count": int(stats.GetNumberOfPixels(label)),
                "bounds_ijk_inclusive": [lo, hi],
                "centroid_lps_mm": lps,
                "centroid_ras_mm": [-lps[0], -lps[1], lps[2]],
                "extent_mm_native_axes": [
                    a * b for a, b in zip(size, grid["spacing_mm"], strict=True)
                ],
                "support_volume_ml": float(stats.GetPhysicalSize(label) / 1000),
                "anatomical_subregion": "unassigned",
            }
        )
    return findings
