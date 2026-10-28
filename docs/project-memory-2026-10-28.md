# Mirai / Rises.io project memory

Updated: **28 October 2026, Asia/Calcutta**. This file is a portable snapshot for
updating an earlier project chat. For later work, read root `PROGRESS.md` first;
it remains the authoritative current checkpoint.

## 1. Current project status

The pancreatic CT project now has a working pipeline from a real CT scan through
pretrained PANORAMA inference to a locally generated HTML report.

**The first real PANORAMA inference run completed successfully in Google Colab.**
The downloaded outputs were validated against the original CT, imported locally,
and displayed in an HTML report containing six images.

Earlier statements such as “GPU inference pending,” “no genuine predictions
exist,” or “the notebook has never executed” describe historical checkpoints.
They no longer describe the current project state.

This establishes a **successful one-case software demonstration**. Clinical
performance, diagnostic accuracy and evaluation independence remain unverified.
No new model was trained.

## 2. Working pipeline

```text
Real NIfTI CT
  -> Local CT intake and geometry inspection
  -> Verified CT-only MHA export
  -> Google Colab GPU inference with pretrained PANORAMA
  -> Prediction and provenance output bundle
  -> Local integrity and physical-grid validation
  -> Native-grid prediction import
  -> HTML report with CT, annotation and prediction views
```

Original CT and annotation files remain unchanged. PANORAMA resamples and crops
derived working copies internally. Its final detection map is restored to the
original image grid; the local importer does not silently resample or register it.

## 3. Completed milestones

| Stage | Completed work |
|---|---|
| CT intake and inspection | Load `.nii`/`.nii.gz`, inspect geometry and metadata, read bounded native slices and display existing annotations |
| Real sample acquisition | Download one public MSD Task07 CT, its existing annotation and dataset metadata without downloading the entire dataset |
| Annotation report | Calculate annotation voxel counts, physical volumes and bounding boxes; render native CT views |
| PANORAMA input preparation | Export CT to MHA with checked RAS/LPS conversion, intensity samples and provenance |
| Colab integration | Pin source revisions, create an isolated GPU environment, check resources and verify model downloads |
| Real GPU inference | Execute both pretrained stages using all five folds per stage |
| Prediction import | Verify input/output hashes, source revisions, physical alignment, finite map values and score consistency |
| Final report | Generate HTML with separate CT, annotation and candidate-map panels |
| New-PC recovery | Restore the local environment, redownload the public case, match its hash to the Colab input and regenerate the report |

The latest completed milestone is restoration of the original public CT on the
new PC and generation/inspection of the first report using actual PANORAMA output.

## 4. Real case and input provenance

| Item | Value |
|---|---|
| Case | `pancreas_290` |
| Dataset | Medical Segmentation Decathlon, Task07 Pancreas |
| Source split | MSD training case |
| Dimensions | `512 x 512 x 97` voxels |
| Voxel spacing | Approximately `0.916 x 0.916 x 2.5 mm` |
| Native orientation | RAS |
| Recorded dataset license | CC BY-SA 4.0 |

The downloader uses only the required archive byte ranges. It verifies archive
ETag, tar headers, response ranges, byte lengths and gzip integrity. The restored
CT is 28,093,127 compressed bytes; its existing annotation is 28,963 bytes.

The new-PC CT SHA256 exactly matches both original input and run provenance:

```text
4b5cb353850c0a68c5b1824519777ef2a736cb171bcbad277c55cfd8c4abaaf8
```

The original `ct.mha` also matches the Colab input hash:

```text
2511980c4a9689647cb808ebcf6bbace82109332147a25b8a2af47242e6fe08c
```

The existing annotation was **not uploaded as an inference input**. It is used
separately for display and annotation measurements.

| Existing dataset annotation | Voxels | Approximate volume |
|---|---:|---:|
| Label 1: pancreas | 29,162 | 61.1735 mL |
| Label 2: cancer annotation | 3,521 | 7.3860 mL |

