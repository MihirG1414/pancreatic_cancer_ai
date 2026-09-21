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

## 2026-09-22 - Real data and notebook validation

- Downloaded exactly one real public MSD Task07 CT and its existing segmentation
  from the official EU mirror (28,122,090 compressed image/mask bytes, plus small
  dataset metadata). No full archive or weights downloaded. Data is on D: outside
  Git. Pinned ETag, TAR headers, exact range/length and gzip CRC checks passed;
  source/license/time/SHA256 are in the local provenance file.
- Real scan: 512 x 512 x 97, float32, spacing approximately
  0.916016 x 0.916016 x 2.5 mm, RAS orientation, qform/sform code 1, zero reported
  obliquity and no geometry warnings. Existing mask geometry matched.
- Ran the CLI with the real scan and existing mask; saved a middle-plane PNG.
  Executed all notebook cells with the real pair and inspected rendered PNGs
  for all three native middle planes. Images, axis labels and annotation legends
  rendered correctly. This is a visual software check, not clinical review.
- Also executed the complete real-data notebook with the optional mask omitted;
  it displayed CT-only planes successfully. Recomputed all downloaded-file
  SHA256 hashes after inspection; they match the acquisition provenance.
- Notebook RSS snapshots: 92.1 MiB before loading, 92.8 after headers, then
  100.1 / 104.9 / 113.1 after the three displayed planes. System available memory
  snapshots ranged approximately 692-824 MiB during plotting. These are not peak
  memory measurements. Full-volume caches remained empty.
- Executed notebook and figures stay under ignored `outputs/`. The tracked
  notebook has no outputs or execution counts. Jupyter emitted Windows event-loop
  fallback and local TCP transport warnings; execution completed successfully.
- No data-access blocker remains for this sample. Broader PANORAMA inference,
  GPU access, weights, train/test overlap analysis, clinical validation, and all
  prediction/performance claims remain deferred and untested. No inference code
  is integrated. The supplied statement's wider deliverable is not yet complete.
- Session commits so far: `4f17cb6` environment/specification, `f2f4775` CT loading
  and overlays, `ceb7bbf` bounded-read and geometry-unit fixes. Final notebook,
  downloader and documentation commit follows final checks, then routine push.
- Final checks: 55 tests passed; Ruff lint and formatting passed; `pip check`
  reported no broken dependencies; locked-requirement dry run required no changes.
  Validated output-free notebook schema and Git exclusions. Code-review fixes
  passed independent review. No standalone type checker is configured.
- The first three commits pushed successfully to `origin/milestone-1-ct-inspection`.
  The final notebook/data-access documentation commit will use the same routine
  push. Next session: plan pretrained PANORAMA inference and suitable GPU access;
  this completed intake milestone does not validate the wider screening system.
