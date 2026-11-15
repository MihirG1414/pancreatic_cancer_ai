# Current research demo — 15 November 2026

This supersedes the earlier same-day milestone-6 handoff. Genuine successful
Colab outputs have now been received for **two different real CTs**, from MSD
Task07 and CPTAC-PDA. Both include actual model segmentation and raw probability.
Source annotations were used only for local comparison, never as model inputs.
These are compatibility/research examples; training independence remains unresolved.

## Open and present

Open either report, keeping its entire directory intact:

| CT | Interactive report | Report-only share ZIP |
|---|---|---|
| MSD Task07 | `outputs/panorama-demo-final-20261115/index.html` | `outputs/panorama-demo-final-20261115.zip` |
| CPTAC-PDA | `outputs/cptac-demo-with-products/report/index.html` | `outputs/cptac-demo-with-products/demo-report.zip` |

Report ZIPs contain HTML, PNG display copies, viewer JavaScript/metadata and
report.json. Extract the ZIP before opening index.html. Source CT, volumetric
predictions and model weights remain outside the report ZIPs and Git.

1. Show the **Research findings summary** at the top. State that this is a
   pretrained PANORAMA research screening demonstration.
2. Show native slice navigation and jump to the largest candidate cross-section
   (k=42 for MSD, k=190 for CPTAC). The source annotation and detection map use
   separate panels.
3. Scroll to **Model segmentation and raw-probability heatmap**. These panels now
   show actual GPU model products. Probability-weighted display opacity leaves
   low-probability CT visible; stored probability values and the 0–1 scale are unchanged.
4. Show the mask measurements and reference-comparison table. Explain that the
   measurements come from model voxels, and the reference comes from the dataset.

Suggested short script:

> We now have an end-to-end pretrained PANORAMA pipeline running on a real 3D CT.
> It produces a candidate map, scan score, predicted lesion mask and probability
> heatmap. We preserve the scan's original geometry, measure the predicted mask,
> compare it with the dataset annotation, and generate this interactive report.
> The same pipeline now works on a second real CT from a different public
> collection, with its own model outputs and source-reference comparison. This
> is a working research prototype; independent accuracy testing is still pending.

## Genuine first-case evidence

Input is the existing public MSD Task07 `pancreas_290` CT. Its original compressed
source hash is unchanged. The second successful GPU run used the same official
baseline `d08f2356fa70d9460881fec0aedba4ebd1566c7e`, five folds in both stages,
and the unchanged baseline postprocessing. Recorded run duration: 222.998082
seconds, excluding setup and weight download. Earlier successful inference and
all old reports remain preserved.

| Result | Value | Meaning |
|---|---:|---|
| Scan score | 0.9995363951 | Uncalibrated maximum candidate score, not a personal cancer probability |
| Retained candidate regions | 1 | Connected positive detection-map support |
| Actual model mask | 4,946 voxels | Predicted stage-2 class 1, not annotation |
| Model-mask volume | 10.3753 mL | Native voxel volume; unvalidated model measurement |
| Inclusive native bounds | [244,276,35]–[273,304,47] | Original ijk coordinates |
| Native-axis box extent | 27.48 x 26.56 x 32.50 mm | Bounding extent, not clinical tumor diameter |
| Source tumor annotation | 3,521 voxels | Existing MSD label 2; PDAC histology unverified |
| Model/reference intersection | 3,211 voxels | Exact native-grid overlap |
| Model-mask Dice / IoU | 0.758474 / 0.610921 | This one case only; not independent accuracy |
| Candidate-support Dice / IoU | 0.748302 / 0.597830 | Different postprocessed region, not model-mask overlap |

All six declared bundle-output hashes and import/grid/voxel checks passed.
Model mask and probability are in
`outputs/panorama-demo-with-products-20261115/imported/`; successful import metadata
and original bundle/run logs are preserved beside it. The final report is rebuilt
from that import; inference was not repeated to change visualization.

Probability is the model's raw class-1 output, **not Grad-CAM or attention**.
Zeros outside the evaluated crop mean not evaluated. Head/body/tail and a
validated yes/no clinical cutoff remain unavailable. One high-scoring positive
example does not establish specificity, ROC-AUC or early-stage screening accuracy.

