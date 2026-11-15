"""Local annotation and optional imported-prediction report; never runs inference."""

# HTML copy stays on complete lines for review alongside the generated report.
# ruff: noqa: E501

import argparse
import html
import json
import sys
from pathlib import Path

import numpy as np

from mirai_ct.cases import Case, read_cases
from mirai_ct.volume import Volume, check_geometry, iter_slices, load_volume, metadata

MSD_LABELS = {0: "Background", 1: "Pancreas", 2: "Cancer"}


def annotation_measurements(scan: Volume, mask: Volume) -> list[dict]:
    """Stream native axis-2 planes and aggregate dataset annotation voxels."""
    check_geometry(scan, mask)
    counts: dict[int, int] = {}
    bounds: dict[int, tuple[list[int], list[int]]] = {}
    for k, plane in enumerate(iter_slices(mask)):
        if (plane < 0).any() or (plane > 65535).any() or not np.equal(plane, np.floor(plane)).all():
            raise ValueError("Existing mask must contain nonnegative integer label IDs <= 65535.")
        ids, frequencies = np.unique(plane, return_counts=True)
        for raw_id, frequency in zip(ids, frequencies, strict=True):
            label_id = int(raw_id)
            counts[label_id] = counts.get(label_id, 0) + int(frequency)
            if label_id == 0:
                continue
            coordinates = np.argwhere(plane == raw_id)
            minimum = [int(coordinates[:, 0].min()), int(coordinates[:, 1].min()), k]
            maximum = [int(coordinates[:, 0].max()), int(coordinates[:, 1].max()), k]
            if label_id in bounds:
                old_min, old_max = bounds[label_id]
                minimum = [min(a, b) for a, b in zip(old_min, minimum, strict=True)]
                maximum = [max(a, b) for a, b in zip(old_max, maximum, strict=True)]
            bounds[label_id] = (minimum, maximum)

    unit_factor = {"meter": 1000.0, "mm": 1.0, "micron": 0.001}.get(scan.header.get_xyzt_units()[0])
    mm3_per_voxel = (
        abs(float(np.linalg.det(scan.affine[:3, :3]))) * unit_factor**3
        if unit_factor is not None
        else None
    )
    return [
        {
            "label_id": label_id,
            "voxel_count": count,
            "bbox_min_ijk": bounds[label_id][0] if label_id in bounds else None,
            "bbox_max_ijk": bounds[label_id][1] if label_id in bounds else None,
            "volume_mm3": count * mm3_per_voxel if mm3_per_voxel is not None else None,
            "volume_ml": count * mm3_per_voxel / 1000 if mm3_per_voxel is not None else None,
        }
        for label_id, count in sorted(counts.items())
    ]


def _name(label_id: int, source: str) -> str:
    if label_id == 0:
        return "Background"
    if "msd task07" in source.lower():
        return MSD_LABELS.get(label_id, "Unknown label")
    return "Unverified label meaning"


