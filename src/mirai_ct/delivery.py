"""Build one offline demonstration entry point from checked existing imports."""

# Keep complete HTML strings readable alongside generated pages.
# ruff: noqa: E501

import argparse
import html
import json
import shutil
import sys
from pathlib import Path

from mirai_ct.cases import read_cases
from mirai_ct.panorama_io import sha256_file, write_json
from mirai_ct.presentation import presentation_assets
from mirai_ct.report import generate_report


def write_delivery_notes(site: Path) -> None:
    """Keep opening instructions and source credits with the portable report."""
    (site / "HOW-TO-OPEN.txt").write_text(
        "Extract the entire ZIP first, then open index.html in a modern browser.\n"
        "Keep all case and viewer folders together. No Python, GPU or internet is needed.\n"
        "Choose a case, then use Previous/Next, the slice slider, zoom and overlay controls.\n"
        "Source annotations, model candidates, model masks and probability are separate.\n"
        "Where supplied, the explanation explorer compares genuine saved stage-2 occlusion experiments.\n"
        "Presentation view reduces technical detail; Print / save PDF uses the browser print dialog.\n"
        "This is a research demonstration, not a clinical diagnosis or validated screening tool.\n"
        "Scores are uncalibrated. Two selected cases do not establish clinical accuracy.\n"
        "Head/body/tail labels and independent clinical review remain unavailable.\n",
        encoding="utf-8",
    )
    (site / "DATA-SOURCES.txt").write_text(
        "Model: DIAGNijmegen PANORAMA baseline, pretrained research inference.\n"
        "https://github.com/DIAGNijmegen/PANORAMA_baseline\n"
        "Weights and their use conditions: https://zenodo.org/records/11160381\n\n"
        "Case 1: Medical Segmentation Decathlon, Task07 Pancreas, pancreas_290.\n"
        "Source CT and existing tumor annotation; CC-BY-SA 4.0.\n"
        "https://medicaldecathlon.com/\n"
        "https://registry.opendata.aws/msd/\n"
        "https://creativecommons.org/licenses/by-sa/4.0/\n\n"
        "Case 2: TCIA CPTAC-PDA, one public CT series and matched tumor RTSTRUCT.\n"
        "https://www.cancerimagingarchive.net/collection/cptac-pda/\n"
        "https://www.cancerimagingarchive.net/analysis-result/cptac-pda-tumor-annotations/\n\n"
        "Source annotations are reference displays, not PANORAMA predictions or confirmed PDAC diagnoses.\n"
        "Display copies use a CT window and model/reference overlays; the native reference mask\n"
        "was rasterized from source contours for case 2. Original volumes are not in this ZIP.\n"
        "Consult the linked source citation and use conditions before redistribution or deployment.\n"
        "No commercial permission or clinical clearance is asserted by this package.\n",
        encoding="utf-8",
    )


