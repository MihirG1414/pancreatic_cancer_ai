# Reference contour preparation and research findings summary

## Specification and same-day scope

Continue CPU work while the user runs the prepared PANORAMA GPU notebook. Convert
the existing CPTAC source RTSTRUCT to an explicit reference mask, then improve
the per-scan report summary and actual model-mask measurements. These tasks use
no new network or weights. A research demo is the day's target; independent
clinical validation is not inferred from a deadline or software completion.

## Architecture and risks

- Optional `pydicom==3.0.1` parses conventional CT metadata and RTSTRUCT only.
  Existing NumPy/NiBabel implement bounded polygon rasterization/native output;
  no SciPy, segmentation framework or GPU dependency is introduced locally.
- Explicit ROI number and meaning are mandatory. Check RTSTRUCT modality and
  SOP class, selected ROI, FrameOfReferenceUID, referenced CT series and each
  contour's SOP image linkage, position, finite coplanar points and geometry.
- Map LPS millimetres through the original CT affine, not array shape/filename
  guesses. Reject out-of-grid, missing-plane, open/nonplanar, mixed-XOR and
  unsupported slab/interpolation cases. Never interpolate unlabeled slices.
- Rasterization samples original voxel centers. Polygon-boundary centers are
  included; combine CLOSED_PLANAR polygons by union and CLOSEDPLANAR_XOR by XOR,
  following DICOM C.8.8.6. A documented derived raster is not the original expert
  volume and is not a clinical diagnosis or a model output.
- Preserve input hashes and record source CT/RTSTRUCT/DICOM links and raster
  rules locally. Refuse overwrite, verify saved native voxels and geometry, and
  keep medical data/identifiers/outputs out of Git.
- Findings summary uses actual imported score/map and measured geometry. Missing
  model masks remain missing. When a real mask exists, report its native volume
  and bounding extent as unvalidated model measurements, never as clinical
  diameter, reference size or confidence. Do not invent head/body/tail.

## Plan, tasks and checks

1. Inspect the existing small RTSTRUCT after installing only the optional parser.
2. Add failing analytical rasterization and source-linkage tests; implement
   native mask conversion with memory/size/no-overwrite guards.
3. Convert this real reference and inspect all three native overlay views; check
   original CT/export hashes unchanged. Keep the existing input export, since
   inference never uses the annotation.
4. Add tested summary/actual-mask measures to JSON and HTML, preserving explicit
   absence/empty-map states and reference/model distinction.
5. Generate the current genuine demo, run relevant/full software checks, document
   current artifacts and acceptance gates, commit/push and check remote head.

## External gates

Await the genuine extended Colab ZIP, run second-case inference on that runtime,
review contour/reference alignment clinically, audit positive/negative evaluation
cases, implement/test anatomical localization and decision attribution, complete
FROC/error review and actual browser acceptance. No full-project completion claim
until the applicable deliverables are supported by evidence.
