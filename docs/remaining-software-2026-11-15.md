# Remaining phase-one software and evidence gates

The accepted two-case research demos remain intact. This extension adds lesion
matching/FROC, explicit external anatomical subregion integration and genuine
input-occlusion explanation support. None of these changes trains a network or
turns the two examples into independent clinical validation.

## Explicit anatomy, not image-coordinate guesses

PANORAMA has no head/body/tail output. The report accepts an external native-grid
NIfTI mask with IDs 0=outside, 1=head, 2=body, 3=tail. Supply both
`--anatomy-mask` and `--anatomy-provenance` to report/demo. Provenance is JSON:

```json
{
  "schema_version": 1,
  "source_ct_sha256": "SHA256_OF_EXACT_ORIGINAL_CT",
  "mask_sha256": "SHA256_OF_SUBREGION_NIFTI",
  "labels": {"1": "head", "2": "body", "3": "tail"},
  "source_type": "expert-annotation",
  "method": "Describe how these actual labels were obtained",
  "review_status": "reviewed",
  "reviewer_code": "DEIDENTIFIED_REVIEWER_CODE"
}
```

An external pretrained model is also supported as `source_type=external-model`;
use `review_status=unreviewed` until actually reviewed. These declarations are
traceability, not independent proof of correctness. Never fill them using the
CT's left/right position or a source tumor annotation. The report retains mixed
head/body/tail overlap, uncovered voxels and partial coverage. There is currently
no genuine reviewed subregion mask for either demo case.

## Signed input-occlusion explanation

The GPU-only `mirai_ct.panorama_explain` command reuses a successful run's saved
crop, multiclass labels, raw probabilities and already verified checkpoints.
It does not modify the original run or model weights. It checks original CT
export/crop identity, native geometry, bundled products, source pins, environment
and all five folds. It repeats two unchanged-input controls then eight input block ablations
using all five folds/default TTA. The fixed target is mean class-1 probability
over the original predicted class-1 voxels. Version 2 uses the explicit control policy below; ten passes may take considerably longer than the
original inference. The genuine second-case V2 run is now complete; its eight
block passes took about 124–127 seconds each, excluding controls/setup.

Each block replaces input with stored intensity 50; HU calibration is still
unresolved. A positive score drop means that intervention reduced the target;
negative values mean it increased the target. These are coarse conditional input
sensitivities. They are not Grad-CAM, calibrated probability, a causal explanation
or an explanation of stage-1 crop selection/the full final scan score. Blank
regions are untested. Display uses one symmetric signed scale per case, with
actual differences on the colorbar.

`explanation.json` is atomically journaled after each completed pass. Rerunning an
identical job resumes it; a different CT, weights, code identity or configuration
is refused. A Linux process lock prevents duplicate jobs and is automatically
released if the process exits. A browser reconnect alone is not an exited job.
No torch/CUDA or model installation is needed locally. The existing Colab source
is kept separate from any new tool checkout.

On the GPU host, using the checked source for this extension:

```bash
/content/mirai-panorama/gpu-env/bin/python -m mirai_ct.panorama_explain --root /content/mirai-panorama --baseline /content/mirai-panorama/baseline --run-dir /content/mirai-panorama/run-20261115-124314 --input /content/mirai-panorama/input-cptac-pilot-01 --output /content/mirai-panorama/explanation-cptac-pilot-01
```

Then use `--explanation PATH_TO_DOWNLOADED_explanation.json` with the existing
report/demo command and a fresh output folder. Local import checks the original
run/model identity, fixed-target voxels and exact native probability bytes before
showing attribution available. Missing or incomplete evidence remains unavailable.
Actual GPU acceptance is separate from fake-network/API/arithmetic tests.

## Lesion-level comparison

`python -m mirai_ct.lesion_evaluation --spec lesions.local.json --output NEW_FOLDER`
uses an ignored local JSON spec with `min_iou` and `cases`. Each case needs
manifest, case_id, predictions (validated import), patient_key, reference_label,
reference_description, overlap_status and overlap_evidence. Paths are relative
to the spec. Repeated patients/case IDs/source CTs are refused. Connected positive
candidate support is matched to explicit reference components using 26-connectivity
and maximum-cardinality one-to-one IoU matching at each score threshold. Score
ties enter together. An all-excluded point is included; no reference lesions
makes lesion sensitivity undefined. Minimum IoU is declared before analysis.
This policy is explicit, not asserted identical to the official challenge metric.

