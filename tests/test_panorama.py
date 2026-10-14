"""Synthetic bundles test import contracts; they are never real model runs."""

import json

import nibabel as nib
import numpy as np
import pytest

from mirai_ct.cases import Case
from mirai_ct.volume import load_volume, read_slice

sitk = pytest.importorskip("SimpleITK")


def bundle_fixture(tmp_path, zero=False):
    from mirai_ct.panorama_io import export_case, sha256_file, write_json
    from mirai_ct.panorama_runtime import BASELINE_REV, NNUNET_REV

    affine = np.array([[0, -1.2, 0, 23], [2.3, 0, 0, -47], [0, 0, -3.1, 62], [0, 0, 0, 1]])
    array = np.arange(8 * 9 * 5, dtype=np.int16).reshape(8, 9, 5)
    ct_path = tmp_path / "ct.nii.gz"
    image = nib.Nifti1Image(array, affine)
    image.header.set_xyzt_units("mm")
    image.header.set_slope_inter(2.5, -100)
    nib.save(image, ct_path)
    case = Case("synthetic", ct_path, None, "synthetic software fixture")
    exported = tmp_path / "input"
    export_case(case, exported)
    bundle = tmp_path / "bundle"
    map_path = bundle / "images/pdac-detection-map/detection_map.mha"
    map_path.parent.mkdir(parents=True)
    scores = np.zeros(array.shape, dtype=np.float32)
    if not zero:
        scores[2:5, 3:7, 1:4] = 0.73
    mha = sitk.GetImageFromArray(scores.transpose(2, 1, 0))
    mha.CopyInformation(sitk.ReadImage(str(exported / "ct.mha")))
    sitk.WriteImage(mha, str(map_path))
    score_path = bundle / "pdac-likelihood.json"
    write_json(score_path, float(scores.max()))
    (bundle / "input-provenance.json").write_bytes(
        (exported / "input-provenance.json").read_bytes()
    )
    info = json.loads((exported / "input-provenance.json").read_text())
    # Declared run fields mimic the real bundle schema only inside pytest temp dirs.
    run = {
        "schema_version": 1,
        "status": "success",
        "execution_kind": "pretrained-inference",
        "baseline_revision": BASELINE_REV,
        "nnunet_revision": NNUNET_REV,
        "folds": [0, 1, 2, 3, 4],
        "runtime_seconds": 1.2,
        "versions": {"fixture": "synthetic"},
        "input_mha_sha256": info["mha_sha256"],
        "source_sha256": info["source_sha256"],
        "output_sha256": {
            name: sha256_file(bundle / name)
            for name in (
                "images/pdac-detection-map/detection_map.mha",
                "pdac-likelihood.json",
                "input-provenance.json",
            )
        },
    }
    write_json(bundle / "run.json", run)
    return case, exported, bundle, scores


@pytest.mark.parametrize("zero", [False, True])
def test_import_restores_native_voxel_order_and_preserves_ct(tmp_path, zero):
    from mirai_ct.panorama import import_predictions, load_predictions
    from mirai_ct.panorama_io import sha256_file

    case, exported, bundle, values = bundle_fixture(tmp_path, zero)
    before = sha256_file(case.scan_path)
    output = tmp_path / "imported"
    import_predictions(case, exported, bundle, output)
    prediction, info = load_predictions(case, output)
    for axis in range(3):
        np.testing.assert_allclose(read_slice(prediction, axis, 2), np.take(values, 2, axis=axis))
    np.testing.assert_allclose(prediction.affine, load_volume(case.scan_path).affine)
    assert info["score"] == pytest.approx(float(values.max()))
    assert before == sha256_file(case.scan_path)
    assert not prediction.in_memory
    with pytest.raises(ValueError, match="exists"):
        import_predictions(case, exported, bundle, output)


@pytest.mark.parametrize(
    "raw", ["true", "null", '"0.5"', "{}", "[0.2]", "NaN", "Infinity", "-0.1", "1.1"]
)
def test_score_parser_rejects_wrong_type_and_range(tmp_path, raw):
    from mirai_ct.panorama import parse_score

    path = tmp_path / "score.json"
    path.write_text(raw)
    with pytest.raises(ValueError, match="score"):
        parse_score(path)


@pytest.mark.parametrize("raw", ["0", "1", "0.125"])
def test_score_parser_accepts_official_scalar_json(tmp_path, raw):
    from mirai_ct.panorama import parse_score

    path = tmp_path / "score.json"
    path.write_text(raw)
    assert parse_score(path) == float(raw)


