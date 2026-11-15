"""Validate signed sensitivity evidence and render it independently of probability."""

import hashlib
import html
import json
import math
from pathlib import Path

import numpy as np

from mirai_ct.occlusion import METHOD, TARGET, validate_blocks, validate_effects
from mirai_ct.volume import Volume, iter_slices, metadata


def load_explanation(path: Path, info: dict, segmentation: Volume, probability: Volume) -> dict:
    if path.stat().st_size > 1024**2:
        raise ValueError("Explanation metadata exceeds 1 MiB.")
    result = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(result, dict)
        or result.get("schema_version") != 1
        or result.get("status") != "success"
    ):
        raise ValueError("No successful occlusion evidence supplied.")
    spec = result.get("spec", {})
    if not isinstance(spec, dict) or spec.get("method") != METHOD or spec.get("target") != TARGET:
        raise ValueError("Unsupported explanation method/target.")
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if result.get("fingerprint") != digest:
        raise ValueError("Explanation identity fingerprint mismatch.")
    original = info["run"]
    identity = spec.get("identity", {})
    if not isinstance(identity, dict):
        raise ValueError("Explanation model identity must be an object.")
    for key, expected in {
        "run_sha256": info["run_sha256"],
        "source_sha256": info["source_sha256"],
        "baseline_revision": original["baseline_revision"],
        "nnunet_revision": original["nnunet_revision"],
        "model_sha256": original.get("model_sha256"),
        "folds": [0, 1, 2, 3, 4],
        "versions": original["versions"],
    }.items():
        if expected is None or identity.get(key) != expected:
            raise ValueError("Explanation source/model identity mismatch: " + key)
    coords = original["crop_coordinates_ijk_exclusive_finish"]
    start = [coords[f"{a}_start"] for a in "xyz"]
    finish = [coords[f"{a}_finish"] for a in "xyz"]
    if identity.get("crop_start_ijk") != start or spec.get("shape_ijk") != [
        b - a for a, b in zip(start, finish, strict=True)
    ]:
        raise ValueError("Explanation crop geometry mismatch.")
    blocks = spec.get("block_bounds_ijk")
    validate_blocks(blocks, spec["shape_ijk"])
    validate_effects(result, blocks, complete=True)
    if type(spec.get("fill_value")) not in (int, float) or not math.isfinite(spec["fill_value"]):
        raise ValueError("Invalid occlusion fill value.")
    hashes = [hashlib.sha256(), hashlib.sha256()]
    target_count = 0
    target_sum = 0.0
    for k, (mask, raw) in enumerate(
        zip(iter_slices(segmentation), iter_slices(probability), strict=True)
    ):
        if start[2] <= k < finish[2]:
            region = np.s_[start[0] : finish[0], start[1] : finish[1]]
            target = np.ascontiguousarray(mask[region].T == 1)
            target_count += int(np.count_nonzero(target))
            raw_region = np.ascontiguousarray(raw[region].T, dtype=np.float32)
            target_sum += float(raw_region[target].sum(dtype=np.float64))
            hashes[0].update(target.tobytes())
            hashes[1].update(raw_region.tobytes())
    if (
        hashes[0].hexdigest() != spec.get("target_sha256")
        or hashes[1].hexdigest() != spec.get("reference_probability_sha256")
        or target_count != identity.get("target_voxel_count")
        or not target_count
    ):
        raise ValueError("Explanation target/probability differs from actual imported products.")
    if abs(result["saved_target_mean"] - target_sum / target_count) > 1e-8:
        raise ValueError("Explanation baseline target differs from original probabilities.")
    native_blocks = []
    for block in result["blocks"]:
        native_blocks.append(
            {
                **block,
                "bounds_ijk": [
                    [v + s for v, s in zip(bound, start, strict=True)]
                    for bound in block["bounds_ijk"]
                ],
            }
        )
    return {
        **result,
        "native_blocks": native_blocks,
        "scope": (
            "Fixed stage-2 lesion target; not the complete "
            "patient-score/crop/postprocessing pipeline"
        ),
        "interpretation": (
            "Positive drop: occlusion reduced target. Negative drop: increased target. "
            "Outside blocks untested. Not causal or clinical validation."
        ),
    }