The two existing CTs each have one reference component and one overlapping
candidate at min_iou=0.1. Their source-reference candidate IoUs are 0.597830 and
0.641187. This is an exploratory localization check with no independent negative
cohort; it establishes neither clinical sensitivity nor specificity. Actual
model-mask voxel misses remain visible in the original per-case Dice reports.

## Completion status

Implemented/tested software is distinct from received real evidence:

| Requirement | Current state |
|---|---|
| DICOM/NIfTI intake, pretrained PANORAMA, score/location/mask | Genuine two-case demos accepted |
| Native mask size and source overlap | Genuine two-case counts checked |
| Lesion matching/FROC machinery | Tested; exploratory two-case calculation performed |
| Classification ROC/sensitivity/specificity machinery | Tested; requires explicit diagnosis and threshold declarations |
| Anatomical subregion integration | Tested; genuine external labels/review still required |
| Signed occlusion export/import/reporting | Genuine CPTAC V2 controls + eight blocks accepted; interactive report included |
| Independent clinical validation and expert error review | Requires audited positive/negative cases and qualified review |

Synthetic CTs and fake networks can test software, not fill clinical evaluation
or explanation evidence gaps. The original private statement is not published.

## Numerical-control revision after actual GPU check

The first real explanation attempt (v1) stopped safely: the repeated prediction's
largest voxel difference was 0.0019400716, exceeding its 0.001 rule. Inputs,
weights, numerical versions and original native products passed identity checks.
That attempt did not produce an accepted explanation. Floating-point GPU results
need not be bitwise identical; see [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)
and [numerical accuracy](https://docs.pytorch.org/docs/stable/notes/numerical_accuracy.html).
This does not by itself prove that a particular discrepancy is harmless.

V2 adds two unchanged-input controls before ablation. Each control vs the saved
map, and the controls vs one another, must meet *all* predeclared engineering
bounds: max absolute difference <=0.005, whole-crop mean absolute difference
<=0.0001, fixed-lesion-target mean absolute voxel difference <=0.0005, and
absolute fixed-target mean-score difference <=0.0001. These are our software
acceptance bounds for approximate conditional input sensitivity, not published
clinical tolerances. Compared with v1, a sparse outlier has more allowance but
systematic/target drift has additional strict checks. Do not keep raising bounds
to force a successful result if this protocol fails.

Effects use the mean of the two fresh control scores. A control-resolution floor
is max(0.0001, control-score difference, control-mean vs saved-target difference).
All signed block effects remain in the table; only effects exceeding this floor
are colored. This is not a confidence interval or statistical significance test.
Unchanged-control metrics are journaled even if acceptance fails. Original
predictions are preserved; no alteration is presented as the original model run.

## Genuine evidence received and review delivery

V2 completed on the existing Colab run using source f49a766. Downloaded JSON
SHA256: 564741aca5474264b22d91cd052baa5c70e79cd89f6597ae1b43a95083bed066.
Local loader checked the exact CT, original model/run hashes, native geometry,
39,059 target voxels and original probability bytes. The unchanged controls
agreed exactly. Each control vs saved map: max error 0.00191924, mean error
0.000000716680, target voxel MAE 0.0000591867, target-mean error 0.000000962436.
These pass the declared V2 bounds; they do not identify the cause of the original
numerical-path difference. Baseline target 0.8039246523; signed effects span
0.0968189258..0.5830156352, above the 0.0001 resolution floor. Original inference
outputs remain unchanged. No source annotation was used for these experiments.

The polished offline entry point and presentation instructions are in
[the review guide](review-2026-11-16.md). Both CTs retain their original numeric
outputs. The first case has no explanation; neither case has reviewed subregion
labels. The [lead handoff](lead-handoff-2026-11-15.md) lists the deferred inputs.
