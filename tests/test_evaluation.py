"""Analytical software fixtures, never clinical model-performance evidence."""

import json

import nibabel as nib
import numpy as np
import pytest

from mirai_ct.cases import Case
from mirai_ct.volume import load_volume


def volume(tmp_path, name, array, affine=None):
    path = tmp_path / name
    image = nib.Nifti1Image(
        np.asarray(array, dtype=np.float32), np.eye(4) if affine is None else affine
    )
    image.header.set_xyzt_units("mm")
    nib.save(image, path)
    return load_volume(path)


def test_overlap_analytical_counts_and_no_volume_cache(tmp_path):
    from mirai_ct.evaluation import overlap_metrics

    ref = np.zeros((3, 4, 2))
    ref[0, :3, 0] = 2
    ref[1, :1, 1] = 2
    pred = np.zeros_like(ref)
    pred[0, :2, 0] = 0.8
    pred[2, :2, 1] = 0.7
    r, p = volume(tmp_path, "ref.nii.gz", ref), volume(tmp_path, "pred.nii.gz", pred)
    got = overlap_metrics(r, p, reference_label=2, binary_prediction=False)
    assert got["reference_voxels"] == 4
    assert got["predicted_voxels"] == 4
    assert got["intersection_voxels"] == 2
    assert got["false_positive_voxels"] == 2
    assert got["false_negative_voxels"] == 2
    assert got["dice"] == 0.5
    assert got["iou"] == pytest.approx(1 / 3)
    assert not r.in_memory and not p.in_memory


@pytest.mark.parametrize(
    "ref_positive,pred_positive", [(False, False), (True, False), (False, True)]
)
def test_empty_overlap_semantics(tmp_path, ref_positive, pred_positive):
    from mirai_ct.evaluation import overlap_metrics

    r, p = np.zeros((2, 2, 2)), np.zeros((2, 2, 2))
    r[0, 0, 0], p[0, 0, 0] = int(ref_positive), int(pred_positive)
    got = overlap_metrics(
        volume(tmp_path, "r.nii.gz", r),
        volume(tmp_path, "p.nii.gz", p),
        reference_label=1,
        binary_prediction=True,
    )
    expected = 0.0 if ref_positive or pred_positive else None
    assert got["dice"] == got["iou"] == expected


@pytest.mark.parametrize("bad", ["shift", "nan", "fractional_reference", "nonbinary", "range"])
def test_overlap_rejects_unsafe_comparison(tmp_path, bad):
    from mirai_ct.evaluation import overlap_metrics

    r, p = np.zeros((2, 2, 2)), np.zeros((2, 2, 2))
    affine = np.eye(4)
    if bad == "shift":
        affine[0, 3] = 10
    elif bad == "nan":
        r[0, 0, 0] = np.nan
    elif bad == "fractional_reference":
        r[0, 0, 0] = 0.5
    elif bad == "nonbinary":
        p[0, 0, 0] = 0.8
    else:
        p[0, 0, 0] = 1.1
    with pytest.raises(ValueError):
        overlap_metrics(
            volume(tmp_path, "r.nii.gz", r),
            volume(tmp_path, "p.nii.gz", p, affine),
            reference_label=1,
            binary_prediction=True,
        )


def test_ranking_ties_and_threshold_confusion_counts():
    from mirai_ct.evaluation import classification_metrics

    # Positive-negative pairs: 1 win, 1 tie, 2 losses -> AUC 0.375.
    got = classification_metrics([1, 0, 1, 0], [0.8, 0.8, 0.2, 0.4], threshold=0.5)
    assert got["roc_auc"] == 0.375
    assert got["true_positive"] == got["false_positive"] == 1
    assert got["true_negative"] == got["false_negative"] == 1
    assert got["sensitivity"] == got["specificity"] == 0.5
    assert got["decision_rule"] == "score >= threshold"


@pytest.mark.parametrize("labels", [[1, 1], [0, 0]])
def test_one_class_has_no_auc(labels):
    from mirai_ct.evaluation import classification_metrics

    got = classification_metrics(labels, [0.3, 0.8], threshold=0.5)
    assert got["roc_auc"] is None
    assert got["specificity" if labels[0] else "sensitivity"] is None


@pytest.mark.parametrize("scores,threshold", [([np.nan], 0.5), ([1.1], 0.5), ([0.3], -1)])
def test_invalid_scores_and_threshold_rejected(scores, threshold):
    from mirai_ct.evaluation import classification_metrics

    with pytest.raises(ValueError):
        classification_metrics([1], scores, threshold=threshold)


