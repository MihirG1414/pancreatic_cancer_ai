# PANORAMA Pilot Implementation Plan

**Goal:** Export one verified CT, prepare a five-fold GPU pilot, and import genuine
baseline outputs into the local report.

**Architecture:** `panorama_io.py` owns geometry/export; `panorama.py` owns
prediction import; `panorama_runtime.py` owns GPU orchestration. Reuse loader,
manifest and plotting functions. Optional SimpleITK stays outside core runtime.

**Tech stack:** Existing Python 3.11/NumPy/NiBabel/psutil/matplotlib; optional
SimpleITK 2.4.0; GPU Python 3.11, torch 2.4.0, nnU-Net 2.5.1.

Execute inline in the authorized existing branch. Review before delivery.

## Sequential tasks

- [x] Write `tests/test_panorama_io.py`: anisotropic rotated/reflected affine
  with translation, intensity scaling, both corner conventions; failure for
  unknown units, shear, conflicting transforms, insufficient RAM, overwrite.
  Run `.venv/Scripts/python.exe -m pytest tests/test_panorama_io.py -q` and
  observe missing-module failure before implementation.
- [x] Implement `src/mirai_ct/panorama_io.py`, optional requirements file;
  verify tests with `outputs/panorama-io` on PYTHONPATH. Run manifest export
  on pancreas_290; verify source hash, actual MHA and saved verification JSON.
- [x] Commit verified export and progress evidence using specific filenames.
- [x] Write runner tests for pinned commands, archive safety, checksums,
  checkpoint completeness, empty masks and invalid crops. Observe failure.
- [x] Implement `src/mirai_ct/panorama_runtime.py` and
  `notebooks/02_panorama_inference_colab.ipynb`. Run static notebook validation,
  compile code cells, dependency resolution check, source/API compatibility
  review. Probe available browser/runtime; do not claim unexecuted inference.
- [x] Write `tests/test_panorama.py` for genuine-format synthetic bundles:
  map/score/hashes/source geometry and failure cases. Observe failure.
- [x] Implement importer and extend `report.py`/`visualization.py`. Run tests;
  generate real CT unavailable-prediction report and clearly synthetic overlay
  fixture for manual view verification. Never save synthetic results as real.
- [x] Write `docs/milestone-3-demo.md`, update README/progress. Run full pytest,
  Ruff lint/format, pip check, whitespace/notebook-output/privacy checks.
- [ ] Review complete diff, fix findings, commit related groups, push existing
  branch and compare remote/local head. Record genuine GPU blocker/next action.
