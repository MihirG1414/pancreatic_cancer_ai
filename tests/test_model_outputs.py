"""Synthetic cropped model products; no actual GPU execution is performed."""

import numpy as np
import pytest

sitk = pytest.importorskip("SimpleITK")


def crop_fixture():
    reference = sitk.Image([9, 10, 7], sitk.sitkFloat32)
    reference.SetSpacing([1.2, 2.3, 3.4])
    reference.SetOrigin([35, -41, 12])
    reference.SetDirection([0, -1, 0, -1, 0, 0, 0, 0, -1])
    coords = dict(x_start=2, x_finish=7, y_start=3, y_finish=9, z_start=1, z_finish=5)
    labels = sitk.RegionOfInterest(sitk.Cast(reference, sitk.sitkUInt8), [5, 6, 4], [2, 3, 1])
    labels[1, 2, 1] = 1
    labels[2, 2, 1] = 4
    probability = np.zeros((4, 6, 5), np.float32)
    probability[1, 2, 1] = 0.73
    return reference, coords, labels, probability


def test_model_products_preserve_crop_indices_and_world_geometry(tmp_path):
    from mirai_ct.panorama_outputs import MODEL_FILES, export_model_outputs

    reference, coords, labels, probability = crop_fixture()
    hashes = export_model_outputs(reference, coords, labels, probability, tmp_path)
    assert set(hashes) == set(MODEL_FILES.values())
    mask = sitk.ReadImage(str(tmp_path / MODEL_FILES["segmentation"]))
    raw = sitk.ReadImage(str(tmp_path / MODEL_FILES["probability"]))
    assert mask.GetSize() == raw.GetSize() == reference.GetSize()
    assert mask.GetOrigin() == raw.GetOrigin() == reference.GetOrigin()
    assert mask.GetDirection() == raw.GetDirection() == reference.GetDirection()
    assert mask[3, 5, 2] == 1 and mask[4, 5, 2] == 0
    assert raw[3, 5, 2] == pytest.approx(0.73)
    assert raw[0, 0, 0] == 0
    assert sitk.GetArrayViewFromImage(mask).sum() == 1


@pytest.mark.parametrize("failure", ["origin", "shape", "nan", "range", "label", "crop"])
def test_invalid_model_products_fail_before_writing(tmp_path, failure):
    from mirai_ct.panorama_outputs import export_model_outputs

    reference, coords, labels, probability = crop_fixture()
    if failure == "origin":
        labels.SetOrigin([0, 0, 0])
    elif failure == "shape":
        probability = probability[:, :, 1:]
    elif failure == "nan":
        probability[0, 0, 0] = np.nan
    elif failure == "range":
        probability[0, 0, 0] = 1.1
    elif failure == "label":
        labels[0, 0, 0] = 9
    elif failure == "crop":
        coords["x_finish"] = 99
    with pytest.raises(ValueError):
        export_model_outputs(reference, coords, labels, probability, tmp_path)
    assert not list(tmp_path.rglob("*.mha"))


def test_candidate_regions_have_checked_ras_lps_and_support_extent(tmp_path):
    import nibabel as nib

    from mirai_ct.findings import candidate_regions
    from mirai_ct.volume import load_volume

    values = np.zeros((7, 8, 5), np.float32)
    values[1:3, 2:4, 1:3] = 0.8
    values[6, 7, 4] = 0.4
    affine = np.array([[0, -3, 0, 20], [2, 0, 0, -30], [0, 0, -4, 50], [0, 0, 0, 1]])
    image = nib.Nifti1Image(values, affine)
    image.header.set_xyzt_units("mm")
    path = tmp_path / "synthetic.nii.gz"
    nib.save(image, path)
    v = load_volume(path)
    findings = candidate_regions(v)
    assert len(findings) == 2
    first = findings[0]
    assert first["voxel_count"] == 8
    assert first["bounds_ijk_inclusive"] == [[1, 2, 1], [2, 3, 2]]
    assert first["extent_mm_native_axes"] == pytest.approx([4, 6, 8])
    assert first["support_volume_ml"] == pytest.approx(0.192)
    assert first["centroid_ras_mm"] == pytest.approx([12.5, -27, 44])
    assert first["centroid_lps_mm"] == pytest.approx([-12.5, 27, 44])
    assert first["anatomical_subregion"] == "unassigned"
    assert not v.in_memory


def test_runner_cli_forwards_optional_output_request(tmp_path, monkeypatch):
    from mirai_ct import panorama_runtime as runtime

    called = {}

    def fake_run(*args, **kwargs):
        called.update(kwargs)
        return tmp_path / "synthetic-output.zip"

    monkeypatch.setattr(runtime, "run_pilot", fake_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "panorama_runtime",
            "run",
            "--root",
            str(tmp_path),
            "--input",
            str(tmp_path / "input"),
            "--baseline",
            str(tmp_path / "baseline"),
            "--run-dir",
            str(tmp_path / "run"),
            "--include-model-outputs",
        ],
    )
    assert runtime.main() == 0
    assert called["include_model_outputs"] is True
