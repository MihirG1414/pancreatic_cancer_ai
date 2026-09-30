# Milestone 2 demonstration: CPU dataset annotation report

Open native PowerShell in the project root. Use the existing `.venv` and ignored `cases.local.csv`; no download or server is needed. Choose a **new** output directory for each run:

```powershell
$reportDir = ".\outputs\pancreas-290-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
.\.venv\Scripts\python.exe -m mirai_ct.report --manifest .\cases.local.csv --case-id pancreas_290 --output $reportDir
Invoke-Item -LiteralPath "$reportDir\index.html"
```

The browser report contains original CT dimensions, spacing, orientation, qform/sform codes and geometry warnings. It checks the supplied mask against CT shape, units, spacing and affine. It counts each **dataset annotation** label and shows an inclusive, zero-based `(i, j, k)` bounding box in native NIfTI voxel coordinates. Volumes use voxel count times the absolute affine determinant, with mm³ and mL shown only when spatial units are known. Label names 0 background, 1 pancreas and 2 cancer come from the locally retrieved official MSD Task07 `dataset.json`; unknown IDs are left uninterpreted. These are supplied annotation measurements, **not** model predictions or diagnosis.

Three PNGs show native CT axis planes with the existing annotation overlay. The command centers views on label 2 when available, otherwise another positive label or the scan center. The views retain original voxel geometry; axes and direction letters are labeled. The saved `index.html` and `axis-*.png` live in ignored `outputs/`. They can be opened locally without an application server. Use another `--output` name when rerunning; the command refuses to replace an existing directory.

For the existing public sample, the 2026-09-30 run read a 512 × 512 × 97 RAS scan at approximately 0.916 × 0.916 × 2.5 mm, with matching mask geometry and no geometry warnings. Annotation label 1 contained 29,162 voxels (61.1735 mL), bounded by `[149, 248, 26]`–`[280, 309, 59]`. Label 2 contained 3,521 voxels (7.3860 mL), bounded by `[246, 275, 37]`–`[283, 303, 44]`. The label-1 count excludes label-2 voxels; it is not a combined pancreas-plus-lesion volume. The three chosen slice indices were 264, 289 and 40; each image visibly showed the existing annotation. Counts include 25,395,285 background voxels and total 25,427,968, matching scan dimensions. The report is a software/data inspection of **one** provided public case, not a performance measurement.

The [PANORAMA integration plan](panorama-inference-plan.md) documents the next GPU phase. The baseline requires a permitted GPU environment, licensed weights and a venous CT input conversion/geometry check. Its detection map and uncalibrated score still need a real one-case run. Independent evaluation and separate explanation/risk calibration require further work and source-overlap checks.