@pytest.mark.parametrize(
    "failure",
    [
        "shift",
        "reflection",
        "size",
        "map_nan",
        "map_range",
        "score_max",
        "tamper",
        "input_tamper",
        "wrong_ct",
        "failed_run",
        "folds",
        "missing_map",
    ],
)
def test_import_rejects_unexplained_output_and_provenance(tmp_path, failure):
    from mirai_ct.panorama import import_predictions
    from mirai_ct.panorama_io import sha256_file, write_json

    case, exported, bundle, _ = bundle_fixture(tmp_path)
    path = bundle / "images/pdac-detection-map/detection_map.mha"
    run_path = bundle / "run.json"
    run = json.loads(run_path.read_text())
    if failure in ("shift", "reflection", "size", "map_nan", "map_range"):
        image = sitk.ReadImage(str(path))
        if failure == "shift":
            image.SetOrigin([x + 5 for x in image.GetOrigin()])
        elif failure == "reflection":
            direction = list(image.GetDirection())
            direction[1] *= -1
            image.SetDirection(direction)
        elif failure == "size":
            image = image[1:, :, :]
        else:
            image[2, 3, 1] = float("nan") if failure == "map_nan" else 1.2
        sitk.WriteImage(image, str(path))
        run["output_sha256"]["images/pdac-detection-map/detection_map.mha"] = sha256_file(path)
    elif failure == "score_max":
        write_json(bundle / "pdac-likelihood.json", 0.4)
        run["output_sha256"]["pdac-likelihood.json"] = sha256_file(bundle / "pdac-likelihood.json")
    elif failure == "tamper":
        (bundle / "pdac-likelihood.json").write_text("0.2")
    elif failure == "input_tamper":
        with (exported / "ct.mha").open("ab") as stream:
            stream.write(b"tamper")
    elif failure == "wrong_ct":
        with case.scan_path.open("ab") as stream:
            stream.write(b"different CT hash")
    elif failure == "failed_run":
        run["status"] = "failed"
    elif failure == "folds":
        run["folds"] = [0]
    elif failure == "missing_map":
        path.unlink()
    write_json(run_path, run)
    with pytest.raises((ValueError, OSError)):
        import_predictions(case, exported, bundle, tmp_path / "imported")
    assert not (tmp_path / "imported/import.json").exists()


def test_prediction_report_and_import_tampering(tmp_path):
    from mirai_ct.panorama import import_predictions, load_predictions
    from mirai_ct.report import generate_report

    case, exported, bundle, _ = bundle_fixture(tmp_path)
    output = tmp_path / "imported"
    import_predictions(case, exported, bundle, output)
    report = generate_report(case, tmp_path / "report", predictions=output)
    text = report.read_text(encoding="utf-8")
    assert "PANORAMA candidate detection map" in text
    assert "uncalibrated model score" in text
    assert "1.2" in text
    assert "Predictions unavailable" not in text
    with (output / "detection.nii.gz").open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="checksum"):
        load_predictions(case, output)


def test_imported_score_metadata_cannot_diverge_from_baseline_json(tmp_path):
    from mirai_ct.panorama import import_predictions, load_predictions
    from mirai_ct.panorama_io import write_json

    case, exported, bundle, _ = bundle_fixture(tmp_path)
    output = tmp_path / "imported"
    import_predictions(case, exported, bundle, output)
    info = json.loads((output / "import.json").read_text())
    info["score"] = 0.22
    write_json(output / "import.json", info)
    with pytest.raises(ValueError, match="score"):
        load_predictions(case, output)


def test_import_cli_fails_clearly_on_missing_bundle(tmp_path, monkeypatch):
    from mirai_ct.panorama import main

    case, exported, _, _ = bundle_fixture(tmp_path)
    manifest = tmp_path / "cases.csv"
    manifest.write_text(
        "case_id,scan_path,label_path,dataset_source\nsynthetic,ct.nii.gz,,synthetic\n"
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "panorama",
            "--manifest",
            str(manifest),
            "--case-id",
            case.case_id,
            "--input-export",
            str(exported),
            "--bundle",
            str(tmp_path / "missing"),
            "--output",
            str(tmp_path / "imported"),
        ],
    )
    assert main() == 1
    assert not (tmp_path / "imported").exists()
