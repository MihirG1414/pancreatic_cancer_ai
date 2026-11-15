# Phase-one completion and demo checkpoint — 15 November 2026

**Earlier milestone-6 snapshot.** Later on the same day, actual GPU model products
were received and checked and the second CT's reference mask was converted.
Use [the latest demo checkpoint](demo-ready-2026-11-15.md) for current results,
artifact paths and remaining requirements; historical pending items below are
superseded where that checkpoint records completion.

## What works

The project already has a real pretrained PANORAMA inference result, not just a
viewer or synthetic prediction. Its two stages and five folds ran on a Colab T4
in approximately 168 seconds (excluding installation/download). No new training
is needed to assemble the demonstration.

| Pipeline requirement | Current evidence | Remaining work |
|---|---|---|
| CT intake | Native NIfTI inspection/export; now conventional DICOM intake, verified on one additional public CT | More input diversity; compatible phase/intensity review |
| Pancreas isolation | Official pretrained first stage ran in genuine pilot | Optional export/display of that intermediate, if required |
| Candidate detection | Genuine map and connected-region coordinates/extents | Lesion-level matching and FROC on suitable references |
| Scan score | Genuine maximum candidate score 0.999536395 | Independent case-score evaluation and a justified operating point; calibration if claiming probabilities |
| Tumor segmentation | Native class-1 export/import implemented and synthetic-tested | Fresh genuine output from current Colab notebook; reference comparison |
| Heatmap/explanation | Raw-probability export/import/plots implemented | Genuine probability output; decision attribution remains separate work |
| Location | Native voxel bounds and RAS/LPS centroids | Validated head/body/tail localization |
| Report/demo | Interactive offline CT/candidate/annotation report; one-command ZIP-to-report builder | Actual browser acceptance checks, genuine extra model views |
| Evaluation | Native overlap evaluator; explicit patient-separated PDAC cohort AUC/sensitivity/specificity evaluator | Independently audited positive/negative cases, reference masks, FROC, visual error review and clinical review |

A working software prototype and a clinically validated screening model are
different deliverables. This checkpoint completes further software/demo steps;
it does not establish clinical accuracy or full problem-statement completion.

## Demonstration available now

Open `outputs/panorama-demo-20261115/report/index.html`. Share the entire report
folder or `outputs/panorama-demo-20261115/demo-report.zip` (about 9.4 MiB).
The source CT, derived medical volumes and inference logs are not in the
report-only ZIP; its PNG display copies still contain medical-image information.
Inputs and generated artifacts remain outside Git.

1. Explain that this is a research screening output for one public CT.
2. Show the synchronized slice viewer and jump to the largest candidate section,
   native k=42. Navigate through adjacent slices to show its 3D extent.
3. Compare the existing annotation and PANORAMA candidate in separate panels.
4. Show coordinates/extents and the uncalibrated score. Do not call the score
   a 99.95% probability of cancer or the candidate box a measured tumor diameter.
5. Show the new reference-comparison table and the explicit missing-output section.

Manual browser checks: synchronized panels at k=0, 42 and 96; focus button;
previous/next; candidate zoom; fill/outline/off; opacity; browser reload from a
local extracted report directory. Automated JS checks and PNG inspection do not
replace this browser acceptance check.

## What the new measured result says

For the existing MSD case, reference label 2 contains 3,521 voxels; positive
candidate support contains 5,168; intersection is 3,251. Candidate-support Dice
is **0.74830245**, IoU **0.59783008**. This is overlap of a postprocessed detection
region with an existing tumor annotation. It is **not** model-segmentation Dice,
independent generalization, case sensitivity or proof of PDAC diagnosis.

Actual class-1 segmentation metrics remain unavailable until a genuine extended
bundle arrives. MSD's tumor label does not by itself confirm PDAC histology.
The evaluator records hashes, exact label semantics and missing values in JSON;
both-empty overlap is null, not a fictitious perfect tumor score.

## Generate the report from a Colab ZIP

Use the existing environment. These commands preserve all original artifacts;
choose a new output directory for each run. After the new Colab download, use
its actual path and add `--require-model-products` to enforce the extended gate.

```powershell
.\.venv\Scripts\python.exe -m mirai_ct.demo --manifest .\cases.local.csv --case-id pancreas_290 --input-export 'C:\Users\Mihir1\Downloads\Telegram Desktop' --bundle 'C:\Users\Mihir1\Downloads\panorama-output-with-model-products.zip' --require-model-products --reference-label 2 --reference-description 'MSD Task07 tumor annotation label 2; PDAC status and training independence unverified' --output .\outputs\panorama-demo-with-products
```

