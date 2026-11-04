"""Geometry of retained candidate support; no diagnosis or anatomical partition."""

from typing import Any

import numpy as np

from mirai_ct.panorama_io import geometry, require_memory, simpleitk
from mirai_ct.volume import Volume, read_slice


def candidate_regions(prediction: Volume) -> list[dict[str, Any]]:
    """Describe 26-connected nonzero support, not authoritative tumor boundaries."""
    require_memory(prediction.shape)
    grid = geometry(prediction)
    support = np.empty(prediction.shape[::-1], dtype=np.uint8)
    for k in range(prediction.shape[2]):
        plane = read_slice(prediction, 2, k)
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
    for k in range(prediction.shape[2]):
        values = read_slice(prediction, 2, k).T
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
