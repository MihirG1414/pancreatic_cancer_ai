# CT inspection implementation plan

**Goal:** A reproducible CPU-only NIfTI inspection milestone for Mirai / Rises.io.

**Architecture:** One small Python package shared by CLI and notebook. Lazy
volume access, strict geometry validation and local-only scan manifests.

**Tech stack:** Python 3.11, NiBabel, NumPy, Matplotlib, psutil, ipykernel,
nbformat, nbclient, pytest, Ruff. Native Windows / PowerShell.

## Tasks and review points

- [x] Environment and Git: initialize a milestone branch, add privacy ignores,
  create `.venv` with `py -3.11 -m venv .venv`, install binary dependencies without
  cache, capture exact installed versions and run `python -m pip check`.
  Record machine measurements and commit the verified setup.
- [x] Tests first: add `tests/test_volume.py`, `tests/test_cases.py` and
  `tests/test_visualization.py`. Generate tiny arrays in pytest temp directories,
  including a translated mask that has the same shape. Verify missing APIs fail.
- [x] Implement `src/mirai_ct/volume.py`: `load_volume(path)`, `metadata(image)`,
  `read_slice(image, axis, index)`, `check_geometry(scan, mask)`, memory reporting.
  Reject non-3D input; preserve transforms and apply NIfTI scaling per slice.
- [x] Implement `cases.py`, `visualization.py`, `__main__.py`: validated local
  CSVs, native-axis slice plots with optional integer mask and explicit metadata.
  Run `python -m pytest -q` and `python -m ruff check .`; review and commit.
- [x] Add `notebooks/01_inspect_ct.ipynb`, `cases.example.csv`, README and official
  dataset instructions. Execute notebook through nbclient using ignored outputs.
- [x] Inspect one public CT and matching label if a verified single-case object
  is accessible; record source, license, checksums and geometry locally. Otherwise
  document the precise access blocker. Never download a dataset archive.
- [x] Review privacy, geometry and memory handling. Run tests, lint, pip check,
  inspect plotted slices, update `docs/progress.md` with measured evidence and
  limitations, commit and push to the requested remote without force.

No existing implementation or tests were present. Work stays in the supplied
project folder on a dedicated milestone branch; no duplicate worktree is needed
for this new repository. The user's detailed scope and instruction to execute
authorize these routine design choices and commits. The user selected origin at https://github.com/MihirG1414/pancreatic_cancer_ai.git; the checked core commits have pushed successfully. Final documentation is pushed at session close.