This validates source/output checksums and native geometry, imports the actual
products, generates the offline report/reference comparison, and creates
`demo-report.zip`. It performs no model inference and cannot reconstruct absent
intermediates. A failed build leaves a failure record; use a fresh folder after
correcting the cause. Failures after bundle extraction/import begins retain
diagnostic artifacts; ZIP preflight rejection can occur before a folder is made.

For overlap comparison without rebuilding images:

```powershell
.\.venv\Scripts\python.exe -m mirai_ct.evaluation case --manifest .\cases.local.csv --case-id pancreas_290 --predictions .\outputs\panorama-import-20261028 --reference-label 2 --reference-description 'MSD Task07 existing tumor annotation; PDAC status unverified' --output .\outputs\comparison-new
```

For cohort score evaluation, use `python -m mirai_ct.evaluation cohort
--specification <local-json> --output <new-folder>`. The local JSON contains
`threshold`, `threshold_source`, and `cases`. Each case requires paths `manifest`
and `predictions` (relative to the JSON), `case_id`, a de-identified `patient_key`,
explicit integer `pdac_label` 0/1, `diagnosis_reference`, `overlap_status`
(`unknown`, `known-overlap`, `verified-independent`) and `overlap_evidence`.
Optional `reference_label` and `reference_description` enable mask comparisons.
One scan per patient; repeated patient keys, case IDs and source CT hashes fail.
One-class AUC and unavailable class-specific rates are null. Unknown/known
overlap marks the result exploratory. The software cannot audit a declaration
of independence or establish that a study is clinically adequate.

## Public data selected for the next model run

See [the bounded public-data record](public-ct-pilot-2026-11-15.md). One additional
real CPTAC-PDA CT and its matching RTSTRUCT have been downloaded and checked,
not an entire dataset. Its native NIfTI is
`data/CPTAC-PDA-pilot/native/ct.nii.gz`; manifest `cases.cptac.local.csv`.
Inspection-only report: `outputs/cptac-inspection-20261115/index.html`.
No model has run on this CT yet. The RTSTRUCT is not yet rasterized into a
reference mask, and training independence/phase are not established.

The completed second-case Colab input is
`outputs/cptac-pilot-input-20261115-ready/`. After downloading the current case's
successful ZIP, keep the Colab GPU environment and weights. In a new code cell:

```python
INPUT = ROOT / "input-cptac-pilot-01"
```

Then rerun only cells 5, 7, 8 and 9, in that order. Upload the three files from
that local `-ready` folder when cell 5 asks. Keep `EXPORT_MODEL_OUTPUTS=True` and
`SOFTWARE_SMOKE_TEST=True`. The new INPUT path must not already contain another
case. Cell 7 creates a new run directory. Cell 9 downloads a separate ZIP; rename
it `panorama-cptac-pilot-01.zip` locally to keep the cases distinct. This is a
pending user GPU action, not an executed or tested second-case inference.

Once it is available, build its demo using `--manifest cases.cptac.local.csv`,
`--case-id cptac_pilot_01`, `--input-export outputs/cptac-pilot-input-20261115-ready`,
its actual ZIP path and `--require-model-products`. Leave out reference-label
options until a verified native voxel reference exists. Do not use the MSD
annotation or a dataset-diagnosis assumption for this new CT.

## Exact next steps

1. Finish the existing nine-cell T4 notebook with `EXPORT_MODEL_OUTPUTS=True`.
   The earlier ZIP dated 28 October IST was rechecked on 15 November: all four
   recorded checksums match, but it has no model-output pair. Keep it as evidence.
2. Download the new ZIP immediately and copy it to persistent storage. Optionally
   use Colab's Google Drive mount to copy the completed archive after success;
   `/content` is temporary. Do not treat a restarted runtime as saved storage.
3. Run the one-command demo builder with `--require-model-products`, inspect the
   actual segmentation/probability views and compare the actual mask with label 2.
4. Run the same pretrained baseline on the prepared CPTAC CT, one case at a time.
   Reuse the Colab environment/weights, export a new CT-only input, and use a new
   run directory; never silently reuse the previous case's input folder.
5. Add verified RTSTRUCT-to-native-mask conversion and inspect its alignment;
   audit independence and recruit suitable non-PDAC controls before cohort metrics.
6. Complete anatomical localization and a tested decision-attribution approach,
   followed by expert/visual review and a rehearsed demo.

Do not train a new network or download whole collections to solve these
integration/evidence gaps. T4 has already worked for the first case; resource
needs of this larger second case must be measured when it is actually run.
