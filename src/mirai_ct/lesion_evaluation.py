"""Explicit connected-component lesion matching and exploratory FROC."""

# Keep complete HTML copy readable alongside generated report.
# ruff: noqa: E501

import argparse
import html
import json
import math
import sys
from pathlib import Path

import numpy as np
import psutil

from mirai_ct.cases import read_cases
from mirai_ct.panorama import load_predictions
from mirai_ct.panorama_io import sha256_file, simpleitk, write_json
from mirai_ct.volume import check_geometry, iter_slices, load_volume


def _matched(candidates: list[dict], reference_count: int) -> int:
    """Maximum-cardinality bipartite matching; no greedy duplicate assignment."""
    owners: dict[int, int] = {}

    def augment(index: int, visited: set[int]) -> bool:
        for ref in candidates[index]["matches"]:
            if ref in visited:
                continue
            visited.add(ref)
            if ref not in owners or augment(owners[ref], visited):
                owners[ref] = index
                return True
        return False

    for i in range(len(candidates)):
        augment(i, set())
        if len(owners) == reference_count:
            break
    return len(owners)


def froc_curve(records: list[dict]) -> list[dict]:
    """Admit score ties together; None threshold means all candidates excluded."""
    if not isinstance(records, list) or not 1 <= len(records) <= 500:
        raise ValueError("Provide 1..500 explicit scan records.")
    scores = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each scan record must be an object.")
        nr, candidates = record.get("reference_count"), record.get("candidates")
        if (
            type(nr) is not int
            or not 0 <= nr <= 500
            or not isinstance(candidates, list)
            or len(candidates) > 500
        ):
            raise ValueError("Bounded lesion counts and candidates required.")
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise ValueError("Each candidate must be an object.")
            score, matches = candidate.get("score"), candidate.get("matches")
            if (
                type(score) not in (int, float)
                or not math.isfinite(score)
                or not 0 <= score <= 1
                or not isinstance(matches, list)
                or len(matches) != len(set(matches))
                or any(type(i) is not int or not 0 <= i < nr for i in matches)
            ):
                raise ValueError("Invalid candidate score or reference match index.")
            scores.add(score)
    total = sum(r["reference_count"] for r in records)
    result = []
    for threshold in [None, *sorted(scores, reverse=True)]:
        detected = n_pred = 0
        for record in records:
            selected = (
                []
                if threshold is None
                else [c for c in record["candidates"] if c["score"] >= threshold]
            )
            detected += _matched(selected, record["reference_count"])
            n_pred += len(selected)
        result.append(
            {
                "threshold": threshold,
                "matched_lesions": detected,
                "reference_lesions": total,
                "false_positives": n_pred - detected,
                "false_positives_per_scan": (n_pred - detected) / len(records),
                "sensitivity": detected / total if total else None,
            }
        )
    return result


