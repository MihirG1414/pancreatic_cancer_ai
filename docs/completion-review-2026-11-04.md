# Project completion review — 4 November 2026

This review compares the implementation with the actual original phase-one
problem statement, read locally on 2026-11-04 from the user's private attachment.
The source document remains outside Git. It requires a working pretrained
screening pipeline with score, location/size, segmentation and heatmap, followed
by the stated validation metrics. This review distinguishes implemented software,
genuine model artifacts and requirements that still need evidence.

## Implemented and demonstrated

| Capability | Evidence/status |
|---|---|
| CPU NIfTI intake, native geometry and bounded slices | Implemented and regression-tested |
| Existing annotation inspection/measurements | Implemented; never presented as model-derived |
| CT-only MHA export with provenance | Implemented; recovered original export matches successful run |
| Pretrained two-stage five-fold PANORAMA | One real Colab T4 pilot completed, 167.6979 seconds |
| Prediction integrity and original-grid import | Genuine pilot imported and checked locally |
| Static HTML demonstration | Generated 2026-10-28, preserved |
| More visible default candidate slice | Largest positive native-k cross-section, k=42 in this case |
| Offline native slice viewer | Implemented: 97 slices, separate synchronized panels, zoom, fill/outline/off, opacity |
| Known Colab runtime defects | Source fixes/regressions for headless backend, caches and standalone download |
| Cleared distributable notebook | Nine ordered cells; executed evidence preserved locally |
| Candidate coordinates and approximate support extent | Optional connected-region measurements in voxel/RAS/LPS coordinates; explicitly not validated tumor size |
| Additional model-product export/import | Implemented with synthetic checks: native-grid class-1 segmentation and raw probabilities; fresh GPU artifacts unavailable |

The reviewed real report is `outputs/panorama-report-20261104-reviewed/index.html`. Its `viewer/`
folder contains native PNG display copies and embedded metadata is used in the
HTML. It does not call a remote API, fetch the original scans in the browser or
require a local web server. Keep the entire report directory when sharing.

Automated control tests cover synchronization, native zoom crop, fill/outline/off,
opacity, boundaries/focus, delayed image races, missing assets and empty input
states. Actual Edge interaction/rendering verification was attempted but the
computer-use tool stopped because it could not determine the current browser
URL sufficiently to enforce its access policy. No further UI input was sent.
**Manual browser verification remains pending.** Python checks of actual PNG
orientation/assets and inspection of static views are separate evidence.

The corrected GPU runner/notebook has not been rerun on a GPU. The previous
genuine inference result remains the only model execution result in this project.
Future fresh GPU execution should verify the corrected handoff when needed;
displaying existing predictions does not require it.

## Remaining broader requirements

| Requirement | Current limit and next evidence required |
|---|---|
| Diagnosis/detection performance | No independent performance estimate. Need permitted, labeled cases with documented overlap audit, positive/negative case mix and patient-level separation |
| Tumor segmentation and size | Optional stage-2 class-1 mask export/import is implemented but needs actual recovered/new GPU products and reference validation. Candidate support geometry is available separately and is not clinical tumor volume |
| Whole-pancreas model segmentation in report | Used internally by the baseline; not preserved in current final export contract. Any exposure of intermediates must record their crop/grid transformations |
| Head/body/tail location | Not implemented; no validated anatomical partition in current outputs |
| Heatmap/decision explanation | Raw class-1 probability export/import/plotting is implemented but needs GPU products. This is not decision attribution; Grad-CAM/attention remains unimplemented |
| Clinical risk probability | Not calibrated. The reported maximum candidate score is not an individual disease probability |
| Clinical/radiology narrative | Current report documents software outputs and annotations; no automated diagnostic narrative |
| Input suitability | Sample venous phase, HU calibration and clinical fields remain unverified |
| General input UI/deployment | Existing CLI/notebook and offline report satisfy the stated script/notebook form; no hosted deployment is required by the original phase-one statement |
| Weight use in a company product | Separate weight permission/licensing remains unresolved for commercial deployment |

## Evaluation data, in plain language

We need CT scans to test the model, ideally with expert annotations and a
reliable diagnosis/reference. To estimate generalization, the same patients and
scans must not have been used to train or develop the model. A different filename
or downloading another MSD/PANORAMA development case does not establish this.
The current `pancreas_290` sample remains a software demonstration with unknown
training overlap. Running more development cases can test robustness of the
software, but is not automatically an independent accuracy evaluation.

Before a performance run, record source/license and permission, de-identification,
CT phase/intensity suitability, reference-label provenance, patient/study IDs
locally and duplicate/overlap checks. Define the endpoint and threshold before
evaluating; do not tune a threshold on the same cases used for the final result.
The original metrics are detection sensitivity/FROC, case-level ROC-AUC and
sensitivity/specificity, segmentation Dice/IoU and visual error review. We need
appropriate reference labels and multiple positive/negative cases before these
can be reported meaningfully. No minimum clinical study size is claimed here.
The source's PANORAMA-to-MSD example does not prove independence for this baseline;
its development set includes MSD cases, so exact overlap must still be checked.

The original statement also discusses density, margins and duct dilation as
features a screening model should capture, with longitudinal growth only when
prior scans exist. We have not separately established that this baseline captures
those features. No feature-specific findings, HU measurements or temporal growth
claims should be fabricated from the current candidate map. Staging, treatment
and pathology are outside the original phase-one scope.

## Exact next actions

1. Open the new report locally and verify slider, candidate zoom, outline/off,
   opacity and focus behavior. Check k=0/96 (empty candidate views) and k=42
   (640 positive candidate voxels) with panels remaining synchronized.
2. Recover `output_fullres/scan.nii.gz` and `scan.npz` from the old successful
   Colab run if available. Otherwise run the revised optional-output notebook on
   authorized GPU compute to obtain actual model segmentation/probabilities.
3. Confirm access to an appropriate test set or document the data-access blocker.
   Continue implementing unblocked requirements rather than inventing clinical
   fields, labels, thresholds or performance numbers.
4. Plan segmentation/localization/explanation work only once the exact required
   outputs and their validation criteria are confirmed.

No new training, model download, dataset batch download or repeated inference was
performed in the 2026-11-04 usability/reliability milestone.
