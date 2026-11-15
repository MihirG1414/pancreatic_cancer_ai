"""Offline entry point from synthetic validated imports; never model inference."""

import json
import zipfile

import pytest


def test_delivery_contains_reports_and_assets_without_source_volumes(tmp_path):
    pytest.importorskip("SimpleITK")
    from test_panorama import extended_bundle

    from mirai_ct.delivery import build_delivery
    from mirai_ct.panorama import import_predictions

    case, export, bundle, _ = extended_bundle(tmp_path)
    import_predictions(case, export, bundle, tmp_path / "imported")
    (tmp_path / "cases.csv").write_text(
        "case_id,scan_path,label_path,dataset_source\n"
        f"{case.case_id},{case.scan_path.name},,synthetic software fixture\n"
    )
    spec = tmp_path / "delivery.json"
    spec.write_text(
        json.dumps(
            {
                "cases": [
                    {"manifest": "cases.csv", "case_id": case.case_id, "predictions": "imported"}
                ]
            }
        )
    )
    report = build_delivery(spec, tmp_path / "delivery")
    info = json.loads((report.parent.parent / "delivery.json").read_text())
    assert info["status"] == "success" and info["case_count"] == 1
    assert info["explanation_cases"] == info["anatomy_cases"] == 0
    assert (report.parent / "case-1/index.html").is_file()
    with zipfile.ZipFile(report.parent.parent / "panorama-research-demo.zip") as z:
        assert z.testzip() is None and "index.html" in z.namelist()
        assert "case-1/viewer/slices/0-ct.png" in z.namelist()
        assert not any(n.endswith((".nii.gz", ".mha", ".pth", ".dcm")) for n in z.namelist())
    with pytest.raises(ValueError, match="exists"):
        build_delivery(spec, tmp_path / "delivery")


def test_delivery_refuses_duplicate_case_ids_before_building(tmp_path):
    from mirai_ct.delivery import build_delivery

    spec = tmp_path / "spec.json"
    row = {"manifest": "missing.csv", "case_id": "same", "predictions": "missing"}
    spec.write_text(json.dumps({"cases": [row, row]}))
    with pytest.raises(ValueError, match="Duplicate"):
        build_delivery(spec, tmp_path / "refused")
    assert not (tmp_path / "refused").exists()


def test_review_delivery_rejects_older_candidate_only_products(tmp_path):
    pytest.importorskip("SimpleITK")
    from test_panorama import bundle_fixture

    from mirai_ct.delivery import build_delivery
    from mirai_ct.panorama import import_predictions

    case, export, bundle, _ = bundle_fixture(tmp_path)
    import_predictions(case, export, bundle, tmp_path / "imported")
    (tmp_path / "cases.csv").write_text(
        "case_id,scan_path,label_path,dataset_source\n"
        f"{case.case_id},{case.scan_path.name},,synthetic software fixture\n"
    )
    spec = tmp_path / "delivery.json"
    spec.write_text(
        json.dumps(
            {
                "cases": [
                    {"manifest": "cases.csv", "case_id": case.case_id, "predictions": "imported"}
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="actual model mask"):
        build_delivery(spec, tmp_path / "delivery")
    assert not (tmp_path / "delivery/panorama-research-demo.zip").exists()


def test_delivery_detects_evaluation_reference_label_mismatch(tmp_path):
    pytest.importorskip("SimpleITK")
    import nibabel as nib
    import numpy as np
    from test_panorama import extended_bundle

    from mirai_ct.delivery import build_delivery
    from mirai_ct.panorama import import_predictions

    case, export, bundle, scores = extended_bundle(tmp_path)
    import_predictions(case, export, bundle, tmp_path / "imported")
    ref = nib.Nifti1Image((scores > 0).astype(np.uint8) * 2, nib.load(case.scan_path).affine)
    ref.header.set_xyzt_units("mm")
    nib.save(ref, tmp_path / "reference.nii.gz")
    (tmp_path / "cases.csv").write_text(
        "case_id,scan_path,label_path,dataset_source\n"
        f"{case.case_id},{case.scan_path.name},reference.nii.gz,synthetic fixture\n"
    )
    row = {
        "manifest": "cases.csv",
        "case_id": case.case_id,
        "predictions": "imported",
        "reference_label": 2,
        "reference_description": "synthetic label 2",
    }
    wrong = {
        **row,
        "reference_label": 1,
        "reference_description": "different synthetic target",
        "patient_key": "fixture",
        "overlap_status": "unknown",
        "overlap_evidence": "fixture only",
    }
    (tmp_path / "lesions.json").write_text(json.dumps({"min_iou": 0.1, "cases": [wrong]}))
    spec = tmp_path / "delivery.json"
    spec.write_text(json.dumps({"cases": [row], "lesion_spec": "lesions.json"}))
    with pytest.raises(ValueError, match="differs"):
        build_delivery(spec, tmp_path / "delivery")
