"""Offline native-slice assets and candidate display selection; never inference."""

# HTML copy remains on complete lines for review alongside the generated report.
# ruff: noqa: E501

import html
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from mirai_ct.panorama_io import available_bytes
from mirai_ct.volume import Volume, check_geometry, metadata, read_slice


def candidate_summary(prediction: Volume) -> dict[str, Any]:
    """Inspect positive candidate support, independent of annotations."""
    counts, maxima = [], []
    total, largest = 0, 0
    focus = [size // 2 for size in prediction.shape]
    lower, upper = np.array(prediction.shape), np.full(3, -1)
    for k in range(prediction.shape[2]):
        plane = read_slice(prediction, 2, k)
        if not np.isfinite(plane).all() or plane.min() < 0 or plane.max() > 1:
            raise ValueError("Candidate values must be finite and in [0,1].")
        support = plane > 0
        count = int(np.count_nonzero(support))
        counts.append(count)
        maxima.append(float(plane.max()))
        total += count
        if count:
            ij = np.argwhere(support)
            lo, hi = ij.min(axis=0), ij.max(axis=0)
            lower = np.minimum(lower, [*lo, k])
            upper = np.maximum(upper, [*hi, k])
            if count > largest:
                largest = count
                focus = [int((lo[0] + hi[0]) // 2), int((lo[1] + hi[1]) // 2), k]
    return {
        "focus_ijk": focus,
        "selection": "largest positive candidate cross-section in native k; earliest tie",
        "positive_voxels": total,
        "bounds_ijk": [lower.tolist(), upper.tolist()] if total else None,
        "slice_counts": counts,
        "slice_maxima": maxima,
    }


def candidate_outline(support: np.ndarray) -> np.ndarray:
    """Four-neighbor boundary of positive support, not a tumor segmentation."""
    padded = np.pad(support, 1, constant_values=False)
    interior = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:]
    return support & ~interior


def export_viewer(
    scan: Volume, prediction: Volume, mask: Volume | None, output: Path
) -> dict[str, Any]:
    """Stream 2D display copies; original volumes remain uncached and unchanged."""
    if output.exists():
        raise ValueError("Viewer output exists; choose a fresh directory.")
    check_geometry(scan, prediction)
    if mask is not None:
        check_geometry(scan, mask)
    pixels = scan.shape[0] * scan.shape[1]
    if scan.shape[2] > 512 or pixels > 2048**2:
        raise ValueError("Offline viewer budget: at most 512 slices of 2048 x 2048 pixels.")
    if available_bytes() < pixels * 64 + 64 * 1024**2:
        raise MemoryError("Insufficient available RAM for bounded viewer slice export.")
    parent = output.resolve().parent
    while not parent.exists():
        parent = parent.parent
    if shutil.disk_usage(parent).free < math.prod(scan.shape) * 16 + 16 * 1024**2:
        raise ValueError("Insufficient disk space for conservative offline viewer asset budget.")
    info = metadata(scan)
    unit_mm = {"mm": 1.0, "meter": 1000.0, "micron": 0.001}[info["spatial_units"]]
    result = {
        **candidate_summary(prediction),
        "shape_ijk": list(scan.shape),
        "spacing": info["affine_spacing"],
        "units": info["spatial_units"],
        "directions": info["orientation"],
        "display_level": 50,
        "display_window": 400,
        "zoom_padding_ij": [math.ceil(15 / (x * unit_mm)) for x in info["affine_spacing"][:2]],
        "annotation_labels": [],
        "slices": [],
    }
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import colormaps
    from matplotlib.image import imsave

    output.mkdir(parents=True)
    assets = output / "slices"
    assets.mkdir()
    label_ids: set[int] = set()
    for k in range(scan.shape[2]):
        # PNG y increases downwards; flip native j so it increases upwards.
        ct = read_slice(scan, 2, k).T[::-1]
        values = read_slice(prediction, 2, k).T[::-1]
        gray = np.clip((ct.astype(np.float32) + 150) / 400 * 255, 0, 255).astype(np.uint8)
        support = values > 0
        rgba = colormaps["magma"](values, bytes=True)
        rgba[..., 3] = np.where(support, 255, 0)
        edge = rgba.copy()
        edge[..., 3] = np.where(candidate_outline(support), 255, 0)
        entry = {
            "k": k,
            "ct": f"slices/{k}-ct.png",
            "candidate": f"slices/{k}-candidate.png",
            "outline": f"slices/{k}-outline.png",
            "annotation": None,
        }
        imsave(output / entry["ct"], gray, cmap="gray", vmin=0, vmax=255)
        imsave(output / entry["candidate"], rgba)
        imsave(output / entry["outline"], edge)
        if mask is not None:
            labels = read_slice(mask, 2, k).T[::-1]
            if (
                not np.isfinite(labels).all()
                or (labels < 0).any()
                or (labels > 65535).any()
                or not np.equal(labels, np.floor(labels)).all()
            ):
                raise ValueError("Annotation labels must be finite nonnegative integers <=65535.")
            annotation = np.zeros((*gray.shape, 4), np.uint8)
            for label in np.unique(labels[labels > 0]).astype(int):
                label_ids.add(int(label))
                color = colormaps["tab10"]((int(label) - 1) % 10, bytes=True)
                annotation[labels == label] = color
            entry["annotation"] = f"slices/{k}-annotation.png"
            imsave(output / entry["annotation"], annotation)
        result["slices"].append(entry)
    result["annotation_labels"] = [
        {"id": label, "rgb": list(colormaps["tab10"]((label - 1) % 10, bytes=True)[:3])}
        for label in sorted(label_ids)
    ]
    # Matplotlib's bytes may be NumPy scalars; persist native JSON numbers only.
    for item in result["annotation_labels"]:
        item["rgb"] = [int(value) for value in item["rgb"]]
    (output / "display.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    shutil.copyfile(Path(__file__).parent / "assets/viewer.js", output / "viewer.js")
    return result


def viewer_html(info: dict[str, Any], case_id: str) -> str:
    """Inline metadata avoids file:// fetch restrictions and network services."""
    payload = json.dumps(info, allow_nan=False).replace("<", "\\u003c")
    return f"""<section id="slice-viewer" aria-label="Interactive native CT slices">
<h2>Explore native CT slices</h2>
<p>Case {html.escape(case_id)}. Use the slider to inspect every native k plane.
CT, existing annotation and PANORAMA candidates share the same slice and zoom.
Zoom changes display only. Candidate outlines mark retained map support, not validated tumor boundaries.</p>
<div class="viewer-controls">
<button id="previous-slice" type="button">Previous</button>
<label>Slice k <input id="slice-index" type="range" min="0" max="{len(info["slices"]) - 1}" value="{info["focus_ijk"][2]}"></label>
<button id="next-slice" type="button">Next</button>
<button id="candidate-focus" type="button">Largest candidate slice</button>
<label><input id="candidate-zoom" type="checkbox"> Candidate zoom</label>
<label>Candidate display <select id="candidate-style"><option value="candidate">Fill</option><option value="outline">Outline</option><option value="off">Off</option></select></label>
<label>Overlay opacity <input id="overlay-opacity" type="range" min="0" max="100" value="65"></label>
</div>
<p id="slice-status" role="status" aria-live="polite">Loading native slice...</p>
<p id="viewer-directions"></p><div class="viewer-panels">
<figure><figcaption>Original CT</figcaption><canvas id="ct-canvas" aria-label="CT native slice"></canvas></figure>
<figure><figcaption>Existing dataset annotation</figcaption><canvas id="annotation-canvas" aria-label="Existing annotation native slice"></canvas></figure>
<figure><figcaption>PANORAMA candidate map</figcaption><canvas id="candidate-canvas" aria-label="PANORAMA candidate native slice"></canvas></figure>
</div><p id="annotation-legend"></p>
<p>Candidate colors: <span style="display:inline-block;width:100px;height:12px;background:linear-gradient(to right,#000004,#b73779,#fcfdbf)"></span>
0 to 1, uncalibrated score. Zero candidate values are transparent.</p>
<p>Fixed display level 50 / window 400 in stored scaled intensities; HU calibration unverified.
Native voxel axes; not standardized radiological orientation.</p>
<noscript>Enable JavaScript for slice navigation. The static views below remain available.</noscript>
<script id="viewer-data" type="application/json">{payload}</script>
<script src="viewer/viewer.js" defer></script></section>"""
