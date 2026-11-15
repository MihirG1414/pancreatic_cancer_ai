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
and all five folds. It repeats the baseline then eight input block ablations
using all five folds/default TTA. The fixed target is mean class-1 probability
over the original predicted class-1 voxels. A baseline discrepancy >0.001 in any
voxel refuses acceptance. Nine passes may take considerably longer than the
original inference; actual duration is not yet measured.

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
| Signed occlusion export/import/reporting | Locally tested; real GPU acceptance pending |
| Independent clinical validation and expert error review | Requires audited positive/negative cases and qualified review |

Synthetic CTs and fake networks can test software, not fill clinical evaluation
or explanation evidence gaps. The original private statement is not published.
