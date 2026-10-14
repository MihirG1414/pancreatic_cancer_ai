"""Synthetic physical-space conversion tests; no model outputs."""

import itertools
import json

import nibabel as nib
import numpy as np
import pytest

sitk = pytest.importorskip("SimpleITK")


def make_scan(tmp_path, units="mm", shear=False):
    angle = 0.37
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, -1]]
    )
    affine = np.eye(4)
    affine[:3, :3] = rotation @ np.diag([0.8, 1.7, 3.2])
    affine[:3, 3] = [31, -72, 18]
    if shear:
        affine[0, 1] += 0.4
    data = np.arange(7 * 9 * 5, dtype=np.int16).reshape(7, 9, 5) - 180
    image = nib.Nifti1Image(data, affine)
    image.header.set_xyzt_units(units)
    image.header.set_slope_inter(2.5, -11)
    path = tmp_path / "ct.nii.gz"
    nib.save(image, path)
    return path, data, affine


def test_export_oblique_reflection_scaling_and_corners(tmp_path):
    from mirai_ct.cases import Case
    from mirai_ct.panorama_io import export_case, sha256_file

    path, data, affine = make_scan(tmp_path)
    original_hash = sha256_file(path)
    # A deliberately nonexistent annotation proves export never reads it.
    case = Case("fixture", path, tmp_path / "DO_NOT_READ.nii.gz", "synthetic")
    output = tmp_path / "export"
    export_case(case, output)
    image = sitk.ReadImage(str(output / "ct.mha"))
    assert image.GetSize() == data.shape
    np.testing.assert_allclose(sitk.GetArrayFromImage(image), (data * 2.5 - 11).transpose(2, 1, 0))
    lps = np.diag([-1, -1, 1, 1]) @ affine
    for ijk in itertools.product(*[(0, size - 1) for size in data.shape]):
        np.testing.assert_allclose(
            image.TransformIndexToPhysicalPoint(ijk), (lps @ [*ijk, 1])[:3], atol=1e-5
        )
    for ijk in itertools.product(*[(-0.5, size - 0.5) for size in data.shape]):
        np.testing.assert_allclose(
            image.TransformContinuousIndexToPhysicalPoint(ijk), (lps @ [*ijk, 1])[:3], atol=1e-5
        )
    record = json.loads((output / "input-provenance.json").read_text())
    assert record["source_sha256"] == original_hash == sha256_file(path)
    assert record["annotation_used"] is False
    assert record["suitability"]["contrast_phase"] == "unknown"
    assert record["verification"]["max_intensity_error"] == 0
    assert record["geometry"]["origin_lps_mm"] == pytest.approx([-31, 72, 18])
    assert json.loads(
        (output / "clinical-information-pancreatic-ct.json").read_text()
    ) == dict.fromkeys(["age", "sex", "study_date", "scanner"])
    assert not any(str(path.parent) in value.read_text() for value in output.glob("*.json"))


@pytest.mark.parametrize("units,factor", [("meter", 1000), ("micron", 0.001)])
def test_spatial_units_convert_to_mm(tmp_path, units, factor):
    from mirai_ct.cases import Case
    from mirai_ct.panorama_io import export_case

    path, _, _ = make_scan(tmp_path, units)
    export_case(Case("fixture", path, None, "synthetic"), tmp_path / "export")
    image = sitk.ReadImage(str(tmp_path / "export/ct.mha"))
    assert image.GetSpacing() == pytest.approx(np.array([0.8, 1.7, 3.2]) * factor)


@pytest.mark.parametrize("problem", ["unknown", "shear", "conflict", "ram", "overwrite"])
def test_export_refuses_unsafe_inputs(tmp_path, monkeypatch, problem):
    from mirai_ct.cases import Case
    from mirai_ct.panorama_io import export_case

    path, _, _ = make_scan(
        tmp_path, "unknown" if problem == "unknown" else "mm", problem == "shear"
    )
    if problem == "conflict":
        image = nib.load(path)
        qform = image.affine.copy()
        qform[0, 3] += 10
        image.set_qform(qform, code=1)
        nib.save(image, path)
    if problem == "ram":
        monkeypatch.setattr("mirai_ct.panorama_io.available_bytes", lambda: 1)
    output = tmp_path / "export"
    if problem == "overwrite":
        output.mkdir()
    with pytest.raises((ValueError, MemoryError)):
        export_case(Case("fixture", path, None, "synthetic"), output)
    assert not (output / "input-provenance.json").exists()
