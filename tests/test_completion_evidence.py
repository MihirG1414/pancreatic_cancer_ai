"""Synthetic evidence contracts; no medical inference or anatomical truth."""

import json

import nibabel as nib
import numpy as np
import pytest


def image(values):
    result = nib.Nifti1Image(np.asarray(values, dtype=np.uint8), np.diag([-2, 3, -4, 1]))
    result.header.set_xyzt_units("mm")
    return result


def test_anatomy_reports_mixed_and_uncovered_voxels():
    from mirai_ct.anatomy import measure_subregions

    lesion = np.zeros((5, 4, 3), np.uint8)
    lesion[1:4, 1, 1] = 1
    parts = np.zeros_like(lesion)
    parts[1, 1, 1] = 1
    parts[2, 1, 1] = 3
    result = measure_subregions(image(lesion), image(parts))
    assert result["assignment"] == "mixed: head, tail"
    assert result["outside_voxels"] == 1
    assert result["overlap_voxels"] == {"head": 1, "body": 0, "tail": 1}
    assert result["covered_fraction"] == pytest.approx(2 / 3)
    assert (
        measure_subregions(image(lesion), image(np.zeros_like(parts)))["assignment"] == "unassigned"
    )
    assert (
        measure_subregions(image(np.zeros_like(lesion)), image(parts))["assignment"]
        == "no predicted mask"
    )


@pytest.mark.parametrize("failure", ["labels", "geometry"])
def test_anatomy_refuses_invalid_masks(failure):
    from mirai_ct.anatomy import measure_subregions

    values = np.ones((3, 3, 3), np.uint8)
    parts = image(values * (4 if failure == "labels" else 1))
    if failure == "geometry":
        parts.affine[0, 3] += 10
    with pytest.raises(ValueError):
        measure_subregions(image(values), parts)


def test_occlusion_uses_fixed_target_and_signed_effects(tmp_path):
    from mirai_ct.occlusion import calculate_effects, partition_bounds

    blocks = partition_bounds([0, 0, 0], [4, 4, 4])
    assert len(blocks) == 8
    x = np.arange(64, dtype=np.float32).reshape(4, 4, 4) / 64
    target = np.zeros_like(x, dtype=bool)
    target[1:3, 1:3, 1:3] = True
    calls = []

    def predict(data):
        calls.append(data.copy())
        return np.full(data.shape, float(data.mean()), dtype=np.float32)

    saved = predict(x)
    calls.clear()
    journal = tmp_path / "explanation.json"
    result = calculate_effects(x, target, saved, blocks, predict, fill_value=0.5, journal=journal)
    assert len(calls) == 9
    assert np.array_equal(x, np.arange(64, dtype=np.float32).reshape(4, 4, 4) / 64)
    for block, effect in zip(blocks, result["blocks"], strict=True):
        a, b = block
        expected = x.copy()
        expected[a[2] : b[2], a[1] : b[1], a[0] : b[0]] = 0.5
        assert effect["occluded_score"] == pytest.approx(expected.mean())
        assert effect["effect"] == pytest.approx(x.mean() - expected.mean())
    assert any(b["effect"] < 0 for b in result["blocks"])
    assert any(b["effect"] > 0 for b in result["blocks"])
    assert result["status"] == "success"
    resumed = calculate_effects(x, target, saved, blocks, predict, fill_value=0.5, journal=journal)
    assert resumed == result and len(calls) == 9
    with pytest.raises(ValueError, match="identity"):
        calculate_effects(x, target, saved, blocks, predict, fill_value=0.1, journal=journal)


def test_occlusion_refuses_nonreproducing_model_and_resumes_completed_passes(tmp_path):
    from mirai_ct.occlusion import calculate_effects, partition_bounds

    x = np.ones((4, 4, 4), np.float32)
    blocks = partition_bounds([0, 0, 0], [4, 4, 4])
    with pytest.raises(ValueError, match="reproduc"):
        calculate_effects(x, x > 0, x * 0.8, blocks, lambda a: a, journal=tmp_path / "bad.json")
    calls = 0

    def interrupted(a):
        nonlocal calls
        calls += 1
        if calls == 4:
            raise RuntimeError("simulated disconnection")
        return a

    journal = tmp_path / "resume.json"
    with pytest.raises(RuntimeError, match="disconnection"):
        calculate_effects(x, x > 0, x, blocks, interrupted, journal=journal, fill_value=0.5)
    assert len(json.loads(journal.read_text())["blocks"]) == 2
    calls = 0
    result = calculate_effects(x, x > 0, x, blocks, lambda a: a, journal=journal, fill_value=0.5)
    assert result["status"] == "success" and len(result["blocks"]) == 8