def _report_html(
    case: Case,
    scan: Volume,
    rows: list[dict],
    has_mask: bool,
    indices: list[int],
    prediction_info: dict | None = None,
    prediction_indices: list[int] | None = None,
    interactive_section: str = "",
    regions: list[dict] | None = None,
    has_model_outputs: bool = False,
    evaluation_section: str = "",
    summary: dict | None = None,
    model_measurements: dict | None = None,
    annotation_info: dict | None = None,
    additional_section: str = "",
    comparison: dict | None = None,
    explanation_info: dict | None = None,
) -> str:
    from mirai_ct.presentation import (
        experiment_explorer,
        presentation_assets,
        presentation_script,
        report_header,
    )

    info = metadata(scan)
    source = html.escape(case.dataset_source)
    title = html.escape(case.case_id)
    table_rows = []
    for row in rows:
        name = html.escape(
            annotation_info["description"]
            if annotation_info is not None and row["label_id"] == annotation_info["label_id"]
            else _name(row["label_id"], case.dataset_source)
        )
        bbox = (
            f"{row['bbox_min_ijk']} to {row['bbox_max_ijk']}"
            if row["bbox_min_ijk"] is not None
            else "—"
        )
        volume = (
            f"{row['volume_mm3']:.2f} mm³ ({row['volume_ml']:.4f} mL)"
            if row["volume_mm3"] is not None
            else "Unavailable: spatial units unknown"
        )
        table_rows.append(
            f"<tr><td>{row['label_id']}</td><td>{name}</td><td>{row['voxel_count']:,}</td>"
            f"<td>{bbox}</td><td>{volume}</td></tr>"
        )
    warning_items = "".join(f"<li>{html.escape(w)}</li>" for w in info["warnings"])
    warnings = (
        f"<ul>{warning_items}</ul>" if warning_items else "<p>None reported by geometry checks.</p>"
    )
    views = "".join(
        f'<figure><img src="axis-{axis}.png" alt="Native axis {axis} CT view'
        f'{" with existing dataset annotation overlay" if has_mask else ""}">'
        f"<figcaption>Native axis {axis}, zero-based slice {indices[axis]}</figcaption></figure>"
        for axis in range(3)
    )
    prediction_section = "<h2>Model inference</h2><p><strong>Predictions unavailable.</strong> No imported PANORAMA run was supplied to this report.</p>"
    region_section = ""
    if regions is not None:
        region_rows = "".join(
            f"<tr><td>{r['region_id']}</td><td>{r['bounds_ijk_inclusive']}</td>"
            f"<td>{[round(x, 2) for x in r['centroid_ras_mm']]}</td>"
            f"<td>{[round(x, 2) for x in r['extent_mm_native_axes']]}</td>"
            f"<td>{r['support_volume_ml']:.4f}</td><td>{r['score_max']:.6g}</td></tr>"
            for r in regions
        )
        region_section = f"""<h2>Retained candidate support regions</h2>
<p>Candidate support present: <strong>{"yes" if regions else "no"}</strong>. This is not a disease yes/no decision; no validated screening cutoff is established.</p>
<p>Regions are 26-connected positive map voxels. Bounds use inclusive native ijk indices; centroids use RAS millimetres. Extents include voxel widths along native axes. Support volume and box extents are not validated tumor volume or diameter. Head/body/tail is unassigned. No feature attribution is inferred from these measurements.</p>
<table><thead><tr><th>Region</th><th>Native bounds</th><th>RAS centroid (mm)</th><th>Native-axis extent (mm)</th><th>Support volume (mL)</th><th>Uncalibrated score</th></tr></thead><tbody>{region_rows or '<tr><td colspan="6">No retained candidate support</td></tr>'}</tbody></table>"""
    model_section = """<h2>Model segmentation and raw-probability heatmap</h2>
<p><strong>Unavailable in this imported bundle.</strong> The candidate map is a postprocessed detection output; it cannot reconstruct the missing model segmentation or raw probability values.</p>"""
    if has_model_outputs:
        model_views = "".join(
            f'<figure><img src="model-axis-{axis}.png" alt="CT, unvalidated model segmentation and raw class-1 probability"><figcaption>Native axis {axis}, slice {prediction_indices[axis]}</figcaption></figure>'
            for axis in range(3)
        )
        model_section = f"""<h2>Model segmentation and raw-probability heatmap</h2>
<p>These additional outputs are the stage-2 predicted class-1 segmentation and raw class-1 probability, pasted into the original grid. They are unvalidated model products. Zero padding outside the evaluated crop does not establish absence of disease. The probability overlay is uncalibrated model output, not Grad-CAM, attention or a validated explanation of the decision. Display opacity increases with raw probability so near-zero values leave CT visible; stored values and the fixed 0–1 color scale are unchanged.</p>{model_views}"""
        if model_measurements is not None:
            model_section += f"""<h3>Measurements of the actual predicted mask</h3>
<p>Predicted mask volume: {model_measurements["volume_ml"]:.4f} mL; {model_measurements["voxel_count"]:,} voxels.<br>
Inclusive native bounds: {model_measurements["bounds_ijk_inclusive"]}<br>
Native-axis bounding extents (mm): {model_measurements["extent_mm_native_axes"]}<br>
RAS centroid (mm): {model_measurements["centroid_ras_mm"]}</p>
<p>These measurements include all positive model voxels, including disconnected parts. They are unvalidated; bounding extent is not clinical tumor diameter. A zero mask does not establish absence of disease outside the evaluated crop.</p>"""
    if prediction_info is not None:
        run = prediction_info["run"]
        provenance = html.escape(
            json.dumps(
                {
                    "baseline_revision": run["baseline_revision"],
                    "nnunet_revision": run["nnunet_revision"],
                    "folds": run["folds"],
                    "runtime_seconds": run.get("runtime_seconds"),
                    "versions": run.get("versions"),
                    "resource_samples": run.get("resource_samples"),
                    "source_sha256": prediction_info["source_sha256"],
                    "suitability": prediction_info["input"]["suitability"],
                    "training_overlap": "unresolved; software smoke test only",
                },
                indent=2,
            )
        )
        prediction_views = "".join(
            f'<figure><img src="prediction-axis-{axis}.png" alt="CT, separate annotation and PANORAMA candidate map panels">'
            f"<figcaption>Candidate-map focus: native axis {axis}, zero-based slice {prediction_indices[axis]}</figcaption></figure>"
            for axis in range(3)
        )
        prediction_section = f"""<h2>Imported PANORAMA inference</h2>
<p><strong>PANORAMA candidate detection map</strong>; patient-level <strong>uncalibrated model score</strong>: {prediction_info["score"]:.6g}.</p>
<p>The map contains extracted candidate values from the baseline postprocessing. It is not Grad-CAM, a validated tumor segmentation, or a calibrated clinical risk probability. Zero values indicate no retained candidate value; they do not establish absence of disease. The score equals the map maximum. Output hashes and the native physical grid were checked during import; no resampling was used. Provenance is supplied by the run and is not cryptographic proof of execution.</p>
<p>Existing dataset annotations and model values appear in separate panels and legends. The source annotation never guided model preprocessing, segmentation, crop or detection. The static candidate views use the native k slice with the largest positive candidate cross-section (earliest tie), with i/j centered on that slice's candidate bounds; an all-zero map uses middle slices. This selection is for display only, not a tumor-boundary measurement.</p>
<details><summary>Run provenance and unresolved input suitability</summary><pre>{provenance}</pre></details>{prediction_views}"""
    summary_html = ""
    if summary is not None:
        sentences = "".join(f"<li>{html.escape(s)}</li>" for s in summary["sentences"])
        summary_html = f'<section class="notice"><h2>Research findings summary</h2><ul>{sentences}</ul></section>'
    annotation_note = ""
    if annotation_info is not None:
        annotation_note = f"""<p>Reference provenance checked against CT and mask SHA256. Selected source ROI {annotation_info["roi_number"]}: {html.escape(annotation_info["roi_name"])}; label {annotation_info["label_id"]}. Rasterization: {html.escape(annotation_info["rasterization"])}. This is a derived source annotation, not a model prediction or clinical diagnosis.</p>"""
    header = report_header(
        case.case_id,
        prediction_info["score"] if prediction_info else None,
        model_measurements,
        comparison,
        has_viewer=bool(interactive_section),
        has_model=has_model_outputs,
        has_evidence=bool(additional_section),
    )
    evidence_section = (
        f'<section class="report-section" id="evidence">{experiment_explorer(explanation_info)}{additional_section}</section>'
        if additional_section
        else ""
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Case report: {title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>.viewer-controls{{display:flex;flex-wrap:wrap;align-items:center;padding:1rem}}.viewer-panels{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}.viewer-panels figure{{min-width:0}}.viewer-panels canvas{{width:100%;height:auto;image-rendering:pixelated;background:#000}}@media(max-width:700px){{.viewer-panels{{grid-template-columns:1fr}}}}</style>
{presentation_assets()}</head>
<body>{header}<main>
<section id="summary" class="report-section">{summary_html}<p class="muted">Dataset source: {source}</p></section>
<section class="report-section">{interactive_section}</section>
<section class="report-section" id="model-products">{model_section if prediction_info is not None else prediction_section}</section>
{evidence_section}
<section class="report-section" id="reference-review">{evaluation_section}</section>
<details id="technical-details" class="technical-details"><summary>Technical details and source annotations</summary>
<p class="notice"><strong>Dataset annotation measurements are not a model prediction, clinical diagnosis, or performance result.</strong> Original CT and annotation files were read without modification. Model outputs, when imported, are labeled separately.</p>
<h2>CT geometry</h2>
<p>Dimensions (i, j, k): {info["shape"]} voxels<br>
Header spacing: {info["spacing"]} {html.escape(info["spatial_units"])}<br>
Affine spacing: {info["affine_spacing"]} {html.escape(info["spatial_units"])}<br>
Increasing voxel-axis directions: {info["orientation"]}<br>
qform code: {info["qform_code"]}; sform code: {info["sform_code"]}; obliquity: {info["obliquity_degrees"]} degrees</p>
<h3>Geometry warnings</h3>{warnings}
<p>Supplied annotation geometry: {"matched CT shape, units, spacing and affine; source pairing still requires dataset verification" if has_mask else "no annotation supplied"}.</p>
<h2>Dataset annotation measurements</h2>
{annotation_note}
<p>Label meanings follow the MSD Task07 dataset.json when the manifest names that dataset, or an explicitly supplied source-reference provenance record checked against the CT and mask hashes. Other IDs are not interpreted. Voxels are counted in native geometry. Volume uses the absolute affine determinant and documented spatial units; 1 mL = 1,000 mm³. Background is included in counts but has no region box.</p>
<p>Bounding boxes use original NIfTI voxel indices (i, j, k), zero-based with both minimum and maximum <strong>inclusive</strong>. They enclose all voxels of each label, including disconnected regions. They are axis-aligned in voxel space; direction letters above indicate increasing indices. These are not head/body/tail assignments.</p>
<table><thead><tr><th>Label ID</th><th>Meaning</th><th>Voxel count</th><th>Bounding box, inclusive</th><th>Physical volume</th></tr></thead><tbody>{"".join(table_rows) if rows else '<tr><td colspan="5">No annotation supplied</td></tr>'}</tbody></table>
<h2>Native CT views</h2><p>Each image shows CT and, when supplied, an existing annotation overlay. Planes are original voxel axes, not standardized radiological views. Display level 50/window 400 affects appearance only.</p>{views}
{prediction_section}
{region_section}
</details></main><footer class="report-footer">PANORAMA CT research report: {title}. Original CT geometry preserved. Head/body/tail requires an explicit reviewed anatomical source. Clinical validation remains pending.</footer>
{presentation_script()}</body></html>"""


def generate_report(
    case: Case,
    output: Path,
    predictions: Path | None = None,
    *,
    interactive: bool = False,
    measure_candidates: bool = False,
    reference_label: int | None = None,
    reference_description: str = "",
    annotation_provenance: Path | None = None,
    anatomy_mask: Path | None = None,
    anatomy_provenance: Path | None = None,
    explanation: Path | None = None,
) -> Path:
    """Write HTML/native views, plus separate imported-prediction views if supplied."""
    if output.exists():
        raise ValueError("Output directory already exists; choose a new name to preserve it.")
    if (anatomy_mask is None) != (anatomy_provenance is None):
        raise ValueError("Supply both anatomy mask and its explicit provenance.")
    if (interactive or measure_candidates) and predictions is None:
        raise ValueError(
            "Interactive viewer/candidate measurements requires a validated --predictions import."
        )
    evaluation, evaluation_section = None, ""
    if reference_label is not None or reference_description:
        if predictions is None or reference_label is None:
            raise ValueError("Reference comparison requires predictions, label ID and description.")
        from mirai_ct.evaluation import comparison_html, evaluate_case

        evaluation = evaluate_case(
            case,
            predictions,
            reference_label=reference_label,
            reference_description=reference_description,
        )
        evaluation_section = comparison_html(evaluation)
    scan = load_volume(case.scan_path)
    mask = load_volume(case.label_path) if case.label_path is not None else None
    annotation_info = None
    if annotation_provenance is not None:
        from mirai_ct.rtstruct import load_reference_provenance

        annotation_info = load_reference_provenance(
            case.scan_path, case.label_path, annotation_provenance
        )
    prediction, prediction_info, prediction_indices = None, None, None
    model_outputs, regions = {}, None
    if predictions is not None:
        from mirai_ct.panorama import load_predictions, prediction_focus

        prediction, prediction_info = load_predictions(case, predictions)
        prediction_indices = prediction_focus(prediction)
        from mirai_ct.panorama_outputs import load_model_outputs

        model_outputs = load_model_outputs(scan, predictions, prediction_info)
        if measure_candidates:
            from mirai_ct.findings import candidate_regions

            regions = candidate_regions(prediction)
    from mirai_ct.findings import findings_summary, segmentation_measurements

    model_measurements = (
        segmentation_measurements(model_outputs["segmentation"]) if model_outputs else None
    )
    anatomy_info, explanation_info = None, None
    if anatomy_mask is not None or explanation is not None:
        if not model_outputs:
            raise ValueError("Anatomy/explanation requires genuine imported model products.")
        if anatomy_mask is not None:
            from mirai_ct.anatomy import load_anatomy

            anatomy_info = load_anatomy(
                case.scan_path, model_outputs["segmentation"], anatomy_mask, anatomy_provenance
            )
        if explanation is not None:
            from mirai_ct.explanations import load_explanation

            explanation_info = load_explanation(
                explanation,
                prediction_info,
                model_outputs["segmentation"],
                model_outputs["probability"],
            )
    summary = findings_summary(
        prediction_info,
        regions,
        model_measurements,
        anatomy=anatomy_info,
        explanation=explanation_info,
    )
    rows = annotation_measurements(scan, mask) if mask is not None else []
    positives = [row for row in rows if row["label_id"] > 0]
    focus = next((row for row in positives if row["label_id"] == 2), None)
    focus = focus or (positives[0] if positives else None)
    indices = (
        [
            (lo + hi) // 2
            for lo, hi in zip(focus["bbox_min_ijk"], focus["bbox_max_ijk"], strict=True)
        ]
        if focus is not None
        else [size // 2 for size in scan.shape]
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from mirai_ct.visualization import plot_slice

    output.mkdir(parents=True)
    interactive_section = ""
    if interactive:
        from mirai_ct.viewer import export_viewer, viewer_html

        display_info = export_viewer(scan, prediction, mask, output / "viewer")
        interactive_section = viewer_html(display_info, case.case_id)
    for axis in range(3):
        figure = plot_slice(scan, axis=axis, index=indices[axis], mask=mask)
        try:
            figure.savefig(output / f"axis-{axis}.png", dpi=120)
        finally:
            plt.close(figure)
    if prediction is not None:
        for axis in range(3):
            figure = plot_slice(
                scan, axis=axis, index=prediction_indices[axis], mask=mask, prediction=prediction
            )
            try:
                figure.savefig(output / f"prediction-axis-{axis}.png", dpi=120)
            finally:
                plt.close(figure)
    if model_outputs:
        for axis in range(3):
            figure = plot_slice(
                scan,
                axis=axis,
                index=prediction_indices[axis],
                mask=model_outputs["segmentation"],
                prediction=model_outputs["probability"],
                probability_overlay=True,
            )
            figure.axes[1].set_title("Model class-1 segmentation (unvalidated)")
            figure.axes[2].set_title("Raw class-1 probability (uncalibrated)")
            figure.axes[-1].set_ylabel("Raw model probability; not attribution")
            try:
                figure.savefig(output / f"model-axis-{axis}.png", dpi=120)
            finally:
                plt.close(figure)
    from mirai_ct.panorama_io import write_json

    additional_section = ""
    if anatomy_info is not None or explanation_info is not None:
        from mirai_ct.explanations import evidence_html, plot_explanation

        additional_section = evidence_html(anatomy_info, explanation_info)
        if explanation_info is not None:
            for axis in range(3):
                figure = plot_explanation(scan, explanation_info, axis, prediction_indices[axis])
                try:
                    figure.savefig(output / f"explanation-axis-{axis}.png", dpi=120)
                finally:
                    plt.close(figure)
    write_json(
        output / "report.json",
        {
            "schema_version": 1,
            "case_id": case.case_id,
            "source_sha256": prediction_info["source_sha256"] if prediction_info else None,
            "uncalibrated_score": prediction_info["score"] if prediction_info else None,
            "screening_decision": "not established; no validated cutoff",
            "candidate_regions": regions,
            "model_segmentation_available": bool(model_outputs),
            "raw_probability_available": bool(model_outputs),
            "attribution_available": explanation_info is not None,
            "explanation": explanation_info,
            "anatomical_subregion": anatomy_info["assignment"] if anatomy_info else "unassigned",
            "anatomy_result": anatomy_info,
            "clinical_validation": "not established",
            "reference_comparison": evaluation,
            "findings_summary": summary,
            "model_segmentation_measurements": model_measurements,
            "annotation_provenance": annotation_info,
        },
    )
    report = output / "index.html"
    report.write_text(
        _report_html(
            case,
            scan,
            rows,
            mask is not None,
            indices,
            prediction_info,
            prediction_indices,
            interactive_section,
            regions,
            bool(model_outputs),
            evaluation_section,
            summary,
            model_measurements,
            annotation_info,
            additional_section,
            evaluation,
            explanation_info,
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-case local annotation/imported-prediction report; no inference execution."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", type=Path, required=True, help="New local output directory")
    parser.add_argument(
        "--predictions", type=Path, help="Validated local PANORAMA import directory"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Add offline native-k slice navigation"
    )
    parser.add_argument(
        "--measure-candidates",
        action="store_true",
        help="Add connected candidate support geometry (requires optional SimpleITK)",
    )
    parser.add_argument("--reference-label", type=int, help="Explicit annotation ID to compare")
    parser.add_argument("--reference-description", default="", help="Source and meaning of that ID")
    parser.add_argument(
        "--annotation-provenance", type=Path, help="Source reference.json to validate"
    )
    parser.add_argument("--anatomy-mask", type=Path)
    parser.add_argument("--anatomy-provenance", type=Path)
    parser.add_argument(
        "--explanation", type=Path, help="Genuine signed occlusion explanation.json"
    )
    args = parser.parse_args()
    try:
        matches = [case for case in read_cases(args.manifest) if case.case_id == args.case_id]
        if not matches:
            raise ValueError(f"Case ID not found in manifest: {args.case_id}")
        report = generate_report(
            matches[0],
            args.output,
            args.predictions,
            interactive=args.interactive,
            measure_candidates=args.measure_candidates,
            reference_label=args.reference_label,
            reference_description=args.reference_description,
            annotation_provenance=args.annotation_provenance,
            anatomy_mask=args.anatomy_mask,
            anatomy_provenance=args.anatomy_provenance,
            explanation=args.explanation,
        )
        print(
            json.dumps(
                {"report": str(report), "kind": "local annotation/imported prediction report"}
            )
        )
        return 0
    except (OSError, ValueError, MemoryError) as exc:
        print(f"Report failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
