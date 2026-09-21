# Verified dataset access - 2026-09-22 local date

## Small real case used for software inspection

The [official Medical Segmentation Decathlon AWS registry](https://registry.opendata.aws/msd/)
lists the `msd-for-monai-eu` bucket in eu-west-2 with public access and the
[CC-BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
No AWS account is required. The official mirror currently serves Task07 as a
12,289,971,712-byte uncompressed TAR containing compressed NIfTI files. The
project downloads only one CT/mask pair using HTTP Range, not the TAR.

Source archive:
`https://msd-for-monai-eu.s3.eu-west-2.amazonaws.com/Task07_Pancreas.tar`

Pinned ETag: `"324a716d282dfd690c910d14dc153efd-733"`.

| Member | Payload start (inclusive) | Payload end (inclusive) | Bytes |
|---|---:|---:|---:|
| `Task07_Pancreas/dataset.json` | 19968 | 48548 | 28581 |
| `Task07_Pancreas/imagesTr/pancreas_290.nii.gz` | 4127081472 | 4155174598 | 28093127 |
| `Task07_Pancreas/labelsTr/pancreas_290.nii.gz` | 12281422848 | 12281451810 | 28963 |

Each file's 512-byte TAR header is immediately before its payload. The downloader
checks the expected name, size, file type and TAR checksum. Requests require
HTTP 206, exact Content-Range and length, and the pinned ETag before reading.
If the source changes, it stops; do not simply remove these checks. Re-verify
against the official dataset first. Gzip is checked incrementally, preserving
original compressed bytes. SHA256 recorded locally is a reproducibility hash,
not a comparison with a publisher-supplied individual-file checksum.

The retrieved `dataset.json` explicitly pairs the image and mask, identifies CT
from Memorial Sloan Kettering Cancer Center, and lists 281 training/139 test
cases. Its label dictionary is 0 background, 1 pancreas, 2 cancer. These labels
are source annotation categories, not new diagnoses or model predictions.
Preserve attribution if sharing permitted derivatives; this repository does not
redistribute images or annotations. See the linked registry for publication and
citation information.

Run the bounded script and create the local CSV using [README](../README.md).
It saves source links, license, retrieval time, byte ranges and checksums in
`D:/MiraiData/MSD_Task07/sample_provenance.json`, outside Git. The one-case result
can verify file handling and overlay rendering, not sensitivity, specificity,
Dice, screening performance or generalization.

## PANORAMA: later baseline and dataset access

Use the [official imaging and labels page](https://panorama.grand-challenge.org/datasets-imaging-labels/)
as the starting point. It links current dataset batches, including Zenodo
[batch 1](https://zenodo.org/records/13715870),
[batch 2](https://zenodo.org/records/13742336),
[batch 3](https://zenodo.org/records/11034011) and
[batch 4](https://zenodo.org/records/10999754), and the maintained
[panorama_labels repository](https://github.com/DIAGNijmegen/panorama_labels).

1. Read the current official dataset description, label definitions and
   licensing. PANORAMA uses **CC BY-NC 4.0**, distinct from MSD. For an industry
   project, clarify intended use with Rises.io before later dataset use.
2. Join the challenge if needed to read the linked updates/fixes forum. Check
   release updates before choosing files; older Zenodo records may be superseded.
3. Request one permitted de-identified CT and matching annotation from an
   authorized team contact, or plan a bounded subset from the official source.
   Do not download multi-gigabyte batches on this laptop for milestone 1.
4. Record the exact source/version and annotation type. Some annotations are
   AI-derived; do not describe every mask as expert ground truth.
5. Keep files outside Git, add only local manifest rows, and run geometry checks.

The [official pretrained baseline](https://github.com/DIAGNijmegen/PANORAMA_baseline)
documents two-stage nnU-Net processing and links pretrained weights at
[Zenodo](https://zenodo.org/records/11160381). These were inspected as references
only; no weights or ensemble were downloaded. PANORAMA includes some MSD/NIH
data, so MSD cannot automatically be called an independent test set for that
baseline. Check actual training splits and overlap before any later evaluation.
