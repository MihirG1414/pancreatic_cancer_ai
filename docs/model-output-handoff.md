# Obtaining actual segmentation and raw probability products

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
