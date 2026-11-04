"""Reproduce Colab orchestration failures without CUDA, weights or real scans."""

import os
import subprocess
import sys

import pytest


@pytest.fixture
def baseline_repo(tmp_path, monkeypatch):
    from mirai_ct import panorama_runtime as runtime

    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init", "--quiet")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/data_utils.py").write_text("value = 1\n")
    git("add", "src/data_utils.py")
    git(
        "-c",
        "user.name=Synthetic Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "synthetic test repository",
    )
    monkeypatch.setattr(runtime, "BASELINE_REV", git("rev-parse", "HEAD"))
    return tmp_path, git


def test_generated_cache_does_not_block_clean_baseline(baseline_repo):
    from mirai_ct.panorama_runtime import validate_baseline_source

    root, _ = baseline_repo
    cache = root / "src/__pycache__"
    cache.mkdir()
    (cache / "data_utils.cpython-311.pyc").write_bytes(b"synthetic cache")
    validate_baseline_source(root)


@pytest.mark.parametrize("staged", [False, True])
def test_changed_tracked_source_is_rejected(baseline_repo, staged):
    from mirai_ct.panorama_runtime import validate_baseline_source

    root, git = baseline_repo
    (root / "src/data_utils.py").write_text("value = 2\n")
    if staged:
        git("add", "src/data_utils.py")
    with pytest.raises(ValueError, match="modifications"):
        validate_baseline_source(root)


@pytest.mark.parametrize("name", ["extra.py", "__pycache__/extra.py", "outside.pyc"])
def test_untracked_code_and_noncache_files_are_rejected(baseline_repo, name):
    from mirai_ct.panorama_runtime import validate_baseline_source

    root, _ = baseline_repo
    path = root / "src" / name
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="untracked"):
        validate_baseline_source(root)


def test_wrong_source_revision_is_rejected(baseline_repo, monkeypatch):
    from mirai_ct import panorama_runtime as runtime

    root, _ = baseline_repo
    monkeypatch.setattr(runtime, "BASELINE_REV", "0" * 40)
    with pytest.raises(ValueError, match="revision"):
        runtime.validate_baseline_source(root)


def test_inference_environment_overrides_colab_backend_and_bytecode(monkeypatch):
    from mirai_ct.panorama_runtime import configure_inference_environment

    monkeypatch.setenv("MPLBACKEND", "module://matplotlib_inline.backend_inline")
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "0")
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    configure_inference_environment()
    assert os.environ["MPLBACKEND"] == "Agg"
    assert os.environ["PYTHONDONTWRITEBYTECODE"] == "1"
    assert sys.dont_write_bytecode is True
    result = subprocess.check_output(
        [sys.executable, "-c", "import matplotlib; print(matplotlib.get_backend())"],
        text=True,
    )
    assert result.strip().lower() == "agg"
