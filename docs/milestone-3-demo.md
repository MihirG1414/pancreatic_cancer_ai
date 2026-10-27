# Milestone 3 — PANORAMA integration and GPU pilot handoff

2026-10-28 continuation: the user completed both pretrained stages in Colab on
a Tesla T4. The received bundle records 167.6979 seconds and an uncalibrated
score of 0.999536395072937. On the new PC, the single public CT/annotation was
recovered with the bounded downloader; the CT and original MHA hashes match
the inference provenance. Local import and report generation passed. Open
`outputs/panorama-report-20261028/index.html` in this checkout; keep its six PNGs
beside it when sharing the report folder. See the current `PROGRESS.md` for
verification results and remaining limitations. The original handoff below is
historical; no second GPU run is needed for the existing report.

Runtime workarounds used in this pilot: remove only the identified untracked
baseline Python cache, set subprocess `ENV["PYTHONDONTWRITEBYTECODE"] = "1"`
and `ENV["MPLBACKEND"] = "Agg"`, and reload `RUN_DIR / "bundle/run.json"`
before checking download status if notebook variable `run` is undefined.
Permanent runner/notebook fixes remain separate follow-up work. The user's
saved Colab notebook already on the remote has executed outputs; it was
preserved during this reporting milestone, not cleared or recommitted.

Prepared/checked 2026-10-14 on the original Windows laptop. The executable local
integration and GPU notebook are implemented. **No real PANORAMA inference has
run in this session.** Free Colab requires the user to connect a runtime and run
the cells. Model compatibility, actual GPU memory/runtime and predictions remain
pending. Local tests use synthetic fixtures only.

## 1. Windows: verified input and optional IO dependency