def test_froc_matching_is_one_to_one_and_ties_are_simultaneous():
    from mirai_ct.lesion_evaluation import froc_curve

    records = [
        {
            "reference_count": 2,
            "candidates": [
                {"score": 0.8, "matches": [0, 1]},
                {"score": 0.8, "matches": [0]},
                {"score": 0.3, "matches": [1]},
            ],
        },
        {"reference_count": 0, "candidates": [{"score": 0.5, "matches": []}]},
    ]
    curve = froc_curve(records)
    assert curve[0]["threshold"] is None and curve[0]["sensitivity"] == 0
    assert [r["threshold"] for r in curve[1:]] == [0.8, 0.5, 0.3]
    assert curve[1]["matched_lesions"] == 2  # Augmenting path beats greedy assignment.
    assert curve[1]["false_positives_per_scan"] == 0
    assert curve[2]["false_positives_per_scan"] == 0.5
    assert curve[3]["false_positives_per_scan"] == 1


def test_froc_empty_reference_is_undefined_and_bad_matches_rejected():
    from mirai_ct.lesion_evaluation import froc_curve

    assert froc_curve([{"reference_count": 0, "candidates": []}])[0]["sensitivity"] is None
    with pytest.raises(ValueError):
        froc_curve([{"reference_count": 1, "candidates": [{"score": 0.7, "matches": [1]}]}])


@pytest.mark.parametrize("suffix", [".nii", ".nii.gz"])
def test_sequential_planes_keep_scaling_geometry_and_independent_buffers(tmp_path, suffix):
    from mirai_ct.volume import iter_slices, load_volume, read_slice

    values = np.arange(8 * 9 * 7, dtype=np.int16).reshape(8, 9, 7)
    original = nib.Nifti1Image(values, np.diag([-1, 2, -3, 1]))
    original.header.set_slope_inter(2.5, -700)
    path = tmp_path / ("ct" + suffix)
    nib.save(original, path)
    volume = load_volume(path)
    planes = list(iter_slices(volume))
    for k, plane in enumerate(planes):
        np.testing.assert_array_equal(plane, values[:, :, k] * 2.5 - 700)
        np.testing.assert_array_equal(plane, read_slice(volume, 2, k))
    assert not volume.in_memory
    planes[0][:] = 99
    assert not np.all(planes[1] == 99)


def test_real_io_component_matching_uses_reference_labels_and_duplicate_detections(tmp_path):
    pytest.importorskip("SimpleITK")
    from mirai_ct.lesion_evaluation import component_matches, froc_curve

    ref = np.zeros((12, 10, 5), np.uint8)
    ref[1:4, 1:4, 1:4] = 2
    ref[8:11, 6:9, 1:4] = 2
    ref[6, 1, 0] = 1  # Another reference label must be ignored.
    pred = np.zeros_like(ref, dtype=np.float32)
    pred[1:4, 1:4, 1:4] = 0.9
    pred[8, 6, 1] = 0.7
    pred[10, 8, 3] = 0.6
    pred[0, 8, 0] = 0.2  # False positive.
    reference, prediction = tmp_path / "ref.nii.gz", tmp_path / "pred.nii.gz"
    nib.save(image(ref), reference)
    model = nib.Nifti1Image(pred, image(ref).affine)
    model.header.set_xyzt_units("mm")
    nib.save(model, prediction)
    result = component_matches(reference, prediction, label=2, min_iou=0.01)
    assert result["reference_count"] == 2 and len(result["candidates"]) == 4
    assert sorted(result["reference_component_voxels"]) == [27, 27]
    curve = froc_curve([result])
    assert curve[-1]["matched_lesions"] == 2 and curve[-1]["false_positives"] == 2


