# Bounded public CT pilot — 15 November 2026

Later same-day update: the matched RTSTRUCT is now converted and its source CT
links/native saved grid checked. See [the current demo checkpoint](demo-ready-2026-11-15.md)
for counts, overlay report, new reference manifest and model-comparison command.
Earlier statements below that reference-mask conversion is pending describe the
initial acquisition checkpoint. Second-case model inference remains pending.

## Source choice

The [official PANORAMA source](https://github.com/DIAGNijmegen/panorama_labels)
states that its public development data includes 194 MSD cases and 80 NIH
pancreas cases. More cases from those sources can check software behavior but
cannot automatically establish independent performance. We keep the existing
MSD case and choose a different public collection for the next compatibility run.

[TCIA CPTAC-PDA](https://www.cancerimagingarchive.net/collection/cptac-pda/)
provides radiology images with heterogeneous modalities/protocols. The linked
[CPTAC-PDA tumor-annotations release](https://www.cancerimagingarchive.net/analysis-result/cptac-pda-tumor-annotations/)
provides segmentations, seed points and negative-finding assessments under CC BY
4.0, with data citation required. This does not establish that every CT is
untreated portal-venous imaging or that every annotation describes a primary
pancreatic lesion. Negative assessments in a cancer cohort are not automatically
healthy/non-PDAC control patients. No collection-level independence guarantee is
inferred from choosing a different collection name.

## Exact acquisition performed

Only the following small subset was retrieved; original files/provenance remain
ignored under `data/`. No patient identifiers or DICOM UIDs are published here.

- Official v2 metadata URL:
  [2025-10-20 metadata CSV](https://www.cancerimagingarchive.net/wp-content/uploads/Metadata_Report_CPTAC_PDA_2025_10_20-1.csv).
  Retrieved 260,282 bytes; SHA256
  `3bff13e48fd7708671f00443953bc7cf27eca26baa3a4b1ce65347bd9559ea14`.
  It contains 536 annotation records (not 536 independent scans/patients).
- Selection: `ClinicalTrialTimePointID=Pre-Dose`,
  `ReferencedSeriesModality=CT`, `Annotation Type=Segmentation`,
  `Tracking ID=PANCREAS - 1`, series description `2.5 PV ABD/PEL`.
  The selected record is saved locally in `selected-annotation.local.json`.
  The description suggests portal-venous acquisition; that remains a hint pending
  protocol/expert verification, not a confirmed metadata field.
- Queried the official NBIA v4 `getSeriesSize` before downloading: selected CT
  contains 251 DICOM objects, 132,856,392 uncompressed DICOM bytes. Downloaded its
  64,520,781-byte ZIP via `getImageWithMD5Hash`. All 251 publisher-supplied MD5
  values and ZIP CRCs checked; SHA256 provenance recorded locally.
- Downloaded only the linked RTSTRUCT series, one 134,946-byte DICOM object.
  Its publisher MD5/ZIP CRC checked, with SHA256 recorded locally. Source-image
  linkage comes from the official CSV; RTSTRUCT contour/image references still
  need independent parsing before reference-mask evaluation.

Current API endpoint documentation is linked from the
[official TCIA API guide](https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=477659147)
to [NBIA v4](https://cbiit.github.io/NBIA-TCIA/). Base URL inspected:
`https://nbia.cancerimagingarchive.net/nbia-api/services/v4/`.
The size query is `getSeriesSize?SeriesInstanceUID=<selected UID>&format=json`;
the one-series download is `getImageWithMD5Hash?SeriesInstanceUID=<selected UID>`.
Use the selected record's referenced UID for CT and annotation UID for RTSTRUCT,
not an all-collection download. Keep API responses and source hashes locally.
[IDC](https://learn.canceridc.dev/data/downloading-data) also documents direct
selected-series access; this pilot used NBIA v4, not an unverified third-party mirror.

## Native conversion and current local artifacts

`mirai_ct.dicom_intake` supports conventional single-frame CT only. It rejects
mixed series, duplicate SOP/position records, missing frames/geometry, irregular
slice increments, gantry tilt and changing direction/spacing/scaling. It uses
actual DICOM slice positions, not SliceThickness or filename order. No resampling.

The real series is **512 x 512 x 251**, spacing **0.78125 x 0.78125 x 2.0 mm**,
native NIfTI directions LPS. The `2.5` in its series name is not the measured
slice increment. DICOM RescaleType says HU; scanner calibration is not independently
verified. Phase is left unknown for the inference suitability contract.

Each assembled plane matched an independently decoded DICOM slice. Every saved
NIfTI plane matched the rescaled values, and NiBabel RAS geometry matched the
DICOM LPS geometry after the coordinate sign conversion. `conversion.json`
records source hashes, output hash and these checks. No reference annotation
was used during CT conversion.

- `data/CPTAC-PDA-pilot/ct-series.zip` and `dicom/`: unchanged source CT.
- `data/CPTAC-PDA-pilot/annotation/lesion-rtstruct.dcm`: source reference only.
- `data/CPTAC-PDA-pilot/native/ct.nii.gz`: verified native-grid CT.
- `cases.cptac.local.csv`: local one-case manifest, with no voxel reference yet.
- `outputs/cptac-inspection-20261115/index.html`: inspection only, no predictions.
- `outputs/cptac-pilot-input-20261115-ready/`: completed, verified CT-only Colab
  input: `ct.mha`, `input-provenance.json`,
  `clinical-information-pancreatic-ct.json`. Phase/HU suitability remains unknown
  under the existing export contract. Do not use the earlier interrupted folder
  without the `-ready` suffix; it has only a partial MHA and no provenance.

Conversion command, using the selected UID from the local provenance:

```powershell
.\.venv\Scripts\python.exe -m mirai_ct.dicom_intake --dicom-dir .\data\CPTAC-PDA-pilot\dicom --series-uid '<selected CT UID>' --output .\data\CPTAC-PDA-pilot\native-new
```

The first real conversion attempt stopped at the memory gate. After available
RAM recovered, the unchanged gate passed and conversion completed. No unrelated
process was stopped and no environment was reinstalled. Failed/partial generated
outputs are preserved; a new directory is required for each attempt.

## What this data can establish next

A real model run can check compatibility on another public CT and supply another
demo example. Reference contour conversion/alignment, diagnosis/protocol review
and training-overlap audit remain necessary before evaluating PDAC performance.
This one positive-source pilot cannot establish specificity, case ROC-AUC,
independent generalization or early-stage screening sensitivity. Synthetic tests
remain useful for software arithmetic/geometry; they do not replace these data.
