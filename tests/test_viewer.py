"""Synthetic native-grid display checks; these are not model accuracy tests."""

import json

import nibabel as nib
import numpy as np
import pytest
from PIL import Image

from mirai_ct.volume import load_volume


def volume(tmp_path, name, values, affine=None, units="mm"):
    affine = np.diag([2.0, 3.0, 4.0, 1.0]) if affine is None else affine
    path = tmp_path / (name + ".nii.gz")
    image = nib.Nifti1Image(values, affine)
    image.header.set_xyzt_units(units)
    nib.save(image, path)
    return load_volume(path)


def test_uniform_candidate_focus_uses_largest_cross_section(tmp_path):
    from mirai_ct.panorama import prediction_focus

    values = np.zeros((10, 11, 6), np.float32)
    values[1, 2, 1] = 0.9  # first maximum is a tiny edge slice
    values[3:7, 4:9, 3] = 0.9
    prediction = volume(tmp_path, "prediction", values)
    assert prediction_focus(prediction) == [4, 6, 3]


def test_display_summary_empty_ties_and_invalid_values(tmp_path):
    from mirai_ct.viewer import candidate_summary

    values = np.zeros((10, 11, 6), np.float32)
    v = volume(tmp_path, "empty", values)
    info = candidate_summary(v)
    assert info["focus_ijk"] == [5, 5, 3]
    assert info["positive_voxels"] == 0
    assert info["bounds_ijk"] is None
    values[1:3, 4:6, 1:3] = 0.6
    info = candidate_summary(volume(tmp_path, "ties", values))
    assert info["focus_ijk"] == [1, 4, 1]
    assert info["positive_voxels"] == 8
    assert info["bounds_ijk"] == [[1, 4, 1], [2, 5, 2]]
    values[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        candidate_summary(volume(tmp_path, "nan", values))


def test_pngs_keep_native_voxels_and_shared_grid(tmp_path):
    from mirai_ct.viewer import export_viewer

    ct = np.full((6, 8, 4), -150, np.int16)
    ct[1, 6, 2] = 250
    labels = np.zeros(ct.shape, np.uint8)
    labels[1, 6, 2] = 2
    values = np.zeros(ct.shape, np.float32)
    values[1, 6, 2] = 0.8
    affine = np.array([[0, -3, 0, 44], [-2, 0, 0, 25], [0, 0, 4, -12], [0, 0, 0, 1]])
    scan = volume(tmp_path, "ct", ct, affine)
    mask = volume(tmp_path, "mask", labels, affine)
    pred = volume(tmp_path, "prediction", values, affine)
    target = tmp_path / "viewer"
    result = export_viewer(scan, pred, mask, target)
    assert result["shape_ijk"] == [6, 8, 4]
    assert result["focus_ijk"] == [1, 6, 2]
    entry = result["slices"][2]
    gray = np.array(Image.open(target / entry["ct"]))
    overlay = np.array(Image.open(target / entry["candidate"]))
    annotation = np.array(Image.open(target / entry["annotation"]))
    assert tuple(gray.shape[:2]) == (8, 6)
    assert list(gray[1, 1, :3]) == [255, 255, 255]  # native j=6 -> PNG y=1
    assert overlay[1, 1, 3] == annotation[1, 1, 3] == 255
    assert np.count_nonzero(overlay[..., 3]) == 1
    assert not scan.in_memory and not pred.in_memory and not mask.in_memory
    assert len(result["slices"]) == 4
    assert (target / "viewer.js").is_file()
    assert json.loads((target / "display.json").read_text())["focus_ijk"] == [1, 6, 2]
    with pytest.raises(ValueError, match="exists"):
        export_viewer(scan, pred, mask, target)


def test_outline_is_only_candidate_boundary():
    from mirai_ct.viewer import candidate_outline

    support = np.zeros((7, 8), bool)
    support[1:6, 2:7] = True
    edge = candidate_outline(support)
    assert edge.sum() == 16
    assert edge[1, 2] and not edge[3, 4]
    assert not edge[0].any()


def test_viewer_without_mask_and_all_zero_map(tmp_path):
    from mirai_ct.viewer import export_viewer

    values = np.zeros((4, 5, 3), np.float32)
    scan = volume(tmp_path, "ct", values)
    pred = volume(tmp_path, "prediction", values)
    info = export_viewer(scan, pred, None, tmp_path / "viewer")
    assert info["focus_ijk"] == [2, 2, 1]
    assert info["bounds_ijk"] is None
    assert all(x["annotation"] is None for x in info["slices"])
    assert info["annotation_labels"] == []


def test_viewer_rejects_mismatched_geometry_and_resource_budget(tmp_path, monkeypatch):
    from mirai_ct.viewer import export_viewer

    scan = volume(tmp_path, "ct", np.zeros((4, 5, 3), np.float32))
    pred = volume(tmp_path, "prediction", np.zeros((4, 5, 3), np.float32))
    pred.affine[0, 3] += 1
    with pytest.raises(ValueError, match="geometry"):
        export_viewer(scan, pred, None, tmp_path / "mismatch")
    pred.affine[0, 3] -= 1
    monkeypatch.setattr("mirai_ct.viewer.available_bytes", lambda: 1)
    with pytest.raises(MemoryError, match="viewer"):
        export_viewer(scan, pred, None, tmp_path / "too-large")
    assert not (tmp_path / "too-large").exists()


def test_zoom_padding_respects_spatial_units(tmp_path):
    from mirai_ct.viewer import export_viewer

    values = np.zeros((4, 5, 3), np.float32)
    affine = np.diag([0.002, 0.003, 0.004, 1.0])
    scan = volume(tmp_path, "ct", values, affine, "meter")
    pred = volume(tmp_path, "prediction", values, affine, "meter")
    info = export_viewer(scan, pred, None, tmp_path / "viewer")
    assert info["zoom_padding_ij"] == [8, 5]
