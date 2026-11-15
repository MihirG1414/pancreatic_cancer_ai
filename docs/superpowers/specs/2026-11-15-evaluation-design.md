# Measured demonstration and evaluation readiness

## Specification

Complete the next locally executable phase-one requirement: quantitative
comparison of genuine imported outputs with explicitly selected reference labels.
Keep the pretrained PANORAMA baseline and original scan geometry. The user is
running the prepared T4 notebook to supply missing segmentation/probabilities.
Existing candidate maps cannot recreate those products.

## Architecture and risks

- A new CPU `mirai_ct.evaluation` CLI reads validated imports and existing labels.
  Compare native planes without resampling, full-volume arrays or new dependencies.
- Reference label and description are explicit, because MSD label 2 is a tumor
  annotation, not necessarily PDAC. Hash the reference and imported products.
- Report positive candidate-support overlap separately from binary model-mask
  Dice/IoU. If the actual model mask is absent, segmentation metrics are absent.
- Both-empty masks have undefined overlap (JSON null), rather than a fabricated
  perfect tumor score. Empty references do not imply a healthy patient.
- Cohort score metrics require explicit binary PDAC references, patient keys,
  reference provenance and overlap evidence. Reject duplicate patients, case IDs
  and CT hashes. No PDAC label is inferred from a segmentation mask or score.
- A supplied threshold is an operating point, not a validated clinical cutoff.
  ROC-AUC uses pairwise ranking with half credit for ties. Missing classes make
  class-specific rates/AUC undefined. Mark results exploratory if independence
  is unknown or overlap is known. Even verified independence is not itself
  clinical validation or a guarantee of an adequate study design/sample size.
- Public-data research begins with bounded metadata. CPTAC-PDA has heterogeneous
  series and annotation types; choose CT and compatible timing/phase explicitly.
  Negative findings in cancer follow-up are not automatically non-PDAC controls.

## Plan and tasks

1. Add failing tests for exact overlap counts, empty masks, geometry/label/value
   rejection, genuine-import integration, missing model masks, ties/one class,
   duplicate-patient/scan rejection and explicit label semantics.
2. Implement streaming comparison and case/cohort JSON plus readable HTML output.
3. Run the real existing case; record candidate-support comparison without
   presenting it as model-segmentation accuracy or clinical generalization.
4. Inspect official public-data metadata and record a bounded, reproducible
   selection/access route. Do not download entire collections or infer phase.
5. Add demo/completion handoff, run appropriate tests/lint, inspect generated
   artifacts, update PROGRESS.md, commit/push and check the actual remote head.

## Acceptance and outstanding gates

Arithmetic and guardrail regressions pass; real comparison preserves all source
hashes; output clearly states unavailable model segmentation and unresolved
independence. Genuine new GPU products, anatomical head/body/tail, decision
attribution, an independently audited positive/negative cohort, clinical review
and actual browser verification remain separate gates unless evidence arrives.

## Research-driven implementation extension

The metadata identified one pretreatment CT with an explicitly named PV series
and matching primary-pancreas RTSTRUCT. Its API-reported size was bounded before
download. Add conventional single-frame DICOM intake to enable this different
public dataset: refuse mixed series, duplicate slices, irregular spacing, gantry
tilt, inconsistent orientations/scaling and unsupported frames; preserve native
positions, intensities and RAS/LPS geometry. Check memory before allocation and
verify every original and saved plane. No RTSTRUCT rasterization is included in
this step; that reference remains a DICOM annotation, never a fabricated mask.

Add a small demo command orchestrating validated ZIP extraction/import, report,
explicit reference comparison and a report-only ZIP. Limit file count/size and
reject traversal/duplicate entries. Old bundles remain usable for demonstrations;
an explicit complete-products flag rejects them for the expanded output gate.
