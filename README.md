# Mirai - pancreatic CT inspection for Rises.io

Milestone 1: native Windows, CPU-only loading and visualisation of one NIfTI CT
at a time. **No model runs, predictions, training or clinical validation.**
The broader project will use the pretrained
[official PANORAMA baseline](https://github.com/DIAGNijmegen/PANORAMA_baseline);
inference is deferred until this intake milestone is checked and compute is available.

The implementation follows the supplied problem statement and the
[milestone specification](docs/superpowers/specs/2026-09-22-ct-inspection-design.md).
Original scans are never resampled, cropped, reoriented or overwritten.

## 1. Open PowerShell in this project

The tested laptop runs Windows 11, Ryzen 5 3500U and Python 3.11.1 x64. Windows
reports 5.95 GiB usable RAM despite 8 GB installed, with roughly 0.55 GiB free at
initial inspection. C: had 4.44 GiB free; D: had about 458 GiB. Close unused apps
before plotting. The lightweight environment used roughly 300 MB on C:.
See [environment measurements and PowerShell checks](docs/environment.md).

For the already configured checkout, use `.\.venv\Scripts\python.exe` directly.
No environment activation or PowerShell execution-policy change is needed.

To reproduce setup in a fresh checkout:

```powershell
py -0p
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir --only-binary=:all: -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-cache-dir --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m ipykernel install --sys-prefix --name mirai-ct --display-name 'Mirai CT (.venv)'
.\.venv\Scripts\python.exe -m pip check
```

`requirements.txt` contains the lightweight runtime; `requirements-dev.txt` adds
test/notebook-execution/build tools. `requirements-lock.txt` records the exact
tested environment. No PyTorch, MONAI, CUDA, nnU-Net or model weights are installed.

## 2. Get one real public CT and existing mask

```powershell
.\.venv\Scripts\python.exe scripts\download_sample.py --destination 'D:\MiraiData\MSD_Task07'
```

This retrieves **one MSD Task07 training CT and its existing annotation**, about
28.2 MB total, from the [official MSD AWS mirror](https://registry.opendata.aws/msd/).
It requests only verified byte ranges of the archive and refuses a full-archive
response. It checks the archive version, tar headers, byte lengths and gzip CRC,
then records local SHA256 checksums and provenance. No archive is extracted.
The dataset is CC-BY-SA 4.0; attribution and source links are saved locally.
See [dataset access and limitations](docs/dataset-access.md).

The downloader refuses to overwrite existing files. If the sample is already
present, skip this command. After an interrupted download, keep completed files
and choose a different destination for a fresh attempt; failed `.part` files are
removed by the script when possible. Do not download the full dataset.

Create the local CSV (PowerShell preserves correct CSV quoting):

```powershell
[pscustomobject]@{
    case_id = 'pancreas_290'
    scan_path = 'D:\MiraiData\MSD_Task07\Task07_Pancreas\imagesTr\pancreas_290.nii.gz'
    label_path = 'D:\MiraiData\MSD_Task07\Task07_Pancreas\labelsTr\pancreas_290.nii.gz'
    dataset_source = 'MSD Task07 Pancreas; real public CT; CC-BY-SA 4.0'
} | Export-Csv -LiteralPath .\cases.local.csv -NoTypeInformation -Encoding UTF8
```

`cases.example.csv` is intentionally header-only. For your own authorized case,
use a pseudonymous `case_id`, its NIfTI path, optional `label_path` (blank if absent),
and `dataset_source`. Relative paths resolve from the CSV's directory. Duplicate
IDs, missing required fields and malformed rows fail explicitly. Do not put
patient names, dates of birth, hospital IDs or patient paths in tracked files.

## 3. Inspect metadata and save a slice

```powershell
$scanPath = 'D:\MiraiData\MSD_Task07\Task07_Pancreas\imagesTr\pancreas_290.nii.gz'
$maskPath = 'D:\MiraiData\MSD_Task07\Task07_Pancreas\labelsTr\pancreas_290.nii.gz'
.\.venv\Scripts\python.exe -m mirai_ct $scanPath
.\.venv\Scripts\python.exe -m mirai_ct $scanPath --mask $maskPath --axis 2 --output .\outputs\real-msd-middle.png
Invoke-Item -LiteralPath .\outputs\real-msd-middle.png
```

Add `--index N` for a specific zero-based slice; otherwise the middle slice is
used. `--level 50 --window 400` controls only display contrast. Omit `--mask` when
no annotation exists. Use a new output filename for each run; existing files are
not overwritten. Metadata-only mode does not read voxel data or create a figure.

Output includes dimensions, header and affine voxel spacing, spatial units,
orientation codes, voxel-to-world affine, transform codes, obliquity, estimated
full-volume memory and measured process/system memory snapshots. NIfTI intensity
scaling is applied per slice. The file format alone does not prove HU calibration
or contrast phase; check the source. No raw free-text header fields are printed.
For planes across the storage direction, the reader streams one 2D storage slab
at a time and retains only the requested row/column. It never creates a full
volume array. Memory readings are snapshots, not guaranteed peak measurements.

## 4. Use the notebook in VS Code

Open [notebooks/01_inspect_ct.ipynb](notebooks/01_inspect_ct.ipynb). In **Select
Kernel**, choose the Python environment `.venv\Scripts\python.exe` or **Mirai CT
(.venv)**. Run cells from top to bottom. The default reads `cases.local.csv`,
checks the optional mask, prints metadata, and displays three native middle
planes sequentially. Change the `slices` list to inspect other planes.

For an automated run of the same notebook:

```powershell
.\.venv\Scripts\python.exe scripts\execute_notebook.py
```

It saves an executed copy under ignored `outputs/inspection.executed.ipynb`.
Set `$env:MIRAI_CASES`, `$env:MIRAI_CASE_ID` or `$env:MIRAI_SLICE_INDEX` before
starting the notebook kernel to select another manifest/case/axis-2 slice.
Remove those session overrides with `Remove-Item Env:MIRAI_CASES` (and the other
variable names) when finished. Use `--output outputs/another-run.ipynb` for reruns.

Mask overlays require matching shape, spatial units, spacing and full affine;
unknown or conflicting transforms block an overlay. Geometry matching cannot
prove the files belong to the same patient: also check the dataset pairing.
Label colors are categorical **existing annotations**, never model predictions.
Only label IDs present on the displayed slice appear in the legend.

Native axis views preserve voxel geometry. Direction letters denote increasing
array axes; these are not standardized axial/coronal/sagittal radiological views.
Oblique/sheared geometry needs special interpretation. Physical aspect ratio
uses affine voxel sizes, without interpolation or full-volume conversion.

## 5. Run checks and keep Git clean

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
.\.venv\Scripts\python.exe -m pip check
git status --short
```

Tests generate tiny **synthetic arrays in temporary directories** solely to
check software. Real scan inspection is recorded separately in the
[progress log](docs/progress.md). Neither establishes cancer-detection accuracy.

Scan files, weights, local CSVs, reports, credentials and `.venv` are ignored.
The original supplied problem statement stays local. **Clear notebook outputs
before committing**; `.gitignore` cannot remove outputs embedded in a tracked
notebook. Store generated images and executed notebooks under `outputs/`.
Stage specific files, inspect `git diff --cached`, and use meaningful commits.
Routine session push: `git push -u origin milestone-1-ct-inspection`.
Never force-push, commit patient material or manufacture activity.

## Layout and next milestone

- `src/mirai_ct/`: loader/geometry, manifest reader, plotter and CLI.
- `notebooks/`: output-free inspection notebook.
- `scripts/`: bounded sample download and local notebook execution.
- `tests/`: synthetic software checks, no bundled scans.
- `docs/`: design, plan, data-access instructions and progress evidence.
- `.venv/`, `outputs/`, `cases.local.csv`: local, ignored.

One month favors a pretrained baseline, not training. After this intake gate,
verify PANORAMA preprocessing and model licensing, arrange Colab/company GPU
access, then run a small reproducible inference pilot. Before reporting metrics,
establish patient-level splits and overlap with baseline training data. No
inference compute, model output, disease metric or clinical claim is established
by this milestone.