## Genuine second-case evidence and source reference

One selected pretreatment CPTAC-PDA CT was acquired from TCIA using bounded
one-series downloads with publisher MD5 and ZIP CRC checks. Its original native
grid is 512 x 512 x 251, spacing 0.78125 x 0.78125 x 2.0 mm. The series name hints
at PV acquisition; actual protocol suitability/training independence remain unverified.

The matched source RTSTRUCT has 28 closed contours on 27 native slices (176–202).
The new optional CPU converter checks source CT/DICOM hashes, frame/study/series
and per-contour SOP references, physical orientation/position, finite closed
contours, and the saved mask's geometry/voxels. It samples native voxel centers,
includes polygon boundaries, handles explicit XOR holes, and does not interpolate
between slices. See the [DICOM contour definitions](https://dicom.nema.org/MEDICAL/Dicom/2024a/output/chtml/part03/sect_C.8.8.6.html)
and [inner/outer contour rules](https://dicom.nema.org/MEDICAL/DICOM/current/output/chtml/part03/sect_C.8.8.6.3.html).

Derived reference: 64,219 voxels, 78.392334 mL. This is the source ROI's derived
reference volume; it is **not a new model prediction or PDAC diagnosis**. All three
native overlay views were inspected for display/placement; clinical contour review
and general rasterization validation remain pending.

- Reference report: `outputs/cptac-reference-report-20261115/index.html`.
- Native reference/provenance: `data/CPTAC-PDA-pilot/reference-20261115/`.
- Manifest with source reference: `cases.cptac.reference.local.csv`.
- CT-only upload files: `outputs/cptac-pilot-input-20261115-ready/`.

The CT/export hashes did not change and annotation was never supplied to the
model. Do not re-export input merely to add a local evaluation reference.

The received `panorama-output (2).zip` is a genuine successful result for the
second CT, not another run of the MSD scan. Its source checksum matches the
prepared CPTAC CT. Six declared output hashes, export provenance, official
source pins/five folds and native model-product grids/voxels passed validation.
Recorded inference duration: **229.141104 seconds** (about 3 minutes 49 seconds),
excluding setup/download. Sampled maxima were 6,564.86 MiB process-tree RAM and
1,905 MiB device usage; these are samples, not guaranteed exact peaks/minima.

| Second CT result | Value | Meaning |
|---|---:|---|
| Scan score | 0.9768324494 | Uncalibrated model score, not 97.68% cancer probability |
| Actual model mask | 39,059 voxels | Stage-2 class-1 prediction |
| Model-mask volume | 47.679443 mL | Unvalidated native-voxel measurement |
| Source reference | 64,219 voxels / 78.392334 mL | Explicit source ROI, not a new model output |
| Model/reference intersection | 38,875 voxels | Exact overlap on the original grid |
| Model-mask Dice / IoU | 0.752822 / 0.603621 | Per-case overlap, not diagnostic accuracy |
| Candidate-support Dice / IoU | 0.781370 / 0.641187 | Different postprocessed support, not model-mask overlap |

Independent direct MHA/reference counts agreed with the report's NIfTI comparison.
The predicted mask is smaller than the source reference: 25,344 reference voxels
are outside the mask, and 184 model voxels are outside the reference. The source
ROI's clinical interpretation/rasterization still needs expert review. Do not
present overlap as proof of a correct clinical diagnosis or complete tumor extent.

Original result, validated import and machine-readable report are preserved under
`outputs/cptac-demo-with-products/`. Rebuilding is optional; choose a new output
folder so the accepted report is preserved:

```powershell
.\.venv\Scripts\python.exe -m mirai_ct.demo --manifest .\cases.cptac.reference.local.csv --case-id cptac_pilot_01 --input-export .\outputs\cptac-pilot-input-20261115-ready --bundle 'C:\Users\Mihir1\Downloads\panorama-output (2).zip' --require-model-products --reference-label 1 --reference-description 'CPTAC-PDA ROI 1 PANCREAS - 1; source contour-derived reference; diagnosis not inferred' --annotation-provenance .\data\CPTAC-PDA-pilot\reference-20261115\reference.json --output .\outputs\cptac-demo-rebuild-new
```

There are now **two unique model-tested CTs**, not an independent evaluation
cohort. Repeated inference of the first CT does not add a third case. No cohort
ROC-AUC, specificity or lesion FROC is established by these two examples.

## Current review package supersedes earlier report layout

Use `outputs/review-polished-20261115/site/index.html` for the combined two-case
workspace. See [tomorrow's review guide](review-2026-11-16.md). The new layout
adds evidence cards, section navigation, presentation view, print styling and
an interactive selector over eight genuine CPTAC occlusion experiments. Original
CT/model/reference measurements are unchanged. The exploratory lesion-matching
software and two-case review are implemented; this is not clinical FROC validation.
Native head/body/tail integration is implemented, but genuine labels are absent.
The older report-specific verification and paths below remain historical evidence.

## Remaining completion gates

- Local Edge acceptance and extracted-ZIP rehearsal passed (details below).
  If presenting on another computer, repeat the extraction/opening check there.
- Establish an appropriate independent positive/negative patient cohort and
  diagnosis references; no case labels are inferred from empty tumor masks.
- Validate lesion-level matching/FROC and expert error review on an independent cohort; classification
  AUC/sensitivity/specificity software already requires explicit PDAC references
  and patient separation. A clinical study is not established by running the CLI.
- Obtain/review genuine anatomical head/body/tail masks. Conditional stage-2
  occlusion is completed for the second case; probability remains separate.
- Obtain expert input and resolve any commercial weight-use permission before
  company deployment. This delivery is an offline research demonstration.

No new network was trained. The local optional addition is the 2.4-MB pydicom
3.0.1 parser (`requirements-reference-io.txt`), not a CUDA/model installation.

## Verification completed

216 Python tests and 7 Node viewer-control tests passed, along with Ruff lint/
format, dependency, Markdown-link and whitespace checks. The new real reference
overlays and all three genuine model-mask/probability PNGs were visually inspected.

Actual native Edge acceptance passed for the local report: synchronized panels,
first/last slice boundaries, largest-candidate focus (k=42), previous/next (k=43
has 618 candidate voxels), shared candidate zoom, fill/outline/off, opacity and
offline reload. Screenshots confirmed actual rendering. The separate report
window remains open; the user's active Colab window/runtime was preserved.
Second CT verification also passed: all six bundle hashes; matching original
CT/export identity; unchanged native grids and every imported model-output plane;
independent direct MHA/reference counts matching the NIfTI report; all 1,004
viewer PNGs, nine static views and local HTML asset references; ZIP CRC and
byte-for-byte report membership. All three model-mask/raw-probability PNGs and
all three separate reference/candidate PNGs were visually inspected.

Actual Edge checks on the second report confirmed k=0/250 boundaries (Previous/
Next disabled respectively), largest-candidate focus k=190 (3,088 voxels), next
k=191 (2,977), and shared zoom. The reference comparison table rendered the
verified values. The report-only ZIP was extracted to
`outputs/cptac-demo-extracted-check-20261115/` and opened locally in Edge. Its CT,
reference and candidate panels loaded, Off hid the candidate overlay, and reload
restored k=190 / Fill / 65% opacity / full view. Browser accessibility values
sometimes lagged rendering; screenshots and status text confirmed actual state.
The extracted demo is left open in a separate report window; Colab is preserved.

Second report ZIP: 36,791,910 bytes; SHA256
`99d4824283f3a3afc432d6b998d047418704eacb8e5c8a2357808f91ef7b6fa7`.
Original input result ZIP SHA256:
`62d12440b8fb679db437b6fb40ad6e67294a0c79b87ead35739ddbb4497c035a`.
The notebook upload fix passed 12 targeted notebook tests plus Ruff/format and
cleared-notebook/syntax checks. No source behavior changed during the second
result import, so the full project suite was not repeated for documentation-only
handoff updates. These checks do not establish clinical model performance.
