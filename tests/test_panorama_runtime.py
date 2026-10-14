"""GPU orchestration contract tests without weights, CUDA or model inference."""

import hashlib
import zipfile

import numpy as np
import pytest


def test_predict_commands_preserve_all_folds_and_baseline_defaults(tmp_path):
    from mirai_ct.panorama_runtime import STAGES, prediction_command

    for stage in STAGES:
        cmd = prediction_command(stage, tmp_path / "in", tmp_path / "out")
        assert cmd[cmd.index("-f") + 1 : cmd.index("-f") + 6] == ["0", "1", "2", "3", "4"]
        assert cmd[cmd.index("-chk") + 1] == stage["checkpoint"]
        assert cmd[cmd.index("-c") + 1] == "3d_fullres"
        assert cmd[cmd.index("-tr") + 1] == stage["trainer"]
        assert "--save_probabilities" in cmd
        assert "--disable_tta" not in cmd
        assert "-step_size" not in cmd  # saved baseline default 0.5
        assert cmd[cmd.index("-npp") + 1] == "1"


def test_archive_checksum_and_safe_extraction(tmp_path):
    from mirai_ct.panorama_runtime import safe_extract, verify_archive

    archive = tmp_path / "weights.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("Dataset/model/checkpoint.pth", b"synthetic checkpoint bytes")
    md5 = hashlib.md5(archive.read_bytes()).hexdigest()
    verify_archive(archive, md5, archive.stat().st_size)
    with pytest.raises(ValueError, match="checksum"):
        verify_archive(archive, "0" * 32, archive.stat().st_size)
    with pytest.raises(ValueError, match="size"):
        verify_archive(archive, md5, 1)
    safe_extract(archive, tmp_path / "models")
    assert (tmp_path / "models/Dataset/model/checkpoint.pth").is_file()


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/drive", "..\\escape"])
def test_unsafe_zip_members_rejected(tmp_path, name):
    from mirai_ct.panorama_runtime import safe_extract

    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(name, b"bad")
    with pytest.raises(ValueError, match="Unsafe"):
        safe_extract(archive, tmp_path / "out")


def test_model_contract_requires_every_fold_and_metadata(tmp_path):
    from mirai_ct.panorama_runtime import STAGES, validate_models

    with pytest.raises(ValueError, match="Missing"):
        validate_models(tmp_path)
    for stage in STAGES:
        folder = tmp_path / stage["dataset"] / f"{stage['trainer']}__nnUNetPlans__3d_fullres"
        folder.mkdir(parents=True)
        for name in ("plans.json", "dataset.json"):
            (folder / name).write_text("{}")
        for fold in range(5):
            (folder / f"fold_{fold}").mkdir()
            (folder / f"fold_{fold}" / stage["checkpoint"]).write_bytes(b"fixture")
    result = validate_models(tmp_path)
    assert len(result) == 14  # ten checkpoints plus four metadata files
    (folder / "fold_4" / stage["checkpoint"]).unlink()
    with pytest.raises(ValueError, match="Missing"):
        validate_models(tmp_path)


@pytest.mark.parametrize(
    "values", [np.zeros((3, 4, 5)), np.ones((3, 4, 5)), np.array([0, 2]), np.array([0, np.nan])]
)
def test_invalid_predicted_pancreas_is_explicit_failure(values):
    from mirai_ct.panorama_runtime import validate_pancreas

    with pytest.raises(ValueError, match="pancreas"):
        validate_pancreas(values)


def test_valid_predicted_pancreas_and_crop():
    from mirai_ct.panorama_runtime import validate_crop, validate_pancreas

    validate_pancreas(np.array([0, 1]))
    crop = dict(x_start=1, x_finish=5, y_start=2, y_finish=8, z_start=0, z_finish=3)
    validate_crop(crop, (10, 11, 12), (4, 6, 3))
    with pytest.raises(ValueError, match="crop"):
        validate_crop({**crop, "x_finish": 1}, (10, 11, 12), (0, 6, 3))
    with pytest.raises(ValueError, match="crop"):
        validate_crop(crop, (10, 11, 12), (5, 6, 3))


def test_stage_output_geometry_and_preflight_failure(tmp_path, monkeypatch):
    from mirai_ct.panorama_runtime import preflight, validate_stage_grid

    sitk = pytest.importorskip("SimpleITK")
    reference = sitk.Image([5, 6, 7], sitk.sitkFloat32)
    reference.SetSpacing([1.1, 2.2, 3.3])
    reference.SetDirection([0, -1, 0, 1, 0, 0, 0, 0, 1])
    reference.SetOrigin([18, -24, 31])
    validate_stage_grid(reference, reference.GetSize(), reference)
    shifted = sitk.Image(reference)
    shifted.SetOrigin([19, -24, 31])
    with pytest.raises(ValueError, match="Stage output"):
        validate_stage_grid(shifted, reference.GetSize(), reference)
    monkeypatch.setattr(
        "mirai_ct.panorama_runtime.subprocess.run",
        lambda *a, **kw: type("Probe", (), {"stdout": "GPU, 16000, 100, 555"})(),
    )
    with pytest.raises(ValueError, match="resource gate"):
        preflight(tmp_path)


def test_reused_extracted_model_must_match_verified_archive(tmp_path):
    from mirai_ct.panorama_runtime import verify_extracted

    archive = tmp_path / "model.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("Dataset/checkpoint.pth", b"official fixture")
    root = tmp_path / "models"
    (root / "Dataset").mkdir(parents=True)
    checkpoint = root / "Dataset/checkpoint.pth"
    checkpoint.write_bytes(b"official fixture")
    assert (
        verify_extracted(archive, root)["Dataset/checkpoint.pth"]
        == hashlib.sha256(b"official fixture").hexdigest()
    )
    checkpoint.write_bytes(b"changed nonempty checkpoint")
    with pytest.raises(ValueError, match="archive"):
        verify_extracted(archive, root)


def test_crop_host_budget_refuses_oversized_case(monkeypatch):
    from mirai_ct.panorama_runtime import require_crop_memory

    monkeypatch.setattr(
        "mirai_ct.panorama_runtime.psutil.virtual_memory",
        lambda: type("RAM", (), {"available": 8 * 1024**3})(),
    )
    require_crop_memory((512, 512, 97), (240, 180, 50))
    with pytest.raises(MemoryError, match="crop"):
        require_crop_memory((1024, 1024, 1000), (1024, 1024, 1000))