def test_real_contract_fixture_never_calls_candidates_segmentation(tmp_path):
    from test_panorama import bundle_fixture

    from mirai_ct.evaluation import evaluate_case
    from mirai_ct.panorama import import_predictions

    case, exported, bundle, values = bundle_fixture(tmp_path)
    annotation = volume(
        tmp_path, "reference.nii.gz", (values > 0) * 2, load_volume(case.scan_path).affine
    )
    case = Case(case.case_id, case.scan_path, tmp_path / "reference.nii.gz", case.dataset_source)
    output = tmp_path / "import"
    import_predictions(case, exported, bundle, output)
    got = evaluate_case(
        case, output, reference_label=2, reference_description="Synthetic tumor reference"
    )
    assert got["candidate_support_overlap"]["dice"] == 1
    assert got["model_segmentation_overlap"] is None
    assert got["pdac_reference"] is None
    assert got["independent_validation"] is False
    assert got["reference_sha256"]
    assert not annotation.in_memory
    with pytest.raises(ValueError, match="description"):
        evaluate_case(case, output, reference_label=2, reference_description="")
    (output / "detection.nii.gz").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        evaluate_case(case, output, reference_label=2, reference_description="Fixture")


def test_cohort_requires_explicit_diagnoses_and_unique_patients(tmp_path, monkeypatch):
    from mirai_ct import evaluation

    def fake_case(case, predictions, **kwargs):
        return {"case_id": case.case_id, "source_sha256": case.case_id, "score": 0.7}

    monkeypatch.setattr(evaluation, "evaluate_case", fake_case)
    (tmp_path / "cases.local.csv").write_text(
        "case_id,scan_path,label_path,dataset_source\na,a.nii.gz,,synthetic\nb,b.nii.gz,,synthetic\n"
    )
    spec = {
        "threshold": 0.5,
        "threshold_source": "Pre-specified synthetic test value; not clinical",
        "cases": [
            {
                "manifest": "cases.local.csv",
                "case_id": c,
                "predictions": c,
                "patient_key": c,
                "pdac_label": i,
                "diagnosis_reference": "Synthetic reference",
                "overlap_status": "unknown",
                "overlap_evidence": "Not audited",
            }
            for i, c in enumerate(("a", "b"))
        ],
    }
    path = tmp_path / "cohort.local.json"
    path.write_text(json.dumps(spec))
    got = evaluation.evaluate_cohort(path)
    assert got["analysis_kind"] == "exploratory; training overlap not excluded"
    assert got["classification"]["roc_auc"] == 0.5
    spec["cases"][1]["patient_key"] = "a"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="patient"):
        evaluation.evaluate_cohort(path)
    spec["cases"][1]["patient_key"] = "b"
    del spec["cases"][1]["pdac_label"]
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="pdac_label"):
        evaluation.evaluate_cohort(path)


def test_actual_model_mask_compared_separately_and_report_is_escaped(tmp_path):
    from test_panorama import extended_bundle

    from mirai_ct.evaluation import evaluate_case, write_evaluation
    from mirai_ct.panorama import import_predictions
    from mirai_ct.report import generate_report

    case, exported, bundle, values = extended_bundle(tmp_path)
    volume(tmp_path, "ref.nii.gz", (values > 0) * 2, load_volume(case.scan_path).affine)
    case = Case(case.case_id, case.scan_path, tmp_path / "ref.nii.gz", case.dataset_source)
    imported = import_predictions(case, exported, bundle, tmp_path / "imported")
    result = evaluate_case(
        case, imported, reference_label=2, reference_description="<script>test</script>"
    )
    assert result["model_segmentation_overlap"]["dice"] == 1
    assert result["model_output_sha256"]["segmentation.nii.gz"]
    page = write_evaluation(result, tmp_path / "evaluation")
    assert "<script>test</script>" not in page.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="exists"):
        write_evaluation(result, tmp_path / "evaluation")
    report = generate_report(
        case,
        tmp_path / "report",
        imported,
        reference_label=2,
        reference_description="Synthetic reference, not clinical evidence",
    )
    assert "Comparison with the supplied annotation" in report.read_text(encoding="utf-8")
    info = json.loads((report.parent / "report.json").read_text())
    assert info["reference_comparison"]["model_segmentation_overlap"]["dice"] == 1


def test_auc_agrees_with_pairwise_definition_for_tied_rankings():
    from mirai_ct.evaluation import classification_metrics

    # Independent pairwise oracle checks ranking implementation on many tied cohorts.
    rng = np.random.default_rng(18)
    for _ in range(40):
        labels = rng.integers(0, 2, size=12).tolist()
        labels[:2] = [0, 1]
        scores = (rng.integers(0, 5, size=12) / 4).tolist()
        pairs = [
            (p, n)
            for p, y in zip(scores, labels, strict=True)
            if y
            for n, z in zip(scores, labels, strict=True)
            if not z
        ]
        expected = sum((p > n) + 0.5 * (p == n) for p, n in pairs) / len(pairs)
        assert classification_metrics(labels, scores, threshold=0.5)["roc_auc"] == expected