def sensitivity_plane(evidence: dict, shape: tuple, axis: int, index: int) -> tuple:
    axes = [a for a in range(3) if a != axis]
    values = np.zeros(tuple(shape[a] for a in axes), np.float32)
    support = np.zeros_like(values, dtype=bool)
    for row in evidence["native_blocks"]:
        a, b = row["bounds_ijk"]
        if a[axis] <= index < b[axis]:
            region = tuple(slice(a[d], b[d]) for d in axes)
            values[region], support[region] = row["effect"], True
    return values, support


def plot_explanation(scan: Volume, evidence: dict, axis: int, index: int):
    from mirai_ct.visualization import plot_slice

    fig = plot_slice(scan, axis=axis, index=index)
    ax = fig.axes[0]
    values, support = sensitivity_plane(evidence, scan.shape, axis, index)
    info = metadata(scan)
    directions = [a for a in range(3) if a != axis]
    aspect = info["affine_spacing"][directions[1]] / info["affine_spacing"][directions[0]]
    limit = max(
        max(abs(row["effect"]) for row in evidence["native_blocks"]), evidence["control_floor"] * 5
    )
    resolved = support & (np.abs(values) > evidence["control_floor"])
    overlay = ax.imshow(
        np.ma.masked_where(~resolved.T, values.T),
        origin="lower",
        cmap="coolwarm",
        vmin=-limit,
        vmax=limit,
        alpha=0.65,
        interpolation="nearest",
        aspect=aspect,
    )
    ax.set_title("Signed block occlusion sensitivity (not probability)")
    fig.colorbar(
        overlay, ax=ax, label="Baseline minus occluded fixed-target probability", shrink=0.65
    )
    fig.tight_layout()
    return fig


def evidence_html(anatomy: dict | None, explanation: dict | None) -> str:
    sections = []
    if anatomy:
        provenance = anatomy["provenance"]
        sections.append(
            "<section><h2>Externally supplied pancreatic subregions</h2>"
            f"<p>Model-mask overlap: <strong>{html.escape(anatomy['assignment'])}</strong>. "
            f"Outside labeled subregions: {anatomy['outside_voxels']} model voxels.</p>"
            f"<p>Source: {html.escape(provenance['source_type'])}. "
            f"Method: {html.escape(provenance['method'])}. "
            f"Review status: <strong>{html.escape(provenance['review_status'])}</strong>.</p>"
            "<p>This location uses the separately supplied subregion mask, not a PANORAMA "
            "head/body/tail prediction. "
            "Partial coverage or mixed overlap is retained.</p></section>"
        )
    if explanation:
        rows = "".join(
            f"<tr><td>{row['bounds_ijk']}</td><td>{row['occluded_score']:.6f}</td>"
            f"<td>{row['effect']:+.6f}</td></tr>"
            for row in explanation["native_blocks"]
        )
        sections.append(
            "<section><h2>Signed block occlusion sensitivity (not probability)</h2>"
            "<p>Eight nonoverlapping input blocks were replaced with stored intensity "
            f"{explanation['spec']['fill_value']:g}, then the original five-fold/default-TTA "
            "stage-2 predictor was rerun, with two unchanged-input controls. "
            "The fixed target is the mean class-1 probability "
            "over the original predicted class-1 voxels. "
            f"Baseline target: {explanation['baseline_score']:.6f}; maximum reproduction error: "
            f"{explanation['baseline_max_error']:.6g}.</p>"
            f"<p>Control resolution floor: {explanation['control_floor']:.6g}. "
            "Only effects larger than this floor are colored. Transparent regions may be "
            "untested or below the floor. This is a numerical resolution rule, "
            "not statistical significance.</p>"
            "<p>Positive values mean occlusion reduced the target; negative values mean it "
            "increased the target. Blank regions were not tested. This is coarse input "
            "sensitivity, not Grad-CAM, a probability heatmap or a causal/clinical explanation. "
            "The pancreas crop and output target were fixed: this does not explain the "
            "complete patient-level score or the initial crop selection.</p>"
            "<p>Display uses the same symmetric signed range in all three views, set by "
            "the largest absolute block effect. The colorbar reports the actual probability "
            "difference; color strength alone is not a magnitude or diagnostic confidence.</p>"
            "<table><tr><th>Native bounds (exclusive finish)</th><th>Occluded target</th>"
            f"<th>Baseline minus occluded</th></tr>{rows}</table>"
            + "".join(
                f'<figure><img src="explanation-axis-{axis}.png" '
                'alt="Signed input occlusion sensitivity, not probability"></figure>'
                for axis in range(3)
            )
            + "</section>"
        )
    return "".join(sections)
