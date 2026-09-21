# Mirai / Rises.io: milestone 1 specification

Source: the supplied `DOC-20260829-WA0025.md`, read on 2026-09-22.
The original supplied document stays local. This specification summarizes the
authorized software work without republishing that document.

## Scope and acceptance

Build CPU-only NIfTI intake and inspection on native Windows. No training,
inference, predictions, clinical claims, CUDA, or model downloads. Later work
will use the pretrained official PANORAMA baseline, subject to separate compute
and evaluation planning. The statement's resampling/cropping steps are deferred;
milestone 1 must preserve original voxel data and geometry.

1. Record OS, Python, RAM and disk measurements, including their date.
2. Create an isolated 64-bit Python environment and reproducible dependencies.
3. Load one `.nii` or `.nii.gz` CT at a time through NiBabel's array proxy.
4. Report dimensions, header spacing, affine spacing, spatial units, axis codes,
   affine and qform/sform codes without dumping identifying header strings.
5. Return only requested 2D slices; apply stored intensity scaling. Stream at most
   one contiguous 2D storage slab at a time when assembling other native planes.
   Do not call `get_fdata()` or materialize an entire proxy. Report memory snapshots.
6. Overlay an existing integer label mask only when shape, units, voxel spacing,
   and full voxel-to-world affine agree. Fail clearly on mismatch. Do not repair
   or resample it silently. Geometry agreement alone cannot prove patient identity.
7. Provide a notebook and a command line inspection entry point, with an empty
   CSV template and an ignored local case list. Resolve relative paths against
   the CSV's directory; require unique nonempty case IDs and dataset sources.
8. Validate with synthetic fixtures explicitly identified as software tests.
   Obtain and inspect one openly accessible real CT if a bounded single-case
   download is available. Otherwise record a blocked real-data gate and verified
   official access instructions. Never substitute synthetic data for real evidence.
9. Commit meaningful verified changes; push only to the user-selected remote.

## Architecture and alternatives

Use a small `src/mirai_ct` package: volume I/O and geometry, plotting, CSV parsing,
and CLI. The notebook calls the same tested functions. NiBabel + NumPy +
Matplotlib + psutil are sufficient. ipykernel enables VS Code notebooks;
nbclient/nbformat enable automated execution; pytest and Ruff check the code.

SimpleITK is a viable alternative but duplicates NIfTI support. A MONAI/PyTorch
application is premature and adds substantial disk/memory overhead. No web app,
database, widgets, DICOM conversion or new service is needed for this milestone.

Slices use native voxel axes with explicit direction labels and spacing-aware
aspect ratio. They are not implicitly advertised as anatomical axial/coronal/
sagittal views, especially for oblique acquisitions. The display transposes only
the 2D plane. Windowing changes display limits only. Labels retain numeric IDs;
their clinical meaning must come from dataset documentation.

## Resource risks and handling

Inspection found Windows 11 Home Single Language (10.0.26200), Ryzen 5 3500U,
5.95 GiB OS-visible RAM and about 0.55 GiB free at initial measurement. C: had
4.44 GiB free, D: about 458 GiB. Keep scans on D: and install without a pip cache.
Read slices serially and close figures. Compressed NIfTI may decompress earlier
bytes on repeated access, so manual slice selection is preferable to animation.
Code review found proxy slicing can read ahead into an entire volume for some
shapes; explicit bounded storage-plane reads prevent that hidden allocation.
Warn when available memory is low; reject oversized individual slice requests.

NIfTI is a container: it does not independently establish modality, CT contrast
phase, HU calibration or diagnosis. Preserve and report geometry uncertainties
(missing/conflicting transforms, unknown units, obliquity). Strict mask checks
can block questionable inputs; they must not be bypassed for a nicer picture.

## Verification and remaining gates

Unit tests cover compressed/uncompressed input, intensity scaling, geometry
mismatches, invalid input, native slice indexing, rendering and CSV validation.
Execute the notebook, inspect a rendered image manually, run Ruff and pip check.
Keep notebook outputs clear in Git; actual images, local paths and real case IDs
stay in ignored local reports/manifests. Clinical performance remains unevaluated.
