# Remaining phase-one outputs and evaluation

## Specification and scope

Keep the working pretrained five-fold PANORAMA inference and native CTs. Complete
software for explainability, explicitly sourced anatomical subregion location
and lesion-level evaluation. Do not train or silently add another model. The
private statement requires evidence for a flagged region, anatomical location,
size, score and quantitative evaluation; staging/treatment remain outside scope.

## Evidence and architecture

The [official label legend](https://github.com/DIAGNijmegen/panorama_labels#annotations)
has no head/body/tail labels. [Pinned baseline code](https://github.com/DIAGNijmegen/PANORAMA_baseline/blob/d08f2356fa70d9460881fec0aedba4ebd1566c7e/src/data_utils.py)
uses class 1 probabilities, pancreatic mask dilation and lesion extraction.
Saved class probabilities do not supply [Grad-CAM gradients](https://arxiv.org/abs/1610.02391).

1. Anatomy accepts an explicit native-grid label mask (1=head, 2=body, 3=tail)
   with bounded provenance binding exact source CT, mask hash, label meanings,
   reviewer/method and clinical-review status. Quantify actual model-mask overlap
   with subregions and outside support. Report mixed/outside/unassigned rather
   than force a single label. No coordinates-to-anatomy heuristic. An externally
   predicted mask remains unvalidated; reviewed labels are not PANORAMA outputs.
2. A separate Colab sidecar reuses a completed run, original saved crop/labels,
   native CT and already verified weights. Full five-fold/default-TTA stage-2
   predictor repeats two unchanged-input controls then eight nonoverlapping input block occlusions
   around the model-selected lesion with margin. Fixed target is mean class-1
   probability over the original predicted class-1 voxels. Baseline probabilities
   must reproduce the saved output within tolerance before any attribution is
   accepted. Score decreases/increases are signed, not clipped or normalized
   into probability. Store block effects, geometry, hashes, model identity,
   target, fill value, scope and completed-pass evidence. No source annotations
   enter the sidecar. It explains this fixed stage-2 target, not the complete
   stage-1/candidate-extraction/scan-score pipeline or a causal diagnosis.
3. Resume only hash-identical jobs; retain per-block results after each genuine
   call. Zero elsewhere means not evaluated, never no model influence. Native
   block support is explicit. No whole local GPU dependencies or weight download.
4. Local reports accept a complete checked sidecar, keep signed sensitivity
   separate from raw probability, render it with a fixed signed scale and retain
   no-attribution state for old bundles. Optional anatomy/explanation arguments
   flow through the report/demo CLI; never overwrite accepted report directories.
5. Lesion-level analysis uses 26-connected reference/prediction components,
   candidate peak scores, explicit minimum IoU, maximum-cardinality one-to-one
   matching at each unique score threshold (ties admitted together), plus an
   all-excluded point. Count unmatched candidates as false positives per scan.
   No reference lesions makes sensitivity undefined. This explicit matching
   policy is not asserted identical to the PANORAMA challenge evaluator.
   Keep diagnosis/independence audit separate; empty lesion masks do not establish
   non-PDAC. Exploratory two-reference examples are not a validation cohort.

## Risks and acceptance tests

Native axis flips/rotation/spacing, mismatched source/model hashes, unexpected
labels/nonfinite effects, incomplete/replayed blocks, duplicate cases/patients,
unsupported target/pins, absent empty masks and outside anatomy must fail or be
explicitly unavailable. Synthetic known-score tests verify sign, coverage and
fixed target; test greedy-matching counterexamples, ties, duplicate detections,
negatives and zero-reference cases. Actual GPU passes are a separate acceptance
gate; local arithmetic tests do not demonstrate nnU-Net execution or faithfulness.

## Tasks

- [x] Add failing anatomy/occlusion/lesion-matching tests.
- [x] Implement small typed CPU modules and bounded GPU-only adapter.
- [x] Integrate optional reviewed anatomy/explanation into report and demo.
- [x] Add Colab continuation using existing environment/run, with explicit pins.
- [x] Exercise exploratory lesion matching on both genuine existing cases.
- [ ] Full software checks, artifact/browser review, completion matrix/handoff.
- [x] Receive genuine explanation products and verify them before claiming them.
- [ ] Independent cohort and expert review before clinical completion claims.

## V2 numerical controls (actual V1 rejection)

V1's real GPU check rejected max drift 0.0019400716. V2 is a distinct method with
two unchanged-input controls, four fixed whole-map/target reproduction bounds
and a control-resolution floor. Exact bounds, rationale and interpretation are
in [the software handoff](../../remaining-software-2026-11-15.md). Preserve the
failed V1 log; do not relabel it successful. All V2 controls must pass before
accepting any block sensitivity; this is engineering qualification, not clinical
validation. V2 completed and passed local source/model/native target/probability
checks; the genuine second-case report now includes all eight signed effects.

Latest user scope defers clinical cohort/expert review because lead is unavailable
before the 16 November review. Finish all independent software/demo checks and
state those deferred requirements explicitly. No head/body/tail guess is allowed.