Use PowerShell at this repository root and the existing `.venv`.
SimpleITK 2.4.0 is already installed in ignored `outputs/panorama-io`; skip the
install command in this checkout. For another checkout that lacks it:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-deps --no-cache-dir --only-binary=:all: --target .\outputs\panorama-io -r .\requirements-panorama-io.txt
```

Enable that optional directory for this PowerShell session:

```powershell
$env:PYTHONPATH = "$PWD\outputs\panorama-io;$PWD\src"
```

The real sample has already been exported to `outputs/milestone-3-input`.
It contains only `ct.mha`, `input-provenance.json`, and
`clinical-information-pancreatic-ct.json`. **Reuse those three files.**
For a new export, choose a fresh directory:

```powershell
$inputDir = ".\outputs\panorama-input-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
.\.venv\Scripts\python.exe -m mirai_ct.panorama_io --manifest .\cases.local.csv --case-id pancreas_290 --output $inputDir
```

Export reads only CT, never the manifest annotation. It streams scaled float32
planes into an uncompressed embedded MHA and verifies the derived file with
SimpleITK. No interpolation, crop, reorientation or source overwrite occurs.
NIfTI coordinates are RAS; SimpleITK coordinates are LPS: physical X and Y signs
change, native voxel order remains ijk (SimpleITK arrays are kji). Units are
converted to mm. Shear, unknown units and ambiguous transforms fail explicitly.
Both center corners (0 to size−1) and volume-edge corners (−0.5 to size−0.5)
are checked, with 27 representative scaled intensity samples.

Our verified result: 512×512×97; spacing approximately 0.916×0.916×2.5 mm;
zero measured corner/intensity sample error; original CT hash unchanged. RAM
checks run before conversion/read; memory snapshots are not peak guarantees.
Insufficient RAM gives a clear error: close unused apps or convert on the GPU
host. Keep original files and active notebook kernels.

Clinical age, sex, study date and scanner remain JSON nulls for this sample.
Contrast phase and HU calibration remain unknown. This is an explicit smoke-test
adaptation: the reviewed baseline prints those fields but does not use them for
model inference. A verified local metadata JSON can be supplied via
`--clinical-json` for an authorized case; no values should be invented.

## 2. Colab: exact actions and cells

Open [the Colab notebook on the existing branch](https://colab.research.google.com/github/MihirG1414/pancreatic_cancer_ai/blob/milestone-1-ct-inspection/notebooks/02_panorama_inference_colab.ipynb),
or upload `notebooks/02_panorama_inference_colab.ipynb` through Colab's **File →
Upload notebook**. Sign in if required. Choose **Runtime → Change runtime type →
T4 GPU**, or another suitable available NVIDIA GPU. Do not choose a paid plan as
part of this demo. Free availability is not guaranteed.

The notebook labels its nine code cells:

1. Review licenses, set `PERMITTED_NONCOMMERCIAL_USE = True` for permitted
   noncommercial/student use, retain `SOFTWARE_SMOKE_TEST = True`, run configuration.
2. Run resource checks **before large downloads**. Policy gates are ≥12 GiB free
   VRAM, ≥8 GiB available host RAM, ≥15 GiB free disk; these are conservative
   operating gates, not measured baseline minimums.
3. Fetch immutable Mirai and official baseline source revisions; create a
   separate Python 3.11 environment using pinned uv. No Docker is used.
4. Install the Linux dependency lock in that GPU environment; check dependencies,
   expected versions and actual PyTorch CUDA access. The Windows environment is
   unaffected. Actual GPU execution remains the compatibility test.
5. Upload **exactly the three CT export files**. Do not upload an annotation.
   Check input hash, embedded payload, physical grid and RAM.
6. Download the two official weight archives and license; verify published
   MD5/byte counts, record SHA256 and compare extracted model bytes with the
   verified archives. All ten checkpoints and saved plans are required.
7. Run both pretrained stages. Wait for success; inspect saved per-stage logs
   and `run.json` on a failure. Do not run training or reduce folds.
8. Check actual output paths, runtime/resource samples and uncalibrated score;
   inspect the real CT/candidate-map preview. A failed run blocks this cell.
9. Download `panorama-output.zip` before disconnecting. Colab storage is temporary.

Source pins and licenses are recorded in the notebook/run. Baseline code is
Apache-2.0; weights are **CC BY-NC 4.0**; MSD sample is **CC BY-SA 4.0**.
Commercial company use of weights needs separate permission. Cite the baseline
using the attribution in the [official weight record](https://zenodo.org/records/11160381).
The two archives are about 1.64 GiB compressed; extra space is needed for models,
GPU packages and scratch data. No weights were downloaded to this laptop.

The official [build log](https://github.com/DIAGNijmegen/PANORAMA_baseline/blob/d08f2356fa70d9460881fec0aedba4ebd1566c7e/build.log)
supports torch 2.4.0, nnU-Net 2.5.1, SimpleITK 2.4.0 and lesion extraction 0.2.7.
The notebook uses the corresponding pinned nnU-Net revision and a resolved
Linux/Python 3.11 lock. scikit-image 0.21.0 replaces build-log 0.19.3 for a Python
3.11 wheel; this is documented and has not yet been validated by a model run.
Other adaptations: local paths, one preprocessing/export worker, explicit guards,
null clinical metadata without printing it, and disabled optional compilation.
Original resampling, margins, five folds per stage, TTA, checkpoints, saved
plans and candidate extraction stay in use. `data_utils.py` is called unchanged.

The notebook source pin is a reviewed runner commit; local reporter/importer
changes are not needed inside Colab. If future runner fixes are committed,
advance that immutable pin and start a fresh runtime. Do not silently use main.

## 3. Windows: import the genuine output bundle

After an actual successful Colab run, save the downloaded ZIP inside ignored
`outputs/`. Extract into a new directory and validate/import:

```powershell
$env:PYTHONPATH = "$PWD\outputs\panorama-io;$PWD\src"
$bundleDir = ".\outputs\panorama-bundle-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Expand-Archive -LiteralPath .\outputs\panorama-output.zip -DestinationPath $bundleDir
$predictionDir = ".\outputs\panorama-import-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
.\.venv\Scripts\python.exe -m mirai_ct.panorama --manifest .\cases.local.csv --case-id pancreas_290 --input-export .\outputs\milestone-3-input --bundle $bundleDir --output $predictionDir
$reportDir = ".\outputs\panorama-report-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
.\.venv\Scripts\python.exe -m mirai_ct.report --manifest .\cases.local.csv --case-id pancreas_290 --predictions $predictionDir --output $reportDir
Invoke-Item -LiteralPath "$reportDir\index.html"
```

If you used a different export, replace `--input-export` with that exact folder.
The importer verifies original CT hash, export hash, run/source/fold provenance,
output hashes, embedded MHA payload, dimensions, LPS spacing/origin/direction,
physical corners, finite map values and official scalar JSON score. The score
must match map maximum. Alignment failures stop import; no silent resampling or
registration is attempted. It writes a derived native NIfTI map for the existing
lazy viewer and checks saved voxel planes. Checksums establish traceability and
detect changes; they are not a signature proving someone genuinely ran a model.

The report shows original annotation measurements, separate native CT/annotation/
candidate-map panels, fixed [0,1] map colorbar, extra views at a map maximum,
uncalibrated score and run provenance. No thresholded segmentation, Grad-CAM,
calibrated clinical risk, cancer-detection accuracy or head/body/tail assignment
is claimed. Annotation measurements remain explicitly dataset-derived.

## 4. Demonstrate the completed local work before inference

The existing real report is `outputs/milestone-3-report-no-inference/index.html`.
It clearly states **Predictions unavailable**. Open it, or generate a fresh one:

```powershell
Invoke-Item -LiteralPath .\outputs\milestone-3-report-no-inference\index.html
$reportDir = ".\outputs\pre-inference-report-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
.\.venv\Scripts\python.exe -m mirai_ct.report --manifest .\cases.local.csv --case-id pancreas_290 --output $reportDir
Invoke-Item -LiteralPath "$reportDir\index.html"
```

Verification commands (optional IO folder enables all conversion/import tests):

```powershell
$env:PYTHONPATH = "$PWD\outputs\panorama-io;$PWD\src"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts notebooks/02_panorama_inference_colab.ipynb
.\.venv\Scripts\python.exe -m pip check
```

Recorded local results and blockers are in `PROGRESS.md`. The 119-test result
includes synthetic software tests; it is not a model performance result. Three
synthetic display fixtures and real annotation views were inspected separately.
Generated reports, fixtures, ZIPs, scans, weights and notebook outputs stay out
of Git. The pre-existing modified inspection notebook is preserved.

## Exact remaining action

Connect a free Colab NVIDIA GPU and execute cells 1–9 using the existing public
CT-only export. On success, download/import the bundle and inspect the original
CT report. Record actual run measurements and failures. This sample has
unresolved PANORAMA training overlap and unverified phase/HU suitability; it
can establish software operation only. A permitted suitable independent dataset,
validated thresholds/calibration and further explanation/segmentation work are
needed before any disease-performance or clinical claims.
