# Progress log

## 2026-09-22 - CPU environment and specification

- Read the supplied problem statement; scoped this session to CT intake and
  inspection. The full screening pipeline is deferred to pretrained PANORAMA
  inference on suitable compute. No models, CUDA or training frameworks installed.
- Inspected Windows 11 Home Single Language 10.0.26200 x64, Ryzen 5 3500U,
  5.95 GiB OS-visible RAM (about 0.55 GiB free at initial inspection), C: 4.44 GiB
  free, D: 458 GiB free. Reported installed hardware is 8 GB with integrated Vega 8.
- Found Python 3.13, 3.12 and 3.11. Created `.venv` using Python 3.11.1 x64.
  Installed lightweight NIfTI/plotting/notebook dependencies without pip cache.
  `pip check` found no broken requirements. Tests initially fail at collection
  because the planned package is not implemented yet, as expected.
- Folder initially contained only the problem statement, no scans or Git history.
  Initialized `milestone-1-ct-inspection` and configured the user-selected remote:
  `https://github.com/MihirG1414/pancreatic_cancer_ai.git`. Remote has no branches.
- Added private input, scan, weight, output and environment exclusions. Original
  supplied problem statement stays local; committed specification summarizes scope.
- Next: implement tested lazy loading and plotting; retrieve one real public case
  with a bounded download; execute the notebook; review and push checked commits.

## 2026-09-22 - Lazy loading and visualisation

- Added typed volume, CSV, plotting and CLI modules. Metadata omits identifying
  free-text headers; native geometry stays intact; only individual scaled slices
  are read. Existing labels are checked against shape, units, spacing and affine.
- 36 synthetic software checks passed, including `.nii`/`.nii.gz`, intensity
  scaling, corrupted payloads, no full-proxy conversion, low-memory behavior,
  mask mismatch refusal, CSV validation, plotting and CLI success/failure.
  Ruff passed on this implementation. No clinical/model performance is tested.
- Editable installation initially failed because the preinstalled environment
  build backend lacked `wheel`. Added explicit setuptools/wheel development
  dependencies, retried successfully and refreshed the dependency lock.
- Environment/core import check: about 611 MiB system memory available and
  4.14 GiB free on C: after installation. These are time-specific snapshots.
- Next: complete bounded public sample acquisition and real notebook verification.

## 2026-09-22 - Review fixes

- Review reproduced hidden full-volume read-ahead in NiBabel's proxy slicing for
  some shapes. Replaced it with sequential, explicitly bounded storage-slab reads.
  Other native planes are assembled from rows/columns with one 2D slab in memory.
- Review also reproduced a near-voxel translation accepted when spatial units
  were meters. Geometry comparisons now use millimeters internally (0.001 mm
  affine and 0.0001 mm spacing tolerance), leaving stored geometry untouched.
- Wrote both regressions, observed them fail, then fixed the implementation.
  55 tests passed after the fixes (38 core, 17 bounded-download software checks).
  Independent review additionally passed 24 comparisons against NiBabel across
  NIfTI-1/2, compressed/uncompressed files, both byte orders, scaling and all axes.
  No remaining important core review blocker was found.