def evidence_fixture(tmp_path):
    from test_panorama import extended_bundle

    from mirai_ct.occlusion import calculate_effects, partition_bounds
    from mirai_ct.panorama import import_predictions, load_predictions
    from mirai_ct.panorama_io import sha256_file, write_json

    case, exported, bundle, scores = extended_bundle(tmp_path)
    run_path = bundle / "run.json"
    run = json.loads(run_path.read_text())
    coords = {
        f"{a}_{boundary}": value
        for a, size in zip("xyz", scores.shape, strict=True)
        for boundary, value in [("start", 0), ("finish", size)]
    }
    run.update(model_sha256={"fixture": "synthetic"}, crop_coordinates_ijk_exclusive_finish=coords)
    write_json(run_path, run)
    imported = import_predictions(case, exported, bundle, tmp_path / "imported")
    _, info = load_predictions(case, imported)
    native = np.ascontiguousarray(scores.transpose(2, 1, 0))
    identity = {
        k: run[k]
        for k in ("baseline_revision", "nnunet_revision", "model_sha256", "folds", "versions")
    }
    identity.update(
        run_sha256=sha256_file(run_path),
        source_sha256=info["source_sha256"],
        crop_start_ijk=[0, 0, 0],
        target_voxel_count=int(np.count_nonzero(scores)),
    )
    journal = tmp_path / "explanation.json"
    calculate_effects(
        np.zeros_like(native),
        native > 0,
        native,
        partition_bounds([0, 0, 0], list(scores.shape)),
        lambda x: native * (1 - 0.001 * float(x.mean())),
        journal=journal,
        identity=identity,
    )
    parts = nib.Nifti1Image((scores > 0).astype(np.uint8) * 3, nib.load(case.scan_path).affine)
    parts.header.set_xyzt_units("mm")
    mask = tmp_path / "parts.nii.gz"
    nib.save(parts, mask)
    provenance = tmp_path / "parts.json"
    write_json(
        provenance,
        {
            "schema_version": 1,
            "source_ct_sha256": info["source_sha256"],
            "mask_sha256": sha256_file(mask),
            "labels": {"1": "head", "2": "body", "3": "tail"},
            "source_type": "external-model",
            "method": "synthetic software fixture <script>",
            "review_status": "unreviewed",
        },
    )
    return case, imported, journal, mask, provenance


def test_report_keeps_signed_explanation_and_external_anatomy_distinct(tmp_path):
    from mirai_ct.report import generate_report

    case, imported, journal, mask, provenance = evidence_fixture(tmp_path)
    page = generate_report(
        case,
        tmp_path / "report",
        imported,
        explanation=journal,
        anatomy_mask=mask,
        anatomy_provenance=provenance,
    )
    data = json.loads((page.parent / "report.json").read_text())
    assert data["attribution_available"] is True
    assert data["anatomical_subregion"] == "tail"
    assert data["anatomy_result"]["provenance"]["review_status"] == "unreviewed"
    assert len(list(page.parent.glob("explanation-axis-*.png"))) == 3
    text = page.read_text(encoding="utf-8")
    assert "Signed block occlusion" in text and "not probability" in text
    assert "synthetic software fixture <script>" not in text
    assert "Head/body/tail and decision attribution remain unavailable" not in text


@pytest.mark.parametrize("failure", ["identity", "incomplete", "effect", "target"])
def test_explanation_tampering_is_rejected_before_report_write(tmp_path, failure):
    from mirai_ct.report import generate_report

    case, imported, journal, _, _ = evidence_fixture(tmp_path)
    data = json.loads(journal.read_text())
    if failure == "identity":
        data["spec"]["identity"]["source_sha256"] = "wrong"
    elif failure == "incomplete":
        data["blocks"].pop()
    elif failure == "effect":
        data["blocks"][0]["effect"] = float("nan")
    else:
        data["spec"]["target_sha256"] = "wrong"
    if failure in ("identity", "target"):
        import hashlib

        data["fingerprint"] = hashlib.sha256(
            json.dumps(data["spec"], sort_keys=True, allow_nan=False).encode()
        ).hexdigest()
    journal.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        generate_report(case, tmp_path / "refused", imported, explanation=journal)
    assert not (tmp_path / "refused").exists()


