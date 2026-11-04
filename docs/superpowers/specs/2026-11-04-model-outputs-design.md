# Milestone 5: complete model-output contract and candidate geometry

The original private statement was read locally on 2026-11-04 after user upload.
Phase-one outputs include a risk score, region location/size, segmentation and
heatmap. Do not commit the original source. Keep prior pretrained/no-training
constraints; referenced alternative models/tools are suggestions, not install
instructions. Clinical validation cannot be inferred from the software pilot.

## Architecture and acceptance

- Optional GPU runner export preserves stage-2 predicted label-1 segmentation
  and raw class-1 probabilities, pasted into original geometry using verified
  exclusive crop coordinates. This changes exported products, not inference,
  saved plans, model weights, thresholding or official candidate postprocessing.
- Validate crop grid, dimensions, scalar labels/range, available memory, full
  physical grid and on-disk voxels. Zero outside the crop means not evaluated
  there, not a full-volume raw probability estimate. Record this explicitly.
- Include hashes and semantics in run metadata. Existing bundles remain valid;
  absent extras stay unavailable. Import optional outputs only as a complete,
  hash-verified pair. Never reconstruct raw probabilities from candidate scores.
- Local region measurements use 26-connected positive candidate-map support.
  Report voxel/world bounds, centroid, extents and support volume as *candidate*
  geometry, not confirmed tumor size/segmentation. Preserve source hashes and
  model score; anatomical head/body/tail remains unassigned.
- No smooth/attribution heatmap is fabricated. Raw model class probabilities
  can support an explicitly labeled uncalibrated output heatmap in a later
  fresh GPU run/import; this does not satisfy validated decision attribution.

Tests use small rotated/reflected/translated anisotropic synthetic crops and
separate disconnected candidates. Check placement and RAS/LPS coordinates,
range/label/grid failures, pair/hash tampering, old bundles and unavailable
states. Real case verifies candidate geometry only; new model-output export
must remain marked GPU-unexecuted until actual model artifacts are obtained.

## Tasks

- [x] Regression tests for crop restoration and native output semantics.
- [x] Optional runner export and backward-compatible checked import.
- [x] Candidate geometry and explicit report availability fields.
- [x] Reconcile audit with original requirements; document actual data/GPU gates.
- [x] Run checks/review; commit verified source and checkpoint exact next action.
  Final delivery push/head verification is recorded in root PROGRESS.md.
