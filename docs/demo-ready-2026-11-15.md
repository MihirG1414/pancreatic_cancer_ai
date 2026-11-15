# Current research demo — 15 November 2026

This supersedes the earlier same-day milestone-6 handoff. The newly received
Colab ZIP has genuine segmentation and raw-probability outputs. The CT reference
conversion and reporting below are real completed work; they are not predictions
substituted from an annotation or synthetic test.

## Open and present

Open `outputs/panorama-demo-final-20261115/index.html`. Keep its entire directory
intact. Share `outputs/panorama-demo-final-20261115.zip`, which contains the HTML,
PNG display copies, viewer JavaScript/metadata and report.json. Source CT,
volumetric predictions and model weights remain outside that report ZIP and Git.

1. Show the **Research findings summary** at the top. State that this is a
   pretrained PANORAMA research screening demonstration.
2. Show native slice navigation and jump to the largest candidate cross-section
   (k=42). The source annotation and detection map use separate panels.
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
> We also prepared a second public CT with its matching source annotation. This
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

## Second public CT and reference are prepared

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

After receiving the second-case Colab ZIP:

```powershell
.\.venv\Scripts\python.exe -m mirai_ct.demo --manifest .\cases.cptac.reference.local.csv --case-id cptac_pilot_01 --input-export .\outputs\cptac-pilot-input-20261115-ready --bundle 'C:\path\to\panorama-cptac-pilot-01.zip' --require-model-products --reference-label 1 --reference-description 'CPTAC-PDA ROI 1 PANCREAS - 1; source contour-derived reference; diagnosis not inferred' --annotation-provenance .\data\CPTAC-PDA-pilot\reference-20261115\reference.json --output .\outputs\cptac-demo-with-products
```

Only this second-case inference/result remains pending here. Two successful runs
of the first CT are still **one unique model-tested CT**, not a two-case test set.

## Remaining completion gates

- Receive/import the second CT's actual outputs and inspect reference comparisons.
- Rehearse actual browser slider/zoom/opacity and local ZIP extraction. Static PNG
  and automated JS checks are separate from interactive browser acceptance.
- Establish an appropriate independent positive/negative patient cohort and
  diagnosis references; no case labels are inferred from empty tumor masks.
- Complete lesion-level matching/FROC and visual error review; classification
  AUC/sensitivity/specificity software already requires explicit PDAC references
  and patient separation. A clinical study is not established by running the CLI.
- Implement/test anatomical head/body/tail and a decision-attribution method.
  Avoid substituting a guess or calling the probability field attribution.
- Obtain expert input and resolve any commercial weight-use permission before
  company deployment. This delivery is an offline research demonstration.

No new network was trained. The local optional addition is the 2.4-MB pydicom
3.0.1 parser (`requirements-reference-io.txt`), not a CUDA/model installation.
