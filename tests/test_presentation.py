"""Presentation must retain evidence meaning and support absent products."""

import json

from mirai_ct.presentation import experiment_explorer, report_header


def test_report_cards_use_model_mask_overlap_and_escape_case_name():
    text = report_header(
        "case<script>",
        0.97,
        {"volume_ml": 47.6794},
        {
            "candidate_support_overlap": {"dice": 0.99},
            "model_segmentation_overlap": {"dice": 0.752822},
        },
        has_viewer=True,
        has_model=True,
        has_evidence=False,
    )
    assert "case&lt;script&gt;" in text and "case<script>" not in text
    assert ">0.753<" in text and ">0.990<" not in text
    assert "Uncalibrated; not cancer risk" in text
    assert 'href="#evidence"' not in text
    assert 'href="#slice-viewer"' in text


def test_saved_experiment_values_are_exact_and_absence_is_not_fabricated():
    assert experiment_explorer(None) == ""
    evidence = {
        "baseline_score": 0.8039246522665189,
        "blocks": [{"occluded_score": 0.2209090170579009, "effect": 0.583015635208618}],
    }
    text = experiment_explorer(evidence)
    data = json.loads(text.split('type="application/json">')[1].split("</script>")[0])
    assert data["baseline"] == evidence["baseline_score"]
    assert data["scores"] == [evidence["blocks"][0]["occluded_score"]]
    assert data["effects"] == [evidence["blocks"][0]["effect"]]
    assert "not the final patient score" in text
