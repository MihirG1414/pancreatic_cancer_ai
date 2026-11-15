"""Offline presentation chrome for checked research report values."""

# ruff: noqa: E501

import html
import json
from pathlib import Path


def presentation_assets() -> str:
    assets = Path(__file__).parent / "assets"
    return "<style>" + (assets / "report.css").read_text(encoding="utf-8") + "</style>"


def presentation_script() -> str:
    return (
        "<script>"
        + (Path(__file__).parent / "assets/report.js").read_text(encoding="utf-8")
        + "</script>"
    )


def report_header(
    case_id: str,
    score: float | None,
    measurements: dict | None,
    comparison: dict | None,
    *,
    has_viewer: bool,
    has_model: bool,
    has_evidence: bool,
) -> str:
    cards = [
        (
            "Model score",
            f"{score:.6f}" if score is not None else "Unavailable",
            "Uncalibrated; not cancer risk",
        ),
        (
            "Predicted mask",
            f"{measurements['volume_ml']:.2f} mL" if measurements else "Unavailable",
            "Native-grid model measurement",
        ),
    ]
    model_overlap = comparison.get("model_segmentation_overlap") if comparison else None
    cards.append(
        (
            "Model-mask Dice",
            f"{model_overlap['dice']:.3f}" if model_overlap else "Unavailable",
            "Single-case source overlap",
        )
    )
    cards.append(("Clinical validation", "Pending", "Independent cohort and expert review"))
    tiles = "".join(
        f'<div class="metric"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>'
        for label, value, note in cards
    )
    links = [("summary", "Overview")]
    if has_viewer:
        links.append(("slice-viewer", "Explore CT"))
    if has_model:
        links.append(("model-products", "Model outputs"))
    if has_evidence:
        links.append(("evidence", "Explanation"))
    if comparison:
        links.append(("reference-review", "Reference review"))
    links.append(("technical-details", "Technical details"))
    nav = "".join(f'<a href="#{target}">{label}</a>' for target, label in links)
    return f"""<header class="report-hero"><p class="eyebrow">PANORAMA / CT RESEARCH WORKSPACE</p>
<div class="hero-title"><h1>{html.escape(case_id)}</h1><span class="research-badge">Research prototype</span></div>
<p>Pretrained inference, original-grid measurements and traceable visual evidence.</p>
<div class="metrics">{tiles}</div></header>
<nav class="report-nav" aria-label="Report sections">{nav}<span class="nav-actions">
<button id="presentation-mode" type="button" aria-pressed="false">Presentation view</button>
<button id="print-report" type="button">Print / save PDF</button></span></nav>
<p class="research-note">Model scores are uncalibrated. This report does not establish a clinical diagnosis or independent screening accuracy.</p>"""


def experiment_explorer(explanation: dict | None) -> str:
    if explanation is None:
        return ""
    data = {
        "baseline": explanation["baseline_score"],
        "scores": [row["occluded_score"] for row in explanation["blocks"]],
        "effects": [row["effect"] for row in explanation["blocks"]],
    }
    options = "".join(
        f'<option value="{i}">Block {i + 1} (change {value:+.6f})</option>'
        for i, value in enumerate(data["effects"])
    )
    payload = json.dumps(data, allow_nan=False).replace("<", "\\u003c")
    return f"""<section class="experiment-card" aria-labelledby="experiment-title">
<p class="eyebrow">GENUINE GPU EXPERIMENTS / SECOND-STAGE FIXED TARGET</p>
<h3 id="experiment-title">What changes when a block is obscured?</h3>
<p>Select one of the completed experiments. This compares mean lesion-class probability over the same original predicted voxels, not the final patient score.</p>
<label for="occlusion-block">Completed occlusion experiment</label> <select id="occlusion-block">{options}</select>
<div class="score-bars"><div>Unchanged input <strong id="control-score"></strong><div class="bar-track"><div id="control-bar" class="score-bar"></div></div></div>
<div>Occluded input <strong id="occluded-score"></strong><div class="bar-track"><div id="occluded-bar" class="score-bar occluded"></div></div></div></div>
<output id="experiment-result" aria-live="polite"></output>
<p><small>Bars use the same 0–1 target-score scale. A positive baseline-minus-occluded change means the intervention reduced this target. Block locations and all signed results follow below.</small></p>
<script id="experiment-data" type="application/json">{payload}</script></section>"""
