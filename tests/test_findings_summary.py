"""Synthetic mask measurements and explicit report availability states."""

import json

import nibabel as nib
import numpy as np
import pytest

from mirai_ct.volume import load_volume


def test_model_mask_size_native_centroid_and_empty_state(tmp_path):
    from mirai_ct.findings import segmentation_measurements

    values = np.zeros((7, 8, 5), np.uint8)
    values[1:3, 2:4, 1:3] = 1
    affine = np.array([[0, -3, 0, 20], [2, 0, 0, -30], [0, 0, -4, 50], [0, 0, 0, 1]])
    image = nib.Nifti1Image(values, affine)
    image.header.set_xyzt_units("mm")
    nib.save(image, tmp_path / "mask.nii.gz")
    result = segmentation_measurements(load_volume(tmp_path / "mask.nii.gz"))
    assert result["voxel_count"] == 8
    assert result["volume_ml"] == pytest.approx(0.192)
    assert result["extent_mm_native_axes"] == pytest.approx([4, 6, 8])
    assert result["centroid_ras_mm"] == pytest.approx([12.5, -27, 44])
    assert result["bounds_ijk_inclusive"] == [[1, 2, 1], [2, 3, 2]]
    image = nib.Nifti1Image(np.zeros_like(values), affine, header=image.header)
    nib.save(image, tmp_path / "empty.nii.gz")
    empty = segmentation_measurements(load_volume(tmp_path / "empty.nii.gz"))
    assert empty["volume_ml"] == 0
    assert empty["centroid_ras_mm"] is None
    assert empty["extent_mm_native_axes"] is None


@pytest.mark.parametrize("value", [0.5, -1, np.nan])
def test_model_measurements_reject_nonbinary_masks(tmp_path, value):
    from mirai_ct.findings import segmentation_measurements

    image = nib.Nifti1Image(np.full((3, 4, 2), value, dtype=np.float32), np.eye(4))
    image.header.set_xyzt_units("mm")
    nib.save(image, tmp_path / "mask.nii.gz")
    with pytest.raises(ValueError, match="binary|non-finite"):
        segmentation_measurements(load_volume(tmp_path / "mask.nii.gz"))


@pytest.mark.parametrize("extended", [False, True])
def test_report_summary_does_not_invent_missing_products(tmp_path, extended):
    pytest.importorskip("SimpleITK")
    from test_panorama import bundle_fixture, extended_bundle

    from mirai_ct.panorama import import_predictions
    from mirai_ct.report import generate_report

    case, exported, bundle, _ = (extended_bundle if extended else bundle_fixture)(tmp_path)
    imported = import_predictions(case, exported, bundle, tmp_path / "imported")
    report = generate_report(case, tmp_path / "report", imported, measure_candidates=True)
    info = json.loads((report.parent / "report.json").read_text())
    assert info["findings_summary"]["candidate_region_count"] == 1
    assert info["findings_summary"]["clinical_diagnosis"] == "not established"
    assert (info["model_segmentation_measurements"] is not None) is extended
    text = report.read_text(encoding="utf-8")
    assert text.index("Research findings summary") < text.index("CT geometry")
    if extended:
        assert info["model_segmentation_measurements"]["voxel_count"] == 36
        assert "Predicted mask volume" in text
    else:
        assert "Model segmentation is unavailable" in text
