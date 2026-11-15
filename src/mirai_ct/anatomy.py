"""Explicit externally supplied pancreatic subregions; no coordinate heuristic."""

import json
from pathlib import Path

import numpy as np

from mirai_ct.panorama_io import sha256_file
from mirai_ct.volume import Volume, check_geometry, iter_slices, load_volume

LABELS = {"1": "head", "2": "body", "3": "tail"}


def measure_subregions(segmentation: Volume, subregions: Volume) -> dict:
    """Measure overlap, retaining uncovered and mixed predictions explicitly."""
    check_geometry(segmentation, subregions)
    counts = {name: 0 for name in LABELS.values()}
    total = 0
    for lesion, parts in zip(iter_slices(segmentation), iter_slices(subregions), strict=True):
        if not np.isin(lesion, [0, 1]).all() or not np.isin(parts, [0, 1, 2, 3]).all():
            raise ValueError("Binary model mask and subregion labels 0/1/2/3 required.")
        positive = lesion == 1
        total += int(np.count_nonzero(positive))
        for label, name in LABELS.items():
            counts[name] += int(np.count_nonzero(positive & (parts == int(label))))
    covered = sum(counts.values())
    names = [name for name, count in counts.items() if count]
    assignment = "unassigned"
    if not total:
        assignment = "no predicted mask"
    elif len(names) > 1:
        assignment = "mixed: " + ", ".join(names)
    elif names:
        assignment = names[0] + (" (partial coverage)" if covered < total else "")
    return {
        "assignment": assignment,
        "model_voxels": total,
        "overlap_voxels": counts,
        "outside_voxels": total - covered,
        "covered_fraction": covered / total if total else None,
        "meaning": "Overlap with externally supplied subregions; not PANORAMA subregion prediction",
    }


def load_anatomy(scan_path: Path, segmentation: Volume, mask: Path, provenance: Path) -> dict:
    if provenance.stat().st_size > 1024**2:
        raise ValueError("Anatomy provenance exceeds 1 MiB.")
    info = json.loads(provenance.read_text(encoding="utf-8"))
    if (
        not isinstance(info, dict)
        or info.get("schema_version") != 1
        or info.get("source_ct_sha256") != sha256_file(scan_path)
        or info.get("mask_sha256") != sha256_file(mask)
        or info.get("labels") != LABELS
        or info.get("source_type") not in ("expert-annotation", "external-model")
        or info.get("review_status") not in ("reviewed", "unreviewed")
        or not isinstance(info.get("method"), str)
        or not info["method"].strip()
        or (
            info.get("review_status") == "reviewed"
            and (
                not isinstance(info.get("reviewer_code"), str) or not info["reviewer_code"].strip()
            )
        )
    ):
        raise ValueError("Anatomy provenance/labels/source hashes are invalid.")
    parts = load_volume(mask)
    check_geometry(load_volume(scan_path), parts)
    return {**measure_subregions(segmentation, parts), "provenance": info}