def component_matches(reference: Path, prediction: Path, *, label: int, min_iou: float) -> dict:
    """Original native voxels; explicit 26-connectivity and IoU matching policy."""
    if type(label) is not int or not 1 <= label <= 65535:
        raise ValueError("Explicit positive reference label required.")
    if type(min_iou) not in (int, float) or not math.isfinite(min_iou) or not 0 < min_iou <= 1:
        raise ValueError("Minimum IoU must be finite and in (0,1].")
    ref, pred = load_volume(reference), load_volume(prediction)
    check_geometry(ref, pred)
    sitk = simpleitk()
    available = psutil.virtual_memory().available
    sparse_budget = min(128 * 1024**2, available // 8)
    sparse, sparse_bytes = [], 0
    lower, upper = np.array(ref.shape), np.full(3, -1)
    for k, (rp, pp) in enumerate(zip(iter_slices(ref), iter_slices(pred), strict=True)):
        if (rp < 0).any() or (rp > 65535).any() or not np.equal(rp, np.floor(rp)).all():
            raise ValueError("Integer reference labels <=65535 required.")
        if (pp < 0).any() or (pp > 1).any():
            raise ValueError("Candidate scores must be in [0,1].")
        ri, pi = np.argwhere(rp == label).astype(np.int32), np.argwhere(pp > 0).astype(np.int32)
        scores = pp[pi[:, 0], pi[:, 1]]
        sparse_bytes += ri.nbytes + pi.nbytes + scores.nbytes
        if sparse_bytes > sparse_budget:
            raise MemoryError(
                "Positive-voxel component budget exceeded; use more RAM/review noisy maps."
            )
        for coordinates in (ri, pi):
            if len(coordinates):
                lower = np.minimum(lower, [*coordinates.min(axis=0), k])
                upper = np.maximum(upper, [*coordinates.max(axis=0), k])
        if len(ri) or len(pi):
            sparse.append((k, ri, pi, scores))
    base = {"reference_sha256": sha256_file(reference), "candidate_sha256": sha256_file(prediction)}
    if not sparse:
        return {**base, "reference_count": 0, "reference_component_voxels": [], "candidates": []}
    shape = upper - lower + 1
    if int(np.prod(shape)) * 20 + sparse_bytes > min(512 * 1024**2, available // 2):
        raise MemoryError("Component bounding box exceeds one-case RAM budget.")
    reference_values = np.zeros(tuple(shape[::-1]), np.uint8)
    prediction_values = np.zeros(tuple(shape[::-1]), np.float32)
    for k, ri, pi, scores in sparse:
        reference_values[k - lower[2], ri[:, 1] - lower[1], ri[:, 0] - lower[0]] = 1
        prediction_values[k - lower[2], pi[:, 1] - lower[1], pi[:, 0] - lower[0]] = scores
    del sparse

    def components(binary):
        source = sitk.GetImageFromArray(binary.astype(np.uint8))
        operation = sitk.ConnectedComponentImageFilter()
        operation.SetFullyConnected(True)
        operation.SetNumberOfWorkUnits(1)
        labels = operation.Execute(source)
        stats = sitk.LabelShapeStatisticsImageFilter()
        stats.SetNumberOfWorkUnits(1)
        stats.Execute(labels)
        if stats.GetNumberOfLabels() > 500:
            raise ValueError("More than 500 lesions/candidates; review noisy input.")
        counts = {int(i): int(stats.GetNumberOfPixels(i)) for i in stats.GetLabels()}
        return labels, counts

    ref_cc, ref_counts = components(reference_values)
    pred_cc, pred_counts = components(prediction_values > 0)
    r, p = sitk.GetArrayViewFromImage(ref_cc), sitk.GetArrayViewFromImage(pred_cc)
    peaks = {i: 0.0 for i in pred_counts}
    intersections: dict[tuple[int, int], int] = {}
    for rp, pp, sp in zip(r, p, prediction_values, strict=True):
        for index in np.unique(pp[pp > 0]):
            peaks[int(index)] = max(peaks[int(index)], float(sp[pp == index].max()))
        shared = (rp > 0) & (pp > 0)
        pairs, counts = np.unique(
            np.stack([rp[shared], pp[shared]], axis=1), axis=0, return_counts=True
        )
        for pair, count in zip(pairs, counts, strict=True):
            key = tuple(int(v) for v in pair)
            intersections[key] = intersections.get(key, 0) + int(count)
    candidates = []
    reference_ids = sorted(ref_counts)
    for index in sorted(pred_counts):
        overlaps = []
        for reference_id in reference_ids:
            intersection = intersections.get((reference_id, index), 0)
            union = ref_counts[reference_id] + pred_counts[index] - intersection
            overlaps.append(intersection / union)
        candidates.append(
            {
                "component_id": index,
                "score": peaks[index],
                "voxel_count": pred_counts[index],
                "ious": overlaps,
                "matches": [i for i, value in enumerate(overlaps) if value >= min_iou],
            }
        )
    return {
        "reference_count": len(reference_ids),
        "reference_component_voxels": list(ref_counts.values()),
        "candidates": candidates,
        "reference_sha256": sha256_file(reference),
        "candidate_sha256": sha256_file(prediction),
    }


def evaluate_lesions(spec_path: Path) -> dict:
    """Require explicit patient/label/overlap declarations; never infer diagnoses."""
    if spec_path.stat().st_size > 1024**2:
        raise ValueError("Lesion specification exceeds 1 MiB.")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if (
        not isinstance(spec, dict)
        or not isinstance(spec.get("cases"), list)
        or not 1 <= len(spec["cases"]) <= 500
    ):
        raise ValueError("Expected 1..500 explicit lesion-evaluation cases.")
    min_iou = spec.get("min_iou")
    if type(min_iou) not in (int, float) or not 0 < min_iou <= 1:
        raise ValueError("Declare a minimum IoU in (0,1].")
    patients, ids, hashes, records = set(), set(), set(), []
    for row in spec["cases"]:
        if not isinstance(row, dict):
            raise ValueError("Each case must be an object.")
        for field in (
            "manifest",
            "case_id",
            "predictions",
            "patient_key",
            "reference_description",
            "overlap_evidence",
        ):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError("Explicit nonempty declaration required: " + field)
        if row.get("overlap_status") not in ("unknown", "known-overlap", "verified-independent"):
            raise ValueError("Explicit training-overlap status required.")
        if row["patient_key"].strip() in patients or row["case_id"].strip() in ids:
            raise ValueError("Duplicate patient or case ID.")
        patients.add(row["patient_key"].strip())
        ids.add(row["case_id"].strip())
    for row in spec["cases"]:
        matches = [
            c
            for c in read_cases(spec_path.parent / row["manifest"])
            if c.case_id == row["case_id"].strip()
        ]
        if len(matches) != 1 or matches[0].label_path is None:
            raise ValueError("Unique case with explicit source reference required.")
        case = matches[0]
        prediction, info = load_predictions(case, spec_path.parent / row["predictions"])
        check_geometry(load_volume(case.label_path), prediction)
        if info["source_sha256"] in hashes:
            raise ValueError("Duplicate source CT checksum.")
        hashes.add(info["source_sha256"])
        record = component_matches(
            case.label_path,
            spec_path.parent / row["predictions"] / "detection.nii.gz",
            label=row.get("reference_label"),
            min_iou=min_iou,
        )
        record.update(
            {
                "case_id": case.case_id,
                "source_sha256": info["source_sha256"],
                "reference_description": row["reference_description"],
                "reference_label": row["reference_label"],
                "overlap_status": row["overlap_status"],
                "overlap_evidence": row["overlap_evidence"],
            }
        )
        records.append(record)
    return {
        "schema_version": 1,
        "specification_sha256": sha256_file(spec_path),
        "analysis_kind": "exploratory annotation localization; clinical validation not established",
        "matching_policy": "26-connected components; maximum-cardinality one-to-one IoU matching; score >= threshold",
        "min_iou": min_iou,
        "scan_count": len(records),
        "cases": records,
        "curve": froc_curve(records),
        "pdac_classification": "not inferred from lesion annotations",
    }


def write_lesion_report(result: dict, output: Path) -> Path:
    if output.exists():
        raise ValueError("Lesion report exists; choose a fresh output directory.")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.mkdir(parents=True)
    write_json(output / "lesions.json", result)
    fig, ax = plt.subplots(figsize=(7, 4))
    points = [p for p in result["curve"] if p["sensitivity"] is not None]
    if points:
        ax.step(
            [p["false_positives_per_scan"] for p in points],
            [p["sensitivity"] for p in points],
            where="post",
            marker="o",
        )
    else:
        ax.text(
            0.5,
            0.5,
            "No reference lesions: sensitivity undefined",
            ha="center",
            transform=ax.transAxes,
        )
    ax.set(
        xlabel="Unmatched candidates per scan",
        ylabel="Matched reference-lesion fraction",
        title="Exploratory annotation-localization FROC",
        ylim=(-0.02, 1.02),
        xlim=(0, max(1.0, max(p["false_positives_per_scan"] for p in result["curve"]))),
    )
    ax.grid(alpha=0.3)
    fig.text(
        0.5,
        0.01,
        f"{result['scan_count']} demonstration scans; not independent clinical accuracy",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(output / "froc.png", dpi=150)
    plt.close(fig)
    rows = "".join(
        f"<tr><td>{html.escape(c['case_id'])}</td><td>{c['reference_count']}</td><td>{len(c['candidates'])}</td></tr>"
        for c in result["cases"]
    )
    page = output / "index.html"
    page.write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Lesion localization</title>'
        "<style>body{font:16px/1.5 system-ui;max-width:1000px;margin:2rem auto;padding:1rem}img{max-width:100%}td,th{padding:.5rem;border:1px solid #aaa}pre{white-space:pre-wrap}</style>"
        "<h1>Exploratory lesion-reference matching</h1><p>This checks connected annotation regions, not confirmed PDAC diagnosis. Training overlap is not excluded. "
        "This curve is not independent clinical sensitivity/specificity or the official PANORAMA benchmark. "
        "A two-case curve cannot establish generalization. Empty references do not establish non-PDAC.</p>"
        f'<p>Matching: explicit IoU &gt;= {result["min_iou"]}; one-to-one, 26-connected regions.</p><img src="froc.png" alt="Exploratory localization curve">'
        f"<table><tr><th>Case</th><th>Reference components</th><th>Retained candidates</th></tr>{rows}</table>"
        "<details><summary>Counts, thresholds and provenance</summary><pre>"
        + html.escape(json.dumps(result, indent=2))
        + "</pre></details></html>",
        encoding="utf-8",
    )
    return page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(write_lesion_report(evaluate_lesions(args.spec), args.output))
    except (OSError, ValueError, MemoryError) as exc:
        print(f"Lesion evaluation stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