These measurements are dataset-derived, not PANORAMA-derived. Contrast phase,
HU calibration and clinical metadata remain unverified. The current sample is
explicitly treated as a software smoke test with unknown metadata retained as
unknown/null rather than invented.

## 5. Pretrained PANORAMA execution

Stage 1 runs the pancreas model on a lower-resolution working image and uses the
predicted extent to select a crop. Stage 2 runs PDAC detection on the crop,
extracts retained candidates and restores the candidate map to the full CT grid.

Both stages used folds **0, 1, 2, 3 and 4**, with ten checkpoints in total. The
workflow retains the baseline saved plans, test-time augmentation and core
preprocessing/postprocessing. It uses one preprocessing/export worker to bound
host use and does not use Docker.

Pinned source revisions:

```text
PANORAMA baseline:
d08f2356fa70d9460881fec0aedba4ebd1566c7e

nnU-Net:
834b80ffa8517e6cd2981982eb7edc75b2d131d8
```

The final exported products integrated into the report are:

- `images/pdac-detection-map/detection_map.mha`
- `pdac-likelihood.json`
- Run/input provenance, dependency information, stage logs and weight license

Internal segmentations and raw class probabilities are working intermediates;
the current report does not expose them as complete final model products.

## 6. Actual run results

The successful run began on **28 October 2026 at approximately 01:31 IST**.

| Item | Recorded result |
|---|---|
| Status | `success` |
| Execution kind | `pretrained-inference` |
| GPU | NVIDIA Tesla T4 |
| Total GPU memory | 15,360 MiB |
| Total recorded run duration | 167.6979 seconds, approximately 2 minutes 48 seconds |
| Stage 1 duration | 19.5774 seconds |
| Stage 2 duration | 142.4380 seconds |
| Scalar score | `0.999536395072937` |

Both stage logs finish with `done with scan`. The recorded runtime excludes the
complete environment setup and model-download process and is not a general
speed benchmark.

Approximately one-second resource sampling recorded:

- Maximum observed process-tree RSS: 6,156.77 MiB.
- Maximum observed device memory usage: 1,719 MiB.
- Minimum observed available host memory: 8,546.75 MiB.

These are sampled observations, not exact guaranteed peaks or minimum hardware
requirements. The notebook's conservative operating gates remain 12 GiB free
VRAM, 8 GiB available host RAM and 15 GiB free disk; one run does not establish
safe lower gates.

**The scalar is an uncalibrated model score. It is not a 99.95% clinical
probability of cancer.**

## 7. Why the prediction appears as a yellow patch

The exported image is a candidate detection map, not a whole-pancreas overlay or
a smooth raw probability heatmap.

Direct inspection of this case's imported map found:

- 5,168 nonzero voxels.
- Nonzero values on native slices 35 through 47.
- Every nonzero voxel has the same candidate value: `0.999536395072937`.
- Therefore, the rendered candidate looks nearly solid yellow.

The existing report selects the first location containing the maximum map value.
Because the candidate score is uniform, it selects native focus `[251, 290, 35]`,
near the region's edge. Slice 35 has only 107 highlighted voxels. Slice 42 has
640 and would show a larger cross-section.

A clearer viewer could select the largest candidate cross-section, provide
zoom/outlines and allow slice navigation. **These improvements were discussed
but have not been implemented.** No prediction should be altered merely to
improve its appearance.

The colored region is not a confirmed diagnosis, validated tumor boundary or
Grad-CAM explanation.

## 8. Technology stack

Local reporting and Colab inference have separate environments.

