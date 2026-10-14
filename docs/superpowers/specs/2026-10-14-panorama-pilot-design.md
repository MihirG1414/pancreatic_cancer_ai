# Milestone 3: PANORAMA one-case integration

Scope authorized by the user's detailed Milestone 3 request on 2026-10-14.
Use the original checkout/environment and public sample; preserve the modified
inspection notebook. No training, laptop CUDA, or laptop model downloads.

## Architecture and alternatives

Use a streamed derived MHA export, a separate Docker-free GPU subprocess runner,
and a validated local prediction import consumed by the existing report.
Docker in Colab is unsupported by our workflow; copying the entire container
entry point would duplicate baseline behavior. Instead call the pinned official
data_utils functions and the same nnUNetv2_predict configurations. Keep both
stages and all five folds. Explicitly document path/worker adaptations.

Export accepts only the manifest CT; never opens its annotation. Translate the
selected NIfTI RAS affine (known spatial units converted to mm) to SimpleITK LPS
by negating world X/Y, without changing voxel order or interpolating. Reject
ambiguous transforms and shear. Stream float32 scaled planes into uncompressed
MHA; independently verify with optional SimpleITK. Record origin, direction,
spacing, voxel-center and voxel-edge corners, intensity samples and hashes.
Check memory/disk before allocating. Unknown phase, HU and clinical fields stay
unknown; clinical nulls are explicitly a smoke-test adaptation because the
baseline prints those fields and does not use them for prediction.

The Colab notebook checks NVIDIA GPU/free VRAM, host RAM/disk and user permission
before downloads, pins baseline/nnU-Net and build-log numerical dependencies,
checks Zenodo-published MD5 plus records SHA256, validates all ten checkpoints,
runs original preprocessing/crop/postprocessing, fails on empty pancreas/invalid
crop/missing outputs, and writes a hashed provenance bundle. Model compatibility
is only established after a genuine GPU run; successful local tests do not prove it.

Import checks source CT hash, exported input hash/geometry, bundle file hashes,
successful run provenance, finite detection values in [0,1], scalar JSON score
and agreement with map maximum. Convert the aligned MHA to a derived NIfTI for
the existing lazy viewer. Reject unexplained physical mismatch; no silent
resampling. Report uses separate annotation and detection panels, fixed [0,1]
color scale, uncalibrated score, provenance and explicit unavailable state.

## Risks and acceptance

Free Colab allocation/VRAM is not guaranteed. Conservative preparation gates
are operating policy, not claimed baseline minimums. Weight license CC BY-NC 4.0
requires permitted use; MSD is CC BY-SA 4.0 and overlap is unresolved. Public
sample is a software smoke test only; no clinical suitability or accuracy claim.
Tests must cover rotated/reflected anisotropic geometry, nonzero translation,
units, scaling, shear/ambiguous transforms, tampering, wrong CT, map alignment,
invalid scores, missing outputs, and unavailable prediction reports.

Delivery: commands + cleared notebook + demo guide + evidence in PROGRESS.md;
specific staged files, meaningful commits, existing-branch push/remote check.
GPU-dependent work stays pending if no authenticated runtime is accessible.
