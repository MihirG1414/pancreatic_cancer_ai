# Obtaining actual segmentation and raw probability products

## Cell 5: second upload saved with `(1)` filenames

On 15 November, native Colab inspection confirmed that the correct second-case
inputs were fully uploaded but saved as `ct (1).mha`, `input-provenance (1).json`
and `clinical-information-pancreatic-ct (1).json`. The original notebook compared
returned keys with the browser filenames; this fails because Colab's SDK returns
the unique **saved** paths, as implemented in
[the official upload helper](https://github.com/googlecolab/colabtools/blob/main/google/colab/files.py).

The notebook now uses a fresh temporary upload directory, checks canonical
basenames/returned path containment/size, and only then creates the new INPUT.
It frees uploaded buffers and preserves the existing source hash and native-grid
checks. No inference/weight/source-pin changes are needed. Do not reload an
active notebook or re-upload the large CT to apply a source-only notebook fix.

For the specific already-completed second-case upload above, the failed cell
still holds `uploaded`. Recover those bytes in a new cell, using the current
`INPUT = ROOT / "input-cptac-pilot-01"` (which the failed cell did not create):

```python
import hashlib
import json

names = {
    "ct.mha": "ct (1).mha",
    "input-provenance.json": "input-provenance (1).json",
    "clinical-information-pancreatic-ct.json":
        "clinical-information-pancreatic-ct (1).json",
}
if set(uploaded) != set(names.values()):
    raise RuntimeError(f"Unexpected uploaded filenames: {list(uploaded)}")
info = json.loads(uploaded[names["input-provenance.json"]])
if (
    info.get("case_id") != "cptac_pilot_01"
    or info.get("annotation_used") is not False
    or hashlib.sha256(uploaded[names["ct.mha"]]).hexdigest()
       != info.get("mha_sha256")
):
    raise RuntimeError("Uploaded CT/provenance checks failed.")
INPUT.mkdir(exist_ok=False)
for expected, saved in names.items():
    (INPUT / expected).write_bytes(uploaded[saved])
del uploaded
print("Recovered input:", INPUT)
```

Rerun cell 5 for full existing input checks; it reuses the new folder. Then run
7, 8 and 9. Keep previous case folders, completed weights and run outputs.
This recovery code intentionally refuses unexpected names, wrong case/mismatched
bytes or overwriting an existing INPUT. If the dictionary was lost through a
kernel reset, it cannot recover memory that no longer exists; inspect the saved
files before choosing a new upload. Do not silently take old first-case files.

## Reconnecting during cell 6

The browser displaying `Reconnecting` or `Disconnected` does not by itself
establish that the remote weights process has stopped. Cell 6 captures output
and displays it after the command exits, so a quiet cell is not proof of failure.
Reconnect to the same runtime, keep the PC awake and check the existing cell's
execution state. Do not start a second weights command or remove an active
`.part` file. The partial is normal while an archive is being downloaded.

If the existing cell is still running, let it finish. The archives contain
613,484,406 and 1,143,995,491 bytes respectively; the process also verifies hashes
and extracted checkpoints. A quiet period can include verification/extraction.
Once it finishes successfully, continue at cell 7. If the command has exited
with an error, inspect the printed message or `weights-setup.log`; only then
consider removing the specifically named incomplete partial and retrying.

For a recurring browser-connection problem, try a stable network and an updated
supported browser. Google documents Colab's remote VM execution, changing runtime
limits and the `googleusercontent.com` cookie exception in its
[official FAQ](https://research.google.com/colaboratory/faq.html). Browser
reconnection, a kernel crash and VM deletion are different events. If a VM is
actually replaced, `/content` is temporary; saving a notebook alone does not save
its downloaded models or generated output. Persistent archive/result storage is
then necessary. No paid upgrade or larger GPU is justified by this symptom alone.

The original phase-one statement requires model segmentation and a heatmap.
The existing successful ZIP contains only the final candidate map and score.
Its old contents cannot recover the missing intermediate products.

## Check old Colab files before repeating inference

In the old Colab notebook, run only this small check:

```python
from pathlib import Path
r = Path('/content/mirai-panorama/run-20261027-200141')
for name in ('bundle/run.json', 'output_fullres/scan.nii.gz', 'output_fullres/scan.npz'):
    print(name, (r / name).is_file())
```

If the files remain, preserve/download them and keep the original input export.
The model products can be restored from this saved label image/probability array
and the recorded exclusive crop coordinates. No new inference is needed just to
export saved outputs. Do not overwrite the original bundle or pretend post-run
export was another model execution; record export provenance separately.

If those files are gone, use a fresh authorized Colab NVIDIA runtime and the
updated nine-cell notebook. Keep `EXPORT_MODEL_OUTPUTS = True`, review permission
and set its declaration only for permitted use, then execute in order. The source
pin is `b4138f2ae97dc08bcd9aef96b2e37bb5f91698a2`; it includes the tested export
helper. Old source directories must not be silently reused with a different pin.

Cell 7 requests `--include-model-outputs`. Both pretrained stages/five folds and
official candidate extraction remain unchanged. Additional final bundle files:

```text
images/pdac-segmentation/segmentation.mha
images/pdac-probability-map/probability.mha
```

The run records their hashes and semantics. The segmentation is predicted stage-2
class 1, not ground truth. Probability is raw class-1 output, not a clinical
probability, attention map or Grad-CAM attribution. Both are pasted into the
original grid with zeros outside the crop; those zeros mean not evaluated there.
This new GPU export has software regression coverage but no actual GPU run yet.

## Local import/report after receiving a new bundle

Use the existing `.venv` and a fresh output folder. Substitute the actual bundle
and exact original input-export paths; keep the existing successful artifacts.

```powershell
.\.venv\Scripts\python.exe -m mirai_ct.panorama --manifest .\cases.local.csv --case-id pancreas_290 --input-export 'C:\path\to\input-export' --bundle 'C:\path\to\new-bundle' --output .\outputs\panorama-import-with-products
.\.venv\Scripts\python.exe -m mirai_ct.report --manifest .\cases.local.csv --case-id pancreas_290 --predictions .\outputs\panorama-import-with-products --interactive --measure-candidates --output .\outputs\panorama-report-with-products
```

Import checks paired declarations, hashes, grid, ranges and binary labels. The
report adds three static model-segmentation/probability views only when those
products are present. `report.json` records availability and original score.

The `--measure-candidates` flag needs optional SimpleITK (already installed on
this PC). It measures connected retained support, not clinical tumor size, and
does not assign head/body/tail. The current genuine result is available at
`outputs/panorama-report-20261104-reviewed/index.html`, with raw/segmentation
availability correctly false. The slice viewer still displays final candidates;
the extra model products have separate static panels to preserve their meaning.

Independent evaluation, anatomical subregion labeling and decision attribution
remain separate acceptance gates in `completion-review-2026-11-04.md`.