| Layer | Technology/version | Role |
|---|---|---|
| Local operating environment | Windows, PowerShell | Intake, validation, reporting and development |
| Local Python | 3.12.14 in `.venv` | Current new-PC environment |
| Numerical arrays | NumPy 2.5.4 locally | Array calculations and validation |
| NIfTI IO | NiBabel 5.4.2 locally | CT metadata, affine geometry and lazy access |
| Medical-image IO | SimpleITK 2.4.0 | MHA IO, independent geometry checks and import |
| Plotting | Matplotlib 3.11.2 locally | CT slices and separate overlays |
| Memory checks | psutil 7.2.2 locally | Process/system memory monitoring |
| Notebook support | Jupyter/IPython, ipykernel | Interactive inspection and Colab workflow |
| Report presentation | Static HTML, CSS and PNG | Local report without an application server |
| GPU compute | Google Colab, Tesla T4 | Pretrained model execution |
| Deep learning | PyTorch 2.4.0 | CUDA inference |
| Model framework | nnU-Net v2 2.5.1 | Pretrained 3D inference |
| Candidate extraction | report-guided-annotation 0.2.7 | Baseline postprocessing |
| Tests | pytest 9.1.1 locally | Software regressions |
| Lint/format | Ruff 0.17.3 locally | Code checks |
| Version control | Git, GitHub | Source and checkpoint history |

Important versions in the **Colab inference environment**:

```text
Python 3.11
PyTorch 2.4.0
nnU-Net 2.5.1
NumPy 1.24.4
SciPy 1.10.1
SimpleITK 2.4.0
scikit-image 0.21.0
report-guided-annotation 0.2.7
dynamic-network-architectures 0.3.1
acvl-utils 0.2
```

Colab uses an isolated Python environment created with pinned uv 0.8.22. The
notebook kernel and model subprocess interpreter need not have the same Python
version. scikit-image 0.21.0 is a documented Python-wheel adaptation from the
baseline build log's 0.19.3.

The new PC has about 15.19 GiB of OS-visible RAM. Historical Ryzen 5/8 GB laptop
notes refer to the previous PC. PyTorch and model weights remain absent from
the current local reporting environment. SimpleITK is installed directly in
the new `.venv`; the previous PC used a separate optional target directory.

## 9. Repository architecture

| Module/file | Responsibility |
|---|---|
| `src/mirai_ct/volume.py` | CT loading, geometry, bounded slice reading and memory checks |
| `src/mirai_ct/cases.py` | Local manifest parsing and validation |
| `src/mirai_ct/visualization.py` | CT, annotation and candidate-map rendering |
| `src/mirai_ct/panorama_io.py` | CT-only MHA export and physical-space validation |
| `src/mirai_ct/panorama_runtime.py` | GPU preflight, weight verification, execution and packaging |
| `src/mirai_ct/panorama.py` | Bundle validation and native-grid import |
| `src/mirai_ct/report.py` | HTML report and PNG generation |
| `scripts/download_sample.py` | Bounded public single-case acquisition |
| `notebooks/01_inspect_ct.ipynb` | Local inspection notebook |
| `notebooks/02_panorama_inference_colab.ipynb` | Colab inference workflow |
| `PROGRESS.md` | Authoritative current checkpoint |

The CT inspector uses bounded slice access rather than routinely caching an
entire volume. Conversion/import have separate allocation checks. NIfTI RAS
and SimpleITK LPS coordinates are handled explicitly. Original source images
are never overwritten.

## 10. Verification completed

On the new PC:

- **118 software tests passed**.
- Ruff lint/format passed for `src`, `tests` and `scripts`.
- `pip check` and Git whitespace checks passed.
- All four recorded bundle output hashes matched.
- Original CT and MHA hashes matched inference provenance.
- Prediction dimensions and physical grid matched the CT.
- Map values were finite and within `[0, 1]`.
- Scalar score matched the map maximum.
- Restored NIfTI sample planes matched imported map values.
- HTML referenced all six generated images correctly.
- All six report images were visually inspected.

Eight warnings concerned a SimpleITK/NumPy deprecation and did not fail tests.
Only `tests/test_panorama_notebook.py` was excluded: its cleared-output contract
conflicts with the user's already committed executed notebook. That notebook
was preserved. Do not describe the latest check as “all 119 tests passed”; the
119-test result belongs to the earlier cleared-notebook state.

Software checks do not establish diagnostic performance.

## 11. Colab issues resolved for this run

1. The baseline source-cleanliness guard rejected an untracked generated
   `src/__pycache__/data_utils.cpython-311.pyc`. Only that cache was removed and
   subprocess `ENV["PYTHONDONTWRITEBYTECODE"] = "1"` was set.
