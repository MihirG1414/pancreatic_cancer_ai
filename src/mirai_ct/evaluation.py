"""Explicit reference comparisons; never infer PDAC diagnosis from mask labels."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from mirai_ct.cases import Case, read_cases
from mirai_ct.panorama import load_predictions
from mirai_ct.panorama_io import sha256_file
from mirai_ct.panorama_outputs import load_model_outputs
from mirai_ct.volume import Volume, check_geometry, load_volume, read_slice


def overlap_metrics(
    reference: Volume, prediction: Volume, *, reference_label: int, binary_prediction: bool
) -> dict[str, Any]:
    """Count native-grid voxels one plane at a time; positive candidates use >0."""
    if type(reference_label) is not int or not 1 <= reference_label <= 65535:
        raise ValueError("reference_label must be a positive integer <= 65535.")
    check_geometry(reference, prediction)
    reference_count = predicted_count = intersection = 0
    for k in range(reference.shape[2]):
        ref, pred = read_slice(reference, 2, k), read_slice(prediction, 2, k)
        if (
            not np.isfinite(ref).all()
            or (ref < 0).any()
            or (ref > 65535).any()
            or not np.equal(ref, np.floor(ref)).all()
        ):
            raise ValueError("Reference must contain finite nonnegative integer labels <= 65535.")
        if not np.isfinite(pred).all() or (pred < 0).any() or (pred > 1).any():
            raise ValueError("Prediction values must be finite and in [0, 1].")
        if binary_prediction and not np.equal(pred, np.floor(pred)).all():
            raise ValueError("Model segmentation must be binary, not a probability map.")
        ref_positive, pred_positive = ref == reference_label, pred > 0
        reference_count += int(np.count_nonzero(ref_positive))
        predicted_count += int(np.count_nonzero(pred_positive))
        intersection += int(np.count_nonzero(ref_positive & pred_positive))
    total = reference_count + predicted_count
    union = total - intersection
    return {
        "reference_voxels": reference_count,
        "predicted_voxels": predicted_count,
        "intersection_voxels": intersection,
        "false_positive_voxels": predicted_count - intersection,
        "false_negative_voxels": reference_count - intersection,
        "dice": 2 * intersection / total if total else None,
        "iou": intersection / union if union else None,
        "empty_reference": reference_count == 0,
        "both_empty": total == 0,
    }


def classification_metrics(
    labels: Sequence[int], scores: Sequence[float], *, threshold: float
) -> dict[str, Any]:
    """Binary operating-point metrics and rank AUC with half credit for ties."""
    if not labels or len(labels) != len(scores):
        raise ValueError("Provide equal nonempty label and score sequences.")
    if any(type(value) is not int or value not in (0, 1) for value in labels):
        raise ValueError("Explicit binary integer PDAC references (0/1) are required.")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not 0 <= value <= 1
        for value in [*scores, threshold]
    ):
        raise ValueError("Scores and threshold must be finite numbers in [0, 1].")
    y, s = np.asarray(labels), np.asarray(scores, dtype=np.float64)
    positive = y == 1
    predicted = s >= threshold
    tp = int(np.count_nonzero(predicted & positive))
    fp = int(np.count_nonzero(predicted & ~positive))
    tn = int(np.count_nonzero(~predicted & ~positive))
    fn = int(np.count_nonzero(~predicted & positive))
    n_positive, n_negative = tp + fn, tn + fp
    auc = None
    if n_positive and n_negative:
        order = np.argsort(s, kind="stable")
        sorted_scores, sorted_y = s[order], y[order]
        rank_sum, start = 0.0, 0
        while start < len(s):
            end = start + 1
            while end < len(s) and sorted_scores[end] == sorted_scores[start]:
                end += 1
            # 1-based average rank within this tied group.
            rank_sum += (start + 1 + end) / 2 * int(np.count_nonzero(sorted_y[start:end]))
            start = end
        auc = (rank_sum - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative)
    return {
        "case_count": len(labels),
        "positive_cases": n_positive,
        "negative_cases": n_negative,
        "threshold": threshold,
        "decision_rule": "score >= threshold",
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "sensitivity": tp / n_positive if n_positive else None,
        "specificity": tn / n_negative if n_negative else None,
        "roc_auc": auc,
    }


def evaluate_case(
    case: Case,
    predictions: Path,
    *,
    reference_label: int | None = None,
    reference_description: str = "",
) -> dict[str, Any]:
    """Evaluate validated products, with label meaning supplied by the operator."""
    if not isinstance(reference_description, str):
        raise ValueError("Reference description must be text.")
    if reference_label is not None and (
        type(reference_label) is not int or not 1 <= reference_label <= 65535
    ):
        raise ValueError("Reference label must be a positive integer <= 65535.")
    if reference_label is not None and not reference_description.strip():
        raise ValueError("An explicit reference description is required with a reference label.")
    if reference_label is None and reference_description.strip():
        raise ValueError("A reference description requires a reference label.")
    if reference_label is not None and case.label_path is None:
        raise ValueError("No reference segmentation path is present in the case manifest.")
    prediction, info = load_predictions(case, predictions)
    scan = load_volume(case.scan_path)
    outputs = load_model_outputs(scan, predictions, info)
    candidate, segmentation, reference_hash = None, None, None
    if reference_label is not None:
        reference = load_volume(case.label_path)
        check_geometry(scan, reference)
        reference_hash = sha256_file(case.label_path)
        candidate = overlap_metrics(
            reference, prediction, reference_label=reference_label, binary_prediction=False
        )
        if outputs:
            segmentation = overlap_metrics(
                reference,
                outputs["segmentation"],
                reference_label=reference_label,
                binary_prediction=True,
            )
    return {
        "schema_version": 1,
        "case_id": case.case_id,
        "dataset_source": case.dataset_source,
        "source_sha256": info["source_sha256"],
        "detection_sha256": info["detection_sha256"],
        "model_output_sha256": info.get("model_output_sha256", {}),
        "reference_sha256": reference_hash,
        "reference_label": reference_label,
        "reference_description": reference_description,
        "score": info["score"],
        "pdac_reference": None,
        "independent_validation": False,
        "candidate_support_overlap": candidate,
        "model_segmentation_overlap": segmentation,
        "model_segmentation_available": bool(outputs),
        "limitations": [
            "Candidate support is postprocessed detection output, not tumor segmentation.",
            "Reference label meaning is supplied explicitly; no PDAC diagnosis is inferred.",
            "Both-empty overlap is undefined (null); an empty mask does not prove no PDAC.",
            "Single-case overlap is not sensitivity, specificity, FROC or generalization.",
            "Scores are uncalibrated; raw probabilities are not decision attribution.",
        ],
    }


def _case(manifest: Path, case_id: str) -> Case:
    matches = [case for case in read_cases(manifest) if case.case_id == case_id]
    if not matches:
        raise ValueError(f"Case ID not found: {case_id}")
    return matches[0]


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Nonempty {name} is required.")
    return value.strip()


def evaluate_cohort(path: Path) -> dict[str, Any]:
    """Local JSON specification; explicit diagnoses, separation and overlap audit."""
    if path.stat().st_size > 1024**2:
        raise ValueError("Cohort specification exceeds 1 MiB.")
    spec = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise ValueError("Cohort specification must be a JSON object.")
    threshold_source = _text(spec.get("threshold_source"), "threshold_source")
    threshold = spec.get("threshold")
    rows = spec.get("cases")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError("Cohort must contain 1–500 explicit case records.")
    # Validate all declarations before opening any scans.
    patients, case_ids = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each case record must be an object.")
        for key in ("manifest", "case_id", "predictions", "patient_key", "diagnosis_reference"):
            _text(row.get(key), key)
        if type(row.get("pdac_label")) is not int or row["pdac_label"] not in (0, 1):
            raise ValueError("Explicit integer pdac_label 0/1 required; never infer from masks.")
        if row["patient_key"].strip() in patients:
            raise ValueError("Duplicate patient key; use one evaluation scan per patient.")
        if row["case_id"].strip() in case_ids:
            raise ValueError("Duplicate case ID.")
        patients.add(row["patient_key"].strip())
        case_ids.add(row["case_id"].strip())
        if row.get("overlap_status") not in ("unknown", "known-overlap", "verified-independent"):
            raise ValueError("Invalid overlap_status: unknown/known-overlap/verified-independent.")
        _text(row.get("overlap_evidence"), "overlap_evidence")
    classification_metrics(
        [row["pdac_label"] for row in rows], [0.0] * len(rows), threshold=threshold
    )
    records, source_hashes = [], set()
    for row in rows:
        case = _case(path.parent / row["manifest"], row["case_id"])
        record = evaluate_case(
            case,
            path.parent / row["predictions"],
            reference_label=row.get("reference_label"),
            reference_description=row.get("reference_description", ""),
        )
        if record["source_sha256"] in source_hashes:
            raise ValueError("Duplicate source CT checksum, even with a different patient key.")
        source_hashes.add(record["source_sha256"])
        record.update(
            {
                "pdac_reference": row["pdac_label"],
                "diagnosis_reference": row["diagnosis_reference"],
                "overlap_status": row["overlap_status"],
                "overlap_evidence": row["overlap_evidence"],
            }
        )
        records.append(record)
    independent = all(row["overlap_status"] == "verified-independent" for row in rows)
    return {
        "schema_version": 1,
        "analysis_kind": (
            "independence declared by operator; clinical validation not established"
            if independent
            else "exploratory; training overlap not excluded"
        ),
        "specification_sha256": sha256_file(path),
        "threshold_source": threshold_source,
        "classification": classification_metrics(
            [row["pdac_label"] for row in rows], [r["score"] for r in records], threshold=threshold
        ),
        "cases": records,
        "limitations": [
            "Independence declarations require external audit; software cannot establish them.",
            "The supplied operating point is not automatically a validated clinical cutoff.",
            "No FROC, confidence intervals or clinical validation are established by this report.",
            "Segmentation metrics require compatible reference semantics and actual model masks.",
        ],
    }


def comparison_html(result: dict[str, Any]) -> str:
    """Human-readable one-case section, with prediction types kept distinct."""
    rows = []
    for key, title in (
        ("candidate_support_overlap", "Candidate support (not tumor segmentation)"),
        ("model_segmentation_overlap", "Model class-1 segmentation"),
    ):
        metrics = result.get(key)
        if metrics is None:
            rows.append(
                f'<tr><td>{title}</td><td colspan="3">Unavailable / not evaluated</td></tr>'
            )
        else:
            dice = "Undefined (both empty)" if metrics["dice"] is None else f"{metrics['dice']:.4f}"
            iou = "Undefined (both empty)" if metrics["iou"] is None else f"{metrics['iou']:.4f}"
            counts = (
                f"{metrics['intersection_voxels']:,} intersection; "
                f"{metrics['predicted_voxels']:,} predicted; "
                f"{metrics['reference_voxels']:,} reference"
            )
            rows.append(f"<tr><td>{title}</td><td>{dice}</td><td>{iou}</td><td>{counts}</td></tr>")
    description = html.escape(result.get("reference_description", "Not supplied"))
    return (
        "<section><h2>Comparison with the supplied annotation</h2>"
        f"<p>Reference: {description}. Label ID: {result.get('reference_label')}.</p>"
        "<table><thead><tr><th>Output compared</th><th>Dice</th><th>IoU</th>"
        "<th>Native voxel counts</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        "<p>This is a single-case comparison. Candidate-support overlap does not measure "
        "model tumor-segmentation accuracy. No independent accuracy, clinical diagnosis "
        "or validated screening cutoff is established.</p></section>"
    )


def write_evaluation(result: dict[str, Any], output: Path) -> Path:
    """Keep JSON reproducible and readable HTML self-contained; never overwrite."""
    if output.exists():
        raise ValueError("Evaluation output directory already exists; choose a new name.")
    result = {**result, "evaluated_utc": datetime.now(UTC).isoformat()}
    raw = json.dumps(result, indent=2, allow_nan=False)
    output.mkdir(parents=True)
    (output / "evaluation.json").write_text(raw + "\n", encoding="utf-8")
    text = html.escape(raw)
    page = output / "index.html"
    summary = comparison_html(result) if "case_id" in result else ""
    page.write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>PANORAMA reference comparison</title><style>"
        "body{font:16px/1.5 system-ui;max-width:1000px;margin:2rem auto;padding:1rem}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef5f8;padding:1rem}"
        "table{border-collapse:collapse}th,td{border:1px solid #aaa;padding:.5rem}"
        "</style><h1>PANORAMA reference comparison</h1>"
        "<p>Candidate-support overlap and actual model-segmentation overlap are separate. "
        "A null segmentation result means unavailable or not evaluated. "
        "These results do not establish clinical accuracy or a diagnosis.</p>"
        f"{summary}<details><summary>Full measurements and provenance</summary>"
        f"<pre>{text}</pre></details></html>",
        encoding="utf-8",
    )
    return page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("case", help="Compare one validated import with an explicit label")
    single.add_argument("--manifest", type=Path, required=True)
    single.add_argument("--case-id", required=True)
    single.add_argument("--predictions", type=Path, required=True)
    single.add_argument("--reference-label", type=int, required=True)
    single.add_argument("--reference-description", required=True)
    single.add_argument("--output", type=Path, required=True)
    cohort = sub.add_parser("cohort", help="Explicit patient-separated PDAC-reference cohort")
    cohort.add_argument("--specification", type=Path, required=True)
    cohort.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Evaluation output directory already exists; choose a new name.")
        result = (
            evaluate_case(
                _case(args.manifest, args.case_id),
                args.predictions,
                reference_label=args.reference_label,
                reference_description=args.reference_description,
            )
            if args.command == "case"
            else evaluate_cohort(args.specification)
        )
        print(write_evaluation(result, args.output))
    except (OSError, ValueError, TypeError, KeyError, MemoryError) as exc:
        print(f"Evaluation stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