def test_gpu_adapter_preserves_saved_axis_order_full_ensemble_and_tta(tmp_path, monkeypatch):
    """Fake network tests API wiring only; never claims real GPU execution."""
    import sys
    from types import ModuleType, SimpleNamespace

    sitk = pytest.importorskip("SimpleITK")
    from test_panorama import extended_bundle

    from mirai_ct import panorama_explain as adapter
    from mirai_ct.panorama_io import sha256_file, write_json

    case, exported, bundle, scores = extended_bundle(tmp_path)
    run = json.loads((bundle / "run.json").read_text())
    run["model_sha256"] = {"synthetic": "test"}
    (bundle / "WEIGHTS-LICENSE.txt").write_text("Synthetic fixture, not a weight license.")
    run["output_sha256"]["WEIGHTS-LICENSE.txt"] = sha256_file(bundle / "WEIGHTS-LICENSE.txt")
    run["weights"] = {"permission_confirmed_by_operator": True}
    run["crop_coordinates_ijk_exclusive_finish"] = {
        f"{a}_{b}": v
        for a, n in zip("xyz", scores.shape, strict=True)
        for b, v in [("start", 0), ("finish", n)]
    }
    write_json(bundle / "run.json", run)
    (tmp_path / "input_fullres").mkdir()
    (tmp_path / "output_fullres").mkdir()
    ct = sitk.ReadImage(str(exported / "ct.mha"))
    sitk.WriteImage(ct, str(tmp_path / "input_fullres/scan_0000.nii.gz"))
    labels = sitk.ReadImage(str(bundle / "images/pdac-segmentation/segmentation.mha"))
    sitk.WriteImage(labels, str(tmp_path / "output_fullres/scan.nii.gz"))
    probabilities = np.zeros((7, *scores.shape[::-1]), np.float32)
    probabilities[1] = scores.transpose(2, 1, 0)
    np.savez_compressed(tmp_path / "output_fullres/scan.npz", probabilities=probabilities)
    calls = []

    class Predictor:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))

        def initialize_from_trained_model_folder(self, path, **kwargs):
            calls.append(("model", kwargs))

        def predict_single_npy_array(self, array, properties, **kwargs):
            assert array.shape == (1, *scores.shape[::-1])
            assert properties["spacing"] == tuple(ct.GetSpacing()[::-1])
            assert kwargs["save_or_return_probabilities"] is True
            calls.append(("predict", None))
            return np.zeros(scores.shape[::-1]), probabilities.copy()

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(adapter, "preflight", lambda _: None)
    monkeypatch.setattr(adapter, "_versions", lambda: run["versions"])
    monkeypatch.setattr(adapter, "validate_models", lambda _: run["model_sha256"])
    monkeypatch.setattr(adapter, "validate_baseline_source", lambda _: None)
    monkeypatch.setattr(adapter, "configure_inference_environment", lambda: None)
    monkeypatch.setattr(adapter, "require_crop_memory", lambda *_: None)
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True), device=lambda x: x),
    )
    package = ModuleType("nnunetv2.inference.predict_from_raw_data")
    package.nnUNetPredictor = Predictor
    monkeypatch.setitem(sys.modules, "nnunetv2", ModuleType("nnunetv2"))
    monkeypatch.setitem(sys.modules, "nnunetv2.inference", ModuleType("nnunetv2.inference"))
    monkeypatch.setitem(sys.modules, "nnunetv2.inference.predict_from_raw_data", package)
    output = tmp_path / "explanation"
    output.mkdir()
    path = adapter._explain_run(tmp_path, tmp_path / "baseline", tmp_path, exported, output)
    data = json.loads(path.read_text())
    assert data["status"] == "success" and data["spec"]["identity"]["target_voxel_count"] == 36
    assert sum(name == "predict" for name, _ in calls) == 9
    assert calls[0][1]["use_mirroring"] is True and calls[0][1]["tile_step_size"] == 0.5
    assert calls[1][1]["use_folds"] == (0, 1, 2, 3, 4)
    assert calls[1][1]["checkpoint_name"] == "checkpoint_best_panorama.pth"