def build_delivery(spec_path: Path, output: Path) -> Path:
    if output.exists():
        raise ValueError("Delivery output exists; choose a fresh folder.")
    if spec_path.stat().st_size > 1024**2:
        raise ValueError("Delivery specification exceeds 1 MiB.")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if (
        not isinstance(spec, dict)
        or not isinstance(spec.get("cases"), list)
        or not 1 <= len(spec["cases"]) <= 20
    ):
        raise ValueError("Provide 1..20 explicit demo case records.")
    ids = set()
    for row in spec["cases"]:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(key), str) or not row[key].strip()
            for key in ("manifest", "case_id", "predictions")
        ):
            raise ValueError("Manifest, case ID and validated prediction directory required.")
        if row["case_id"].strip() in ids:
            raise ValueError("Duplicate demo case ID.")
        ids.add(row["case_id"].strip())
    output.mkdir(parents=True)
    site = output / "site"
    site.mkdir()
    records, hashes, cards = [], set(), []
    try:
        for number, row in enumerate(spec["cases"], 1):
            matches = [
                case
                for case in read_cases(spec_path.parent / row["manifest"])
                if case.case_id == row["case_id"].strip()
            ]
            if len(matches) != 1:
                raise ValueError("Expected exactly one manifest case.")
            kwargs = {
                key: row[key] for key in ("reference_label", "reference_description") if key in row
            }
            for key in (
                "annotation_provenance",
                "anatomy_mask",
                "anatomy_provenance",
                "explanation",
            ):
                if row.get(key) is not None:
                    kwargs[key] = spec_path.parent / row[key]
            print(f"Building case {number}/{len(spec['cases'])}: {matches[0].case_id}", flush=True)
            report = generate_report(
                matches[0],
                site / f"case-{number}",
                spec_path.parent / row["predictions"],
                interactive=True,
                measure_candidates=True,
                **kwargs,
            )
            data = json.loads((report.parent / "report.json").read_text(encoding="utf-8"))
            page_html = report.read_text(encoding="utf-8").replace(
                '<nav class="report-nav" aria-label="Report sections">',
                '<nav class="report-nav" aria-label="Report sections"><a href="../index.html">&larr; All cases</a>',
            )
            report.write_text(page_html, encoding="utf-8")
            if not data["model_segmentation_available"] or not data["raw_probability_available"]:
                raise ValueError(
                    "Review delivery requires actual model mask and probability products."
                )
            if data["source_sha256"] in hashes:
                raise ValueError("Duplicate source CT; repeated runs are not extra demo cases.")
            hashes.add(data["source_sha256"])
            records.append(data)
            mask = data["model_segmentation_measurements"]
            size = f"{mask['volume_ml']:.2f} mL" if mask else "unavailable"
            explanation = (
                "available (fixed stage-2 target)"
                if data["attribution_available"]
                else "not supplied"
            )
            anatomy = data["anatomical_subregion"]
            if data["anatomy_result"]:
                provenance = data["anatomy_result"]["provenance"]
                anatomy += f" ({provenance['source_type']}; {provenance['review_status']})"
            comparison = data["reference_comparison"]
            overlap = comparison.get("model_segmentation_overlap") if comparison else None
            dice = f"{overlap['dice']:.3f}" if overlap else "Unavailable"
            cards.append(
                f'<article class="case-card"><p class="eyebrow">REAL CT / CASE {number:02d}</p><h2>{html.escape(data["case_id"])}</h2>'
                f'<a href="case-{number}/index.html"><img src="case-{number}/prediction-axis-2.png" '
                'alt="CT, separate source annotation and model candidate panels"></a>'
                f"<dl><div><dt>Uncalibrated score</dt><dd>{data['uncalibrated_score']:.6f}</dd></div><div><dt>Predicted mask</dt><dd>{size}</dd></div>"
                f"<div><dt>Model-mask Dice</dt><dd>{dice}</dd></div><div><dt>Head/body/tail</dt><dd>{html.escape(anatomy)}</dd></div></dl>"
                '<span class="evidence-tag">Model mask + raw probability</span>'
                f'<p class="muted">Input-occlusion evidence: {explanation}</p>'
                f'<a class="button" href="case-{number}/index.html">Open case report</a>'
                f'<a class="secondary-link" href="case-{number}/index.html#slice-viewer">Go to CT viewer &rarr;</a></article>'
            )
        evaluation = ""
        if spec.get("lesion_spec") is not None:
            from mirai_ct.lesion_evaluation import evaluate_lesions, write_lesion_report

            result = evaluate_lesions(spec_path.parent / spec["lesion_spec"])
            if {r["case_id"] for r in result["cases"]} != ids:
                raise ValueError("Lesion evaluation must describe the displayed demo cases.")
            for record in result["cases"]:
                report = next(r for r in records if r["case_id"] == record["case_id"])
                comparison = report["reference_comparison"]
                if (
                    comparison is None
                    or any(
                        record[key] != comparison[key]
                        for key in ("source_sha256", "reference_sha256", "reference_label")
                    )
                    or record["candidate_sha256"] != comparison["detection_sha256"]
                ):
                    raise ValueError(
                        "Lesion analysis differs from displayed source/reference/predictions."
                    )
            write_lesion_report(result, site / "lesion-review")
            evaluation = '<p><a class="button" href="lesion-review/index.html">Open exploratory lesion-reference review</a></p>'
        page = site / "index.html"
        page.write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>PANORAMA CT research demo</title>" + presentation_assets() + "</head><body>"
            '<header class="landing-hero"><p class="eyebrow">PANORAMA / REVIEW WORKSPACE</p><div class="hero-title"><h1>From CT to visual evidence</h1><span class="research-badge">Research prototype</span></div>'
            f"<p>{len(records)} real CT case demonstrations. Explore pretrained model outputs on the original scan grid.</p>"
            f'<div class="metrics"><div class="metric"><span>Real CT cases</span><strong>{len(records)}</strong><small>Distinct input scans</small></div>'
            f'<div class="metric"><span>Genuine explanations</span><strong>{sum(r["attribution_available"] for r in records)}</strong><small>Saved controlled GPU experiments</small></div>'
            '<div class="metric"><span>Review mode</span><strong>Offline</strong><small>No live GPU or network needed</small></div><div class="metric"><span>Clinical validation</span><strong>Pending</strong><small>Independent cohort and expert review</small></div></div></header>'
            '<section class="report-section"><h2>The working pipeline</h2><div class="pipeline"><div><strong>01 / Intake</strong><small>Read CT, verify geometry and source identity</small></div><div><strong>02 / PANORAMA</strong><small>Pretrained pancreas localization and stage-2 inference</small></div><div><strong>03 / Evidence</strong><small>Mask, probability, measurements and optional occlusion</small></div><div><strong>04 / Review</strong><small>Explore native slices and compare source references</small></div></div>'
            '<p class="research-note">Scores are uncalibrated; reference annotations '
            "and model predictions are shown separately. These examples do not establish a "
            "clinical diagnosis or independent screening accuracy. Head/body/tail needs an "
            "explicit anatomical source; probability alone is not decision attribution.</p></section>"
            '<div class="cases">'
            + "".join(cards)
            + '</div><section class="report-section"><h2>Reference review</h2>'
            + evaluation
            + "<p>Per-case reports include native-grid measurements and source-annotation overlap. "
            "Clinical ROC-AUC, sensitivity and specificity remain unestablished without an "
            'audited positive/negative patient cohort and a declared operating point.</p></section><footer class="report-footer">Pretrained PANORAMA research integration. Source credits and opening instructions are included as DATA-SOURCES.txt and HOW-TO-OPEN.txt.</footer></body></html>',
            encoding="utf-8",
        )
        write_delivery_notes(site)
        archive = Path(shutil.make_archive(str(output / "panorama-research-demo"), "zip", site))
        write_json(
            output / "delivery.json",
            {
                "schema_version": 1,
                "status": "success",
                "specification_sha256": sha256_file(spec_path),
                "case_count": len(records),
                "source_sha256": [r["source_sha256"] for r in records],
                "anatomy_cases": sum(r["anatomy_result"] is not None for r in records),
                "explanation_cases": sum(r["attribution_available"] for r in records),
                "shareable_report": archive.name,
                "report_zip_sha256": sha256_file(archive),
                "clinical_validation": "not established",
            },
        )
        return page
    except Exception as exc:
        write_json(output / "delivery-failure.json", {"status": "failed", "error": str(exc)})
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(build_delivery(args.spec, args.output))
    except (OSError, ValueError, MemoryError) as exc:
        print(f"Delivery stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
