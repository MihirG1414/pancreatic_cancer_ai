"""Notebook structure/syntax checks, never a substitute for GPU execution."""

import ast
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import nbformat
import pytest


def code_cells():
    notebook = nbformat.read(Path("notebooks/02_panorama_inference_colab.ipynb"), as_version=4)
    return [cell.source for cell in notebook.cells if cell.cell_type == "code"]


def test_colab_notebook_is_cleared_valid_and_compilable():
    notebook = nbformat.read(Path("notebooks/02_panorama_inference_colab.ipynb"), as_version=4)
    nbformat.validate(notebook)
    codes = []
    for cell in notebook.cells:
        if cell.cell_type == "code":
            assert cell.outputs == []
            assert cell.execution_count is None
            tree = ast.parse(cell.source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in ("check_input", "plot_code")
                    for target in node.targets
                ):
                    ast.parse(ast.literal_eval(node.value))
            codes.append(cell.source)
    joined = "\n".join(codes)
    assert len(codes) == 9
    assert "PERMITTED_NONCOMMERCIAL_USE = False" in joined
    assert "SOFTWARE_SMOKE_TEST = True" in joined
    assert "git+https" not in joined  # installation reads the tracked source-pinned lock
    assert "requirements-panorama-gpu-lock.txt" in joined
    assert "GIT_LFS_SKIP_SMUDGE" in joined
    assert "files.upload()" in joined and "files.download(" in joined
    assert "panorama_runtime" in joined
    assert '"preflight"' in joined and '"weights"' in joined and '"run"' in joined


def test_model_environment_is_headless_before_inference():
    tree = ast.parse(code_cells()[3])
    env_call = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dict"
        and any(k.arg == "PYTHONPATH" for k in node.keywords)
    )
    settings = {k.arg: k.value for k in env_call.keywords}
    assert ast.literal_eval(settings["MPLBACKEND"]) == "Agg"
    assert ast.literal_eval(settings["PYTHONDONTWRITEBYTECODE"]) == "1"


@pytest.mark.parametrize("success", [True, False])
def test_download_works_without_preview_variables(tmp_path, monkeypatch, success):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "run.json").write_text(
        json.dumps(
            {
                "status": "success" if success else "failed",
                "execution_kind": "pretrained-inference",
            }
        )
    )
    archive = tmp_path / "panorama-output.zip"
    archive.write_bytes(b"synthetic output archive")
    downloaded = []
    google = ModuleType("google")
    colab = ModuleType("google.colab")
    colab.files = SimpleNamespace(download=downloaded.append)
    google.colab = colab
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.colab", colab)
    namespace = {"RUN_DIR": tmp_path}
    if success:
        exec(compile(code_cells()[-1], "download-cell", "exec"), namespace)
        assert downloaded == [str(archive)]
    else:
        with pytest.raises(RuntimeError, match="Successful"):
            exec(compile(code_cells()[-1], "download-cell", "exec"), namespace)
        assert downloaded == []


@pytest.mark.parametrize("export", [True, False])
def test_notebook_run_requests_model_outputs_when_selected(tmp_path, export):
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0)

    namespace = {
        "ROOT": tmp_path,
        "PYTHON": Path(sys.executable),
        "INPUT": tmp_path / "input",
        "BASELINE": tmp_path / "baseline",
        "ENV": {},
        "EXPORT_MODEL_OUTPUTS": export,
        "time": SimpleNamespace(strftime=lambda *args: "fixed", gmtime=lambda: None),
        "subprocess": SimpleNamespace(run=fake_run, STDOUT=-2),
    }
    exec(compile(code_cells()[6], "run-cell", "exec"), namespace)
    assert ("--include-model-outputs" in commands[0]) is export


@pytest.mark.parametrize("success", [False, True])
def test_weights_cell_preserves_diagnostic_before_manifest_read(
    tmp_path, monkeypatch, capsys, success
):
    def fake_run(command, **kwargs):
        assert command[3] == "weights"
        assert kwargs.get("check") is not True
        kwargs["stdout"].write("weights ready" if success else "GPU pilot failed: fixture failure")
        return SimpleNamespace(returncode=0 if success else 1)

    if success:
        (tmp_path / "weight-provenance.json").write_text('{"fixture": "synthetic"}')
    namespace = {
        "ROOT": tmp_path,
        "PYTHON": Path(sys.executable),
        "ENV": {},
        "json": json,
        "subprocess": SimpleNamespace(run=fake_run, STDOUT=-2),
    }
    if success:
        exec(compile(code_cells()[5], "weights-cell", "exec"), namespace)
    else:
        with pytest.raises(RuntimeError, match="Weight preparation failed"):
            exec(compile(code_cells()[5], "weights-cell", "exec"), namespace)
    log = tmp_path / "weights-setup.log"
    assert log.is_file()
    assert (
        "weights ready" if success else "GPU pilot failed: fixture failure"
    ) in capsys.readouterr().out
