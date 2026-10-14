"""Notebook structure/syntax checks, never a substitute for GPU execution."""

import ast
from pathlib import Path

import nbformat


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
    assert "PERMITTED_NONCOMMERCIAL_USE = False" in joined
    assert "SOFTWARE_SMOKE_TEST = True" in joined
    assert "git+https" not in joined  # installation reads the tracked source-pinned lock
    assert "requirements-panorama-gpu-lock.txt" in joined
    assert "GIT_LFS_SKIP_SMUDGE" in joined
    assert "files.upload()" in joined and "files.download(" in joined
    assert "panorama_runtime" in joined
    assert '"preflight"' in joined and '"weights"' in joined and '"run"' in joined