2. Stage 1 inherited Colab's inline Matplotlib backend, unavailable in the
   isolated environment. Setting subprocess `ENV["MPLBACKEND"] = "Agg"` fixed it.
3. Cell 9 referenced undefined notebook variable `run`. Reloading
   `RUN_DIR / "bundle/run.json"` enabled the successful output download.

These runtime workarounds enabled the completed run. Permanent runner/notebook
fixes and regression tests remain follow-up work.

## 12. Current local files and report

Repository root:

```text
C:\Users\Mihir1\Downloads\pancreatic_cancer_ai
```

Paths relative to that repository:

```text
Original CT:
data\MSD_Task07\Task07_Pancreas\imagesTr\pancreas_290.nii.gz

Existing annotation:
data\MSD_Task07\Task07_Pancreas\labelsTr\pancreas_290.nii.gz

Local case manifest:
cases.local.csv

Validated prediction import:
outputs\panorama-import-20261028

Generated report:
outputs\panorama-report-20261028\index.html

Shareable report ZIP:
outputs\panorama-report-20261028.zip

Local environment snapshot:
outputs\report-environment-20261028.txt
```

Original input export:

```text
C:\Users\Mihir1\Downloads\Telegram Desktop\
    ct.mha
    input-provenance.json
    clinical-information-pancreatic-ct.json
```

Extracted Colab output:

```text
C:\Users\Mihir1\Downloads\panorama-output
```

The report ZIP contains HTML and six PNGs. Keep those PNGs alongside the HTML
when sharing an extracted report. There is no need to rerun inference to view it.

Datasets, weights, environments, generated reports and the local manifest are
excluded from Git. **Cloning onto another PC does not restore these artifacts.**
Only the public sample was redownloaded during this new-PC recovery; no full
dataset or model weights were downloaded locally.

## 13. Git and handoff

```text
Repository:
https://github.com/MihirG1414/pancreatic_cancer_ai

Branch:
milestone-1-ct-inspection

Verified report-delivery revision, before adding this memory file:
1d4e52d5b75804011c884f0dca1f99195040fa85
```

At verification, local and actual remote heads matched and the working tree was
clean. The user-saved Colab notebook was preserved. This document will introduce
a later documentation commit; do not mistake the report-delivery revision for
an immutable future branch head.

Read root `PROGRESS.md` first when resuming. `docs/progress.md` is historical
evidence, not a competing current task list. Preserve local artifacts, unrelated
changes and active kernels. Keep original geometry, use one scan at a time,
monitor memory and distinguish software fixtures from genuine model outputs.

## 14. Remaining limitations and next work

Still unresolved or unimplemented:

- Exact overlap between this MSD training case and PANORAMA development data.
- Verified venous contrast phase, HU calibration and clinical metadata.
- Performance on independent held-out cases.
- Calibrated clinical risk and validated decision thresholds.
- Validated model-derived tumor measurements and head/body/tail assignments.
- Explanation methods such as Grad-CAM.
- Interactive slice navigation, zoom and better candidate-focus selection.
- Automated clinical radiology report generation.
- Permanent Colab environment/cache/download fixes.

Weights are recorded as **CC BY-NC 4.0**. Baseline code and dataset licenses are
separate. Permitted use must remain part of future deployment planning.

Next milestones: improve display visibility without changing predictions; make
the runtime fixes permanent and test them; then establish a suitable independent
evaluation dataset before reporting diagnostic accuracy.

**Do not rerun successful GPU inference merely to view or improve the existing
report. Reuse the saved validated prediction bundle.**

## Reference links

- Current checkpoint: [PROGRESS.md](../PROGRESS.md)
- Demo/import instructions: [Milestone 3 guide](milestone-3-demo.md)
- Source review: [PANORAMA inference plan](panorama-inference-plan.md)
- Official baseline: https://github.com/DIAGNijmegen/PANORAMA_baseline
- Official weights: https://zenodo.org/records/11160381
