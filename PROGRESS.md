# Mirai / Rises.io - resume record

Updated: 2026-11-15 (Asia/Calcutta). This is the authoritative current handoff.

## Milestone 8 complete: genuine second CT demo (2026-11-15)

Received and validated `C:/Users/Mihir1/Downloads/panorama-output (2).zip`
(19,476,127 bytes; SHA256
62d12440b8fb679db437b6fb40ad6e67294a0c79b87ead35739ddbb4497c035a).
It belongs to cptac_pilot_01, source SHA256
a2c685d4c641cdbceac9da6d260e733c6b5a0033e938640d86adbd8d6ac54bf0,
not the first MSD CT. Both stages completed on T4 with unchanged official
pins/five folds; recorded inference 229.141104468 seconds (excludes setup).
Sampled maxima: 6,564.86 MiB process-tree RAM / 1,905 MiB device; 1-second
samples are not exact peaks. No training or extra inference/download performed.

Current second demo: `outputs/cptac-demo-with-products/report/index.html`.
Share ZIP: `outputs/cptac-demo-with-products/demo-report.zip`, 36,791,910 bytes,
SHA256 99d4824283f3a3afc432d6b998d047418704eacb8e5c8a2357808f91ef7b6fa7.
Original bundle, validated native imports, report.json, demo.json and independent
MHA/reference check are preserved beside it. First-case final demo is unchanged.
Current presentation guide: `docs/demo-ready-2026-11-15.md` (now both cases).

Second CT actual mask: 39,059 voxels / 47.679443359375 mL; inclusive native bounds
[335,258,178]-[403,328,199], extents 53.90625 x 55.46875 x 44.0 mm (not clinical
diameter); RAS centroid [-73.07187044,-27.38929408,-16.19267646] mm. Source ROI
reference: 64,219 voxels / 78.392333984375 mL. Model intersection 38,875; Dice
0.752822479134 / IoU 0.603620949335. There are 25,344 reference voxels outside
model mask and 184 model voxels outside reference. This visibly incomplete
coverage must not be described as clinical accuracy or complete tumor extent.
Candidate support is separate: one region, 41,567 voxels / 50.740966796875 mL,
score 0.976832449436 (uncalibrated), Dice 0.781369935530 / IoU 0.641187148021.
The raw probability field is not decision attribution. Source ROI interpretation,
clinical mask validation and training independence remain unresolved.

Checks passed: all six declared bundle hashes; exact source/export provenance;
native grid/orientation and every imported model-output plane; report comparison
agrees with independent direct original MHA/reference counts; 1,004 viewer PNGs,
nine static views, HTML local assets, ZIP CRC and byte-for-byte report contents.
Visually inspected three actual model-mask/probability views and three separate
source-reference/candidate views. One scan processed at a time in the existing
venv, about 2,003 MiB RAM available at start; no user processes/kernels stopped.

Actual native Edge acceptance: original generated report loaded; synchronized
panels at k=190, correct k=0/250 boundary disabling, largest-candidate return,
next k=191 (2,977 voxels) and shared zoom. Comparison table values rendered.
Extracted the actual report-only ZIP to
`outputs/cptac-demo-extracted-check-20261115/` and opened it locally: all three
panels loaded, Off hid candidate overlay, reload restored k=190 / Fill / 65% /
full view. Left extracted demo open in separate report window; original Colab
window/runtime preserved. Screenshot/status verified state when accessibility
slider values lagged updates. Source/model/artifact contents were not altered.

12 targeted notebook tests, Ruff/format and syntax/cleared-notebook checks passed
for the upload fix. Changed documentation links/Python blocks/Git whitespace
passed. No new implementation changed during this import; latest full-project
checks remain milestone 7's 216 Python / 7 Node tests. Data, local manifests,
source documents and generated outputs remain Git-ignored. Two unique CTs now
have genuine model results; repeated first-case runs are not extra cases.

Exact next code action: inspect the pinned stage-1/stage-2 label definitions
and available exports, then draft
`docs/superpowers/specs/2026-11-15-anatomy-attribution-design.md` against the
original statement, specifying required genuine GPU artifacts and acceptance
tests before implementing head/body/tail or attribution. Separately obtain
audited patient-level PDAC labels and training-overlap checks for an independent
positive/negative cohort before ROC/specificity/FROC claims.
Do not infer diagnoses from an ROI or publish an accuracy estimate from these
two cases. The current two-case research demo is ready to present; overall
clinical phase-one validation is not complete. No repeat Colab run is required
to view either accepted report.

Delivery: upload fix 48745e266a44b10df933b27b762d5e53d6ebdb38 was pushed and
matched the actual remote branch head. This result/documentation checkpoint
will be committed/pushed next, with its own remote head verified before handoff.

## Second-case Colab upload collision fixed (2026-11-15)

Second-case cell 5 finished uploading the correct three inputs but rejected
Colab's returned saved names: `ct (1).mha`, `input-provenance (1).json` and
`clinical-information-pancreatic-ct (1).json`. Read-only native Colab inspection
confirmed the names; official SDK source confirms its unique-name behavior.
This was a notebook upload collision, not incorrect user selection or inference
failure. The later successful second-case result is recorded in milestone 8 above.

Fixed notebook cell 5 to use a fresh temporary upload directory, validate exact
basenames/path containment/size before creating INPUT, and free upload buffers.
Existing exact input list, provenance/hash/native-grid checks and source pins
remain in force. Previous inputs/outputs/weights and the active Colab runtime
were preserved. No environment reinstall or model/data redownload was needed.

Checks: **12 notebook tests passed**, including two consecutive uploads with
identical canonical filenames, existing-input reuse and rejection of missing,
extra annotation or outside-stage paths. Ruff lint/format, notebook compilation/
cleared-output checks, handoff Python syntax/local links and Git whitespace
passed. These use synthetic fixtures/mocked upload and input-check subprocesses;
they do not establish a genuine second-case GPU result or clinical performance.
The full suite was not repeated for this notebook-only change; milestone 7's
216 Python / 7 Node results remain the latest full-project checks.

Recovery for the already-completed browser upload is documented in
`docs/model-output-handoff.md`: use existing `uploaded` bytes only after exact
observed-name, cptac_pilot_01, annotation_used=false and MHA checksum checks;
refuse overwriting INPUT. User was given this cell, then instructed to rerun
cell 5 (full input checks/reuse), followed by 7, 8 and 9. Do not restart/re-upload
or rerun setup/weights to address this error. User subsequently supplied the
successful second-case ZIP, confirming the workflow proceeded; the permanent
staging change itself is locally tested.

The then-pending recovery/inference/import has since completed in milestone 8
above. Do not repeat it. Upload fix commit and remote verification are recorded
there; training independence and clinical validation remain unestablished.

## Milestone 7 complete locally: genuine mask/heatmap demo and source reference (2026-11-15)

Current result: `outputs/panorama-demo-final-20261115/index.html` and shareable
`outputs/panorama-demo-final-20261115.zip` (10,382,959 bytes; SHA256
`6e2f42747151c069bf6a7880bdac7293d421eb60c0f661d9f32beb6813704ee0`).
This report now uses genuine GPU class-1 mask/probability products, with findings
summary, measured model volume/centroid/box and single-case Dice/IoU. All three
final real model PNGs visually inspected after opacity correction; all report
JSON/HTML values, 388 viewer assets and ZIP CRC/contents checked. Original CT,
candidate map, model-product hashes and scores unchanged. Old reports preserved.

Final software checks: **216 Python tests passed**, **7 Node viewer tests passed**;
full Ruff lint/format, pip check, Markdown links and Git whitespace passed.
83 warnings are the existing SimpleITK/NumPy shape deprecation in expanded
coverage. Torch/scipy remain absent locally. No GPU/weight/dataset download
was repeated locally. Actual native Edge browser acceptance also passed after
the implementation commit: loaded the local file in a separate window, inspected
summary/rendered CT panels, exercised k=0/96 boundary behavior, largest-candidate
focus at k=42 (640 voxels), next k=43 (618) and previous, shared zoom, outline/off/
fill, opacity 20 vs 65, and offline reload returning to default full view at k=42.
Screenshots confirmed synchronized CT/annotation/candidate rendering and effects.
The browser access host was unavailable, so used native Edge via computer-use.
Original Colab window/runtime was preserved; its second CT upload was observed
in progress and not controlled. Report left open in the separate Edge window.

Current guide: `docs/demo-ready-2026-11-15.md`; it supersedes the earlier same-day
milestone-6 snapshot. Source code and reference masks are software/integrity
checked, not clinical validation. Head/body/tail, decision attribution, independent
positive/negative evaluation, FROC/error review and clinical review remain open.

Exact next action: receive the second CT's genuine Colab ZIP (user has the
input-switch/cells 5/7/8/9 instructions). Import/build with
`cases.cptac.reference.local.csv`, existing `...input-20261115-ready`, explicit
reference label 1 and `--annotation-provenance` pointing to its reference.json;
require actual model products and inspect alignment/measurements. Do not infer
PDAC diagnosis/independence from its source ROI, fabricate missing attribution or
call the overall project clinically complete. Commit/push and actual remote-head
verification follow the completed checks below.

Delivery verification: implementation commit
`2f6a6d9fd70a6f1dc00c1d44ac8955771f93050b` was pushed and matched the actual
remote branch head, with a clean tree before recording browser acceptance.
This documentation closure captures the subsequent real UI check; push and
verify its own final head separately at session end. No source/model/artifact
changed during the browser check; no additional inference was performed here.

User needs a demonstrable research pipeline today and authorizes continuing local
work while Colab runs. VPN was identified by the user and disconnected. Latest
weights command exited on the Dataset104 partial; instructed removal of ONLY
that named partial and retry cell 6, preserving completed archives. New genuine
segmentation/probability ZIP remains pending. Do not disrupt the Colab session.

Resume: clean local/actual remote head `f739e067e61a30d23daa6366ce6c611da874c9be`;
no local Python kernel/inference processes found; existing outputs preserved.
Available RAM about 1,942 MiB. Existing pydicom/scipy absent; use only a small
optional DICOM parsing dependency for the reference contour task. No Superpowers
skills are installed; follow specification/plan/tests/implementation/review.

Next unblocked work: validate the already downloaded CPTAC RTSTRUCT's frame,
series and per-contour image references; rasterize the explicitly selected ROI
on the unchanged native CT grid with documented inclusion semantics. Test
analytical polygon/holes/orientation and wrong-reference failures first. Generate
and inspect actual reference overlays, never present them as model predictions.
Add a concise research findings summary and native-grid measurements from actual
model masks only when present. No guessed anatomy, clinical cutoff, attribution
or PDAC diagnosis. Final model-output verification still waits for Colab.

Milestone 7 real-reference checkpoint: installed only optional pydicom 3.0.1
(2.4 MB wheel) into the existing venv, declared in requirements-reference-io.txt.
Analytical RTSTRUCT tests first failed for missing code, then passed after
implementation. Real source ROI 1 has 28 CLOSED_PLANAR contours across native
k=176–202. Frame/study/series/SOP links and source DICOM/CT hashes checked;
derived native mask contains 64,219 voxels, 78.392334 mL. Saved/verified all
planes at `data/CPTAC-PDA-pilot/reference-20261115/reference.nii.gz`, SHA256
`fbc376746d0a951be3adb429f39e624919b76fb5e2ccebc5fb53b2e517868308`.
No slice interpolation/resampling/inference; clinical reference validation and
diagnosis remain unestablished. New ignored manifest cases.cptac.reference.local.csv
preserves the old no-reference manifest. Original CT-only export remains valid.
Generated `outputs/cptac-reference-report-20261115/index.html`; visually checked
all three real overlay PNGs, with source-reference semantics hash-bound in report.

Genuine extended ZIP received: `Downloads/panorama-output (1).zip`, 10,157,431
bytes, successful pretrained run started 2026-11-15T12:07:46.542370+00:00,
runtime 222.998082 seconds, unchanged baseline/folds/source CT. New demo builder
successfully checked and imported actual segmentation/probability products to
`outputs/panorama-demo-with-products-20261115/imported`; report/ZIP generated.
Original score 0.999536395072937 and candidate map unchanged. Actual model mask
has 4,946 voxels (10.375289 mL), native bounds [244,276,35]–[273,304,47], extents
[27.4805,26.5645,32.5] mm (box, not clinical diameter). Against MSD label 2:
intersection 3,211; Dice 0.75847408, IoU 0.61092085. This single-case comparison
has unresolved PDAC histology/training overlap; it is not independent accuracy.
Derived mask hash `cdac733629b2e549ca8821a8929de4fb41da2931eafbf47fb0df7bc86eac8de5`;
probability hash `50901a8ec2290c0bcb02f442b30a7d21fd7f136e7df25ad6b2ef5c54f03e6335`.
Raw probability is genuine model output, not Grad-CAM/attention attribution.

Added deterministic findings summary and actual binary-mask volume/centroid/box
measurements, plus explicit annotation provenance in reporting. Visual inspection
of actual model PNGs found near-zero raw probabilities darkening the entire crop;
added/tested probability-weighted opacity (display only) with unchanged 0–1 values.
Regenerate final report from the existing validated import after targeted checks.
User was given the exact second-case input switch and cells 5/7/8/9 to reuse the
successful T4 environment/weights; its new result is still pending. Finish code
review/full checks, final real PNG inspection, documentation and commit/push.

## Milestone 6 software complete; fresh GPU products pending (2026-11-15)

Latest connection checkpoint: user reports recurring Colab UI
`Reconnecting`/`Disconnected` during cell 6, without a RAM-crash/GPU-limit
message. This does NOT establish VM termination or paused download. Instructed
reconnection to the same session and preservation of the active cell/files.
Do not rerun cell 6 concurrently or remove a .part while its download may still
be running. The earlier partial-file removal applied to an already exited
weights command. Notebook cell 6 is quiet during download because it prints its
captured log after subprocess exit. Actual session/process/file progress remains
unobserved here; no fresh GPU run or successful retry is claimed.
Next: reconnect, check whether cell 6 remains busy and whether its download is
progressing, then continue cells 7–9 only after weight setup succeeds. If the
command exits, capture its full error before choosing recovery. If files are
lost across VM replacement, persistent archive caching is a separate next fix.
Updated cell-6 guidance and handoff documentation; all 8 notebook checks, its
Ruff lint/format and Git whitespace passed. Executable code/pins are unchanged.
Resume review found a clean checkout at `874cfff`, matching the actual remote;
no local Python/notebook process was found or stopped. This guidance checkpoint
will be committed/pushed and its actual remote head checked separately.

Latest live Colab checkpoint: user's cell 6 failed before inference. Diagnostic
rerun exposed `Incomplete download exists:
Dataset103_PANORAMA_baseline_Pancreas_Segmentation.zip.part`.
Instructed removal of ONLY that generated partial file under ROOT/archives, then
retry cell 6; completed archives/weights and the runtime are preserved. Actual
retry result is pending. Do not interpret this as a model-inference failure or
change baseline/checksum/resource guards. Notebook cell 6 now retains/displays
`weights-setup.log` before raising a descriptive error, reading weight provenance
only after success. New success/failure behavioral regressions initially failed;
after correction all **8 notebook tests passed**. Full Ruff lint/format including
the cleared notebook and whitespace passed. This follows the earlier full
192-test suite; two newly added notebook regressions were tested separately.
Actual GPU retry success remains unverified.

Delivery verification: milestone 6 implementation commit
`a550d17ccafa08d18a3107342d46a30fb7448eb3` was pushed and matched the actual
remote branch head with a clean tree before the live Colab troubleshooting edit.
This subsequent notebook/logging checkpoint records the known failure and tested
visibility fix; commit/push and verify its own head separately at session end.

Current result: genuine one-case interactive demo with explicit quantitative
reference comparison; one additional public CT downloaded, verified, converted
and prepared for Colab. No new network trained and no second-case inference yet.
Final verification: **192 Python tests passed**, **7 Node control tests passed**;
full Ruff lint/format, pip check and Git whitespace passed. The 72 warnings are
the existing SimpleITK/NumPy shape deprecation in expanded synthetic coverage.
Actual browser interaction remains unverified; all three new real CT static
views and generated HTML/asset/measurement states were checked separately.

Primary demo: `outputs/panorama-demo-20261115/report/index.html`; shareable
`outputs/panorama-demo-20261115/demo-report.zip`. Completed second-case input:
`outputs/cptac-pilot-input-20261115-ready` (three verified files). All data,
medical volumes, local manifests, private statement and outputs remain ignored.
See `docs/completion-and-demo-2026-11-15.md` and
`docs/public-ct-pilot-2026-11-15.md` for commands, limitations and the remaining plan.

Exact next action: user sends the updated Colab output ZIP when it completes
(they confirmed they will). Build its report using `mirai_ct.demo` with
`--require-model-products`, the exact original CT-only export and original
manifest; inspect actual segmentation/probability views and compute actual
model-mask overlap. Then run the prepared CPTAC case on the same T4 with a new
INPUT folder and run directory, preserving the original case. No need to repeat
old-runtime checks or model downloads locally. Reference RTSTRUCT conversion,
head/body/tail, decision attribution, independent cohort/FROC and clinical review
remain open. This is not full phase-one/clinical completion. Commit/push and
actual remote-head verification follow the final recorded checks.

Resumed from the latest checkpoint, reviewed the original private requirements,
source, notebook, tests, local artifacts and Git state. Clean local and actual
remote HEAD both `32a1ea5eac4a0397a62326d73e893f7fa87ab0c4`. No existing Python
kernel/inference process found; existing outputs preserved. Available RAM about
1.78 GiB, disk about 312.7 GiB; no local NVIDIA runtime. No Superpowers skills
are installed; follow specification/design/tests/implementation/review directly.

User confirms the old Colab session was lost and can run a T4 now. Directed them
to the current nine-cell notebook with model-product export enabled. Genuine
segmentation/raw probability remain pending receipt; do not repeat the old-file
recovery check or manufacture these products from the final candidate map.
Continue the pretrained PANORAMA approach; no new training is requested/implied
by assembling the final demonstrable pipeline.

This milestone adds bounded native-grid overlap evaluation, explicit distinction
between candidate-support overlap and actual model-segmentation Dice/IoU, and
patient-separated case-score evaluation with honest undefined/single-class cases.
Research public CT data from primary sources, inspect only small metadata before
selecting any scan, and document source/reference/overlap limitations. Do not
treat MSD tumor labels as confirmed PDAC diagnoses or development-set examples
as independent validation. Add an actionable completion/demo guide and preserve
all existing genuine artifacts. Exact next action: write design and meaningful
evaluation regressions, inspect current CPTAC-PDA annotation metadata, then
implement the evaluator and run it on the existing genuine case.

Milestone 6 checkpoint: 17 new analytical/contract evaluation tests initially
failed for the absent module, then passed after implementation. Genuine existing
case comparison completed: reference 3,521 voxels, candidate support 5,168,
intersection 3,251; candidate-support Dice 0.74830245, IoU 0.59783008. These are
not tumor-segmentation accuracy or independent validation; actual model-mask
metrics remain null. Results saved under ignored `outputs/panorama-evaluation-20261115`.

Retrieved the official CPTAC-PDA v2 (2025-10-20) annotation metadata, 260,282
bytes, 536 annotation records, SHA256
`3bff13e48fd7708671f00443953bc7cf27eca26baa3a4b1ce65347bd9559ea14`.
Selected one pretreatment CT described as `2.5 PV ABD/PEL` with a matching
pancreas-lesion annotation (separate from duct/liver annotations). Phase remains
unconfirmed. Official current NBIA v4 size query reports 251 instances and
132,856,392 DICOM bytes. Downloaded ONLY that series ZIP, 64,520,781 bytes,
including its publisher MD5 manifest, to ignored `data/CPTAC-PDA-pilot`.
No model inference on this CT yet; training independence still not audited.
Next: verify all individual DICOM hashes, preserve bounded download provenance,
add/test native DICOM-series intake without resampling and fetch only the paired
annotation. This is a small public pilot, not a full collection download.

Milestone 6 implementation checkpoint: conventional CT intake tests passed
**11/11**, including irregular spacing/tilt/duplicate/orientation/frame rejection
and an end-to-end synthetic DICOM-to-NIfTI round trip. Real CPTAC conversion
completed after RAM recovered, preserving 512x512x251, 0.78125x0.78125x2.0 mm,
native LPS. Every source and saved plane was checked; output SHA256
`a2c685d4c641cdbceac9da6d260e733c6b5a0033e938640d86adbd8d6ac54bf0`.
All three real inspection PNGs were visually inspected. Retrieved only the paired
134,946-byte RTSTRUCT and verified its publisher MD5/ZIP CRC; rasterization and
contour/image-reference verification remain pending. No new model run performed.

Implemented `mirai_ct.demo`: bounded/duplicate-safe ZIP handling, validated import,
interactive report, explicit comparison and report-only ZIP; optional
`--require-model-products` rejects older bundles. Added readable overlap tables
to `mirai_ct.report` when an explicit label/description is requested. The existing
genuine ZIP built `outputs/panorama-demo-20261115/report/index.html` and a
9,836,317-byte shareable ZIP. Model-mask/probability availability remains false,
score/reference counts unchanged; 97 CT assets and table values checked.

Rechecked user's `Downloads/panorama-output.zip`: it is the original Oct-28-IST
successful run, with all four declared output hashes matching and no model-output
pair. User will supply the new ZIP when the updated Colab run finishes. No need
to ask again about runtime access or old artifacts.

One new CT input export was interrupted deliberately after noticing it overlapped
the genuine demo build; only our own exporter was interrupted, and partial
`outputs/cptac-pilot-input-20261115` is preserved as incomplete. Restarted export
sequentially in a fresh `...-ready` folder after the demo finished. Do not use the
partial folder. Full regression/closure checks and final export validation pending.

Second-case CT-only export completed sequentially at
`outputs/cptac-pilot-input-20261115-ready` (all three required files present;
annotation_used=false). Original CPTAC NIfTI hash remains unchanged. The
interrupted earlier folder is intentionally retained and explicitly excluded
from handoff. Added exact Colab input-switch instructions that reuse environment
and weights while preserving the current case and selecting a new input folder.
User's fresh extended-result ZIP is still pending; do not rerun/download models
locally. Initial full suite passed 190 tests, then ZIP metadata/path review added
two tests plus stricter guards; targeted 26 demo/evaluation tests passed. Final
full-suite, packaging/privacy and remote delivery checks follow.

Historical entries below are dated evidence; their earlier next steps and
inference-pending statements are superseded by this checkpoint.

## In progress: original requirements reconciled; model-output completeness (2026-11-04)

Read the user's original problem statement from the supplied private `._` file
outside this repository. It is plaintext Markdown; do not copy/commit it.
It requires a working inference pipeline with risk score, region location/size,
segmentation and heatmap, plus validation. The earlier provisional audit correctly
identified missing segmentation/explanation/localization outputs; it must now
be updated against the actual document. Its example of PANORAMA-to-MSD external
testing is insufficient for this baseline because MSD overlap is unresolved.
The user's earlier no-training/pretrained-PANORAMA constraint remains in force.

New milestone plan: add explicitly labeled per-region candidate geometry from
the existing validated map; prepare optional native-grid model segmentation/raw
probability exports and validated import without pretending the old candidate
map contains missing intermediates. A raw probability heatmap is model output,
not Grad-CAM/attention attribution. Head/body/tail, calibrated decisions and
independent validation still require additional evidence. User is unsure whether
the old Colab runtime remains; do not rerun/download models locally. Next action:
write design/tests for native output restoration and candidate measurements,
then implement and test with synthetic fixtures; use the real map only for
candidate-support measurements. Browser UI automation remains stopped.

Model-output checkpoint: implemented optional `--include-model-outputs` in the
GPU runner, preserving native-grid stage-2 class-1 binary segmentation and raw
class-1 probability with explicit zero-outside-crop semantics. Original baseline
inference/postprocessing remains in use. Complete-pair semantic/hash/grid/range
checks and per-plane native import checks reject missing/tampered extras; old
bundles remain supported. Report displays actual extras only when present and
explicitly marks their absence in the old real bundle. Probability output is
not labeled as attribution. This path is synthetic-tested, not GPU-executed.

Added optional `--measure-candidates`: 26-connected retained support regions with
inclusive native bounds, RAS/LPS centroid, native-axis extent and support volume.
These are not validated tumor measurements and head/body/tail stays unassigned.
Generated `outputs/panorama-report-20261104-reviewed/index.html` and `report.json`
from the unchanged genuine import. Its one support region has 5,168 voxels,
bounds [244,276,35]-[273,304,47], approximate extents [27.48,26.56,32.5] mm and
support volume 10.8410 mL; do not confuse this with annotation cancer volume.
Model segmentation, raw probability and attribution availability are false in
this real report; calibrated screening decision/clinical validation remain absent.

Checks: full **152 Python tests passed** before adding one CLI forwarding
regression; targeted model-output tests then passed with that regression.
Ruff lint/format, pip check and whitespace passed. Temporary low-memory warnings
occurred during small synthetic tests; real report ran after RAM recovered to
about 1.9 GiB available. No processes were stopped. Next: commit source to obtain
an immutable notebook pin, enable optional output export in its nine cells,
document old-runtime recovery check, then run final checks and push.

Final milestone 5 software checkpoint: native-output source committed at
`b4138f2ae97dc08bcd9aef96b2e37bb5f91698a2`. The nine-cell notebook now pins it
and defaults `EXPORT_MODEL_OUTPUTS=True` (permission remains False until operator
review). Added run-cell behavioral checks for enabled/disabled extra export.
Added `docs/model-output-handoff.md` with a small existence check for old saved
Colab intermediates and exact fresh-run/import/report steps if they are gone.
No source model/weight/fold changes. Original private statement stays outside Git.

Final checks: **155 Python tests passed**, **7 Node control tests passed**;
full Ruff lint/format, pip check and whitespace passed. 57 warnings are the
existing SimpleITK/NumPy deprecation in expanded synthetic coverage. The reviewed
real HTML/report.json still records extra model outputs unavailable, one support
region and unchanged score/source hashes. Created ignored
`outputs/panorama-report-20261104-reviewed.zip` for sharing. New helper GPU
execution and actual browser interactions remain unverified, as already stated.

Exact next action: user runs the three-file old-Colab existence check in
`docs/model-output-handoff.md`. If files exist, recover/re-export genuine saved
segmentation/probabilities with separate provenance; if absent, run the updated
source-pinned notebook on an authorized NVIDIA runtime and import its new bundle.
Then verify actual model views and continue anatomical localization/attribution
and independent evaluation. No actual independent labeled test cases confirmed.
This is implementation progress toward phase one, not full project completion.

Milestone 5 delivery verification: changes through `662e2b6` pushed; local and
actual remote head matched `662e2b6f4966a62554c3188d0fd0928d95d62354`, with clean
working tree. Public immutable runner and model-output helper at notebook pin
`b4138f2` fetched and matched tested Git source byte-for-byte. This closure
checkpoint records that verification; push/check its own commit at session end.
Next user action remains the saved-Colab-intermediate existence check.

## In progress: milestone 4 usability and Colab reliability (2026-11-04)

User authorized review of the repo/plan and continuation toward project completion.
Resume review: clean branch at `6013ef9`, matching actual remote head; existing
scan/import/report artifacts and `.venv` present; existing Python processes left
untouched. Reviewed root checkpoint, milestone specifications/plans, source,
tests and executed notebook. The broader private problem statement is absent
from this clone; asked user for its path and independent evaluation-case access.
No Superpowers skills are installed in the available local skills directory;
follow the same specification/plan/test/implementation/review sequence directly.

Next milestone: (1) permanently fix Colab backend/cache/download handling,
preserve its executed evidence under ignored outputs and restore a cleared
source-pinned notebook; (2) improve candidate focus and add an offline native
slice viewer with synchronized CT/annotation/candidate panels, zoom, outlines
and opacity; (3) audit remaining requirements and prepare evaluation gates.
Reuse the successful model output. No new inference or data/model download.
Exact next action: write milestone 4 design/tasks and failing regressions for
runtime defects and candidate visibility, then implement in small verified commits.

Runtime checkpoint: eight new regressions initially failed for missing helpers;
implemented strict pinned-source validation that tolerates only untracked
`__pycache__/*.pyc` while rejecting source edits and other untracked files, plus
headless Matplotlib/no-bytecode subprocess configuration. Runtime contract and
reliability tests: **23 passed**; targeted Ruff and whitespace checks passed.
Installed only missing declared dev dependency nbformat into the existing venv
for notebook checks. No GPU or model changes; this does not count as a fresh
GPU verification. Exact next action: commit this runner so the cleaned notebook
can pin it, then preserve executed evidence and fix the nine notebook cells.
User will upload original requirements; independent labeled test-case availability
is still being clarified (explained training/development overlap in chat).

2026-11-04 implementation checkpoint: runtime fix committed as
`c9363a9c378e7c539e60a83b802e102cb6ff88e9`; nine-cell notebook now pins that
immutable source, sets headless/no-bytecode ENV before model imports, resets
permission to False, explicitly reports reused inputs, captures top-level logs,
selects the largest candidate preview slice and reloads saved status for download.
Original executed notebook preserved byte-for-byte at ignored
`outputs/colab-evidence-20261104.executed.ipynb` (SHA256
`02219b5554f0910ce4f3bbdd2197f941fd828564c6b72702fcc2daed153f80e8`).
Tracked notebook is cleared; all prior troubleshooting cells removed from it.

Implemented `viewer.py` plus packaged vanilla-JS controls and optional report
`--interactive`. Exports native axis-2 PNGs one plane at a time with original
physical aspect, separate CT/annotation/candidate panels, synchronized slice
navigation, 15-mm padded candidate zoom, fill/outline/off and opacity. No CDN,
server, new runtime dependency, original-grid edit or fabricated probability map.
Static candidate focus now uses largest positive cross-section; real case focus
is [259, 290, 42] (640 positive voxels on k=42), replacing the thin k=35 edge.

Generated `outputs/panorama-report-20261104/index.html`, 388 viewer PNGs covering
all 97 native k planes, six static views and a shareable report ZIP (~9.4 MB).
Asset/embedded-metadata checks passed; all original CT/imported-map hashes and
score 0.999536395072937 unchanged. Visually inspected new static k=42 view.
Verified built wheel contains viewer JavaScript. Report slice assets are about
9.20 MiB. Available RAM afterward 1168.4 MiB (snapshot, not peak).

Verification: **138 Python tests passed**, including the formerly excluded
notebook test and regressions (9 existing SimpleITK/NumPy deprecation warnings).
**7 Node simulated-DOM tests passed**, including navigation/zoom/opacity,
late-image race protection and missing assets. Full Ruff lint/format, pip check
and whitespace checks passed. Initial CLI subprocess test failures were caused
by the new PC lacking an installed project/PYTHONPATH; installed this repository
editable with --no-deps, then the full suite passed. No dependency/environment
reinstallation, model download or GPU rerun.

Actual browser verification is PENDING: native Edge UI automation stopped with
"could not determine the current browser URL on Windows with enough confidence
to enforce policy". Stopped UI interaction as required. Automated JS/state and
PNG checks do not substitute for manual browser rendering verification. Corrected
Colab GPU execution is also untested; previous pilot remains valid evidence.

Added `docs/completion-review-2026-11-04.md` with provisional requirements audit,
evaluation-data explanation, missing segmentation/localization/explanation/risk
work and explicit acceptance gates. Original problem statement upload still
pending; no independent cases confirmed. Updated README/demo/source-plan status.
Exact next action: user opens the new report and checks controls; read the
promised original .md when attached, map its complete requirements to this audit,
then implement unblocked missing outputs and obtain independent test-case access.
Do not mark the overall project or clinical validation complete.

Delivery check: runtime and viewer/notebook commits through `16b841e` pushed to
the existing branch; local and actual remote head both matched
`16b841e44dc39368f34461504fafe740d953d948`, with clean working tree. Fetched
the notebook's immutable runner URL from GitHub and confirmed byte equality
with commit `c9363a9` (SHA256
`285576897f9cedbd9abf19f4b6b0282b684b20d6fbe275fb697bf41f79160ed7`).
This closure update records verification; push/check its own commit at session
end. Browser and fresh-GPU checks remain pending as stated above.

## Portable chat-memory file (2026-10-28)

Created `docs/project-memory-2026-10-28.md` at the user's request. It consolidates
completed milestones, genuine inference/run measurements, validation evidence,
separate local/GPU stacks, artifact locations, runtime workarounds, candidate-map
display findings and remaining work for transfer to an older project chat.
Checks passed: UTF-8 reading, balanced fenced blocks, relative reference links,
key handoff facts and Git whitespace. The file contains approximately 2,291 words.
This is a dated snapshot; this root checkpoint remains authoritative. No code,
model output or notebook changed. Next: user can attach/copy the memory file;
project next steps remain the viewer/runtime/evaluation work recorded below.

## Complete: restored CT and first prediction report (2026-10-28)

User confirms this is a new PC with only the cloned repository and authorizes
redownloading the single public `pancreas_290` sample. Exact original input export
is available in `C:/Users/Mihir1/Downloads/Telegram Desktop` (CT plus two JSONs).
The Colab output bundle is in `C:/Users/Mihir1/Downloads/panorama-output`.
Plan: restore a lightweight local environment; use the existing bounded downloader
for only the sample CT/annotation and dataset metadata; match source/export hashes;
create an ignored manifest; validate/import the bundle; generate and inspect the
report. No GPU installation or repeated inference is needed. Free RAM before
setup is about 2.09 GiB on this new PC (15.19 GiB visible); monitor before IO.
Fetched remote `e935167` (user's saved Colab notebook); preserve its existing
outputs and source changes. Exact next action: download the sample and set up
the absent local environment, then compare original CT SHA256 with run provenance.

Acquisition check: bounded downloader completed for dataset metadata, the
28,093,127-byte CT and 28,963-byte existing annotation in ignored
`data/MSD_Task07`. Tar headers, fixed archive ETag, exact HTTP ranges and gzip CRC
passed. Downloaded CT SHA256 equals both input/run provenance
`4b5cb353850c0a68c5b1824519777ef2a736cb171bcbad277c55cfd8c4abaaf8`;
Telegram export SHA256 equals both recorded MHA hashes
`2511980c4a9689647cb808ebcf6bbace82109332147a25b8a2af47242e6fe08c`.
Created ignored `cases.local.csv`; no source scan/export changed. New `.venv`
uses available bundled Python 3.12.14 (the old PC's Python 3.11 is absent),
with lightweight requirements and optional SimpleITK 2.4.0; installing tools
for local verification. This local reporting environment differs from Colab's
recorded inference environment. Next: execute importer and report, then review.

Completed local validation: `mirai_ct.panorama` imported the genuine bundle to
ignored `outputs/panorama-import-20261028`. Source/export/bundle hashes,
baseline/nnU-Net pins, five folds, successful run declaration, original physical
grid, finite map range, score/map-maximum equality and restored NIfTI sample
planes passed. No resampling was performed. `mirai_ct.report` generated
`outputs/panorama-report-20261028/index.html` plus six PNGs. Visually inspected
all six images; checked HTML links, separate annotations/model panels, score,
provenance and limitations. Original annotation counts remain 29,162 (label 1)
and 3,521 (label 2). Candidate display focus is native [251, 290, 35]; this is a
display selection, not a validated lesion location or accuracy result.

Verification on Python 3.12.14: **118 tests passed** (8 SimpleITK/NumPy 2.5
deprecation warnings). Excluded only `tests/test_panorama_notebook.py`, whose
cleared-output contract is incompatible with the user's already committed
executed Colab notebook (nine code cells have outputs). Preserved that notebook;
did not report its cleanliness test as passed. Ruff lint and format for
`src tests scripts`, pip check and Git whitespace checks passed. Local resolved
environment recorded in ignored `outputs/report-environment-20261028.txt`;
SimpleITK 2.4.0 is installed in this new `.venv`, not the historical optional
target folder. Torch remains absent locally. Available RAM after checks about
1513.7 MiB (snapshot, not a peak measurement). Browser/file opening was queued
through Codex; visual review here used the actual generated PNGs and HTML checks.

Updated README/demo guide to distinguish this successful pilot from the prior
unexecuted handoff. Generated outputs, data, manifest and environment remain
ignored. No input/weight downloads beyond this one sample and no repeated GPU
run. Runtime workarounds still need permanent source fixes; input phase/HU,
clinical metadata, training overlap and independent performance remain unknown.
Exact next action: open the generated HTML report and review the demo with the
user; before another Colab pilot, fix/test notebook environment/cache/download
handling and clear tracked notebook outputs in a separately scoped change.
For evaluation, first obtain suitable independently held-out permitted cases.

Delivery preparation: created ignored `outputs/panorama-report-20261028.zip`
containing the HTML and six images for sharing. Reconciled the new remote by
fast-forwarding to the user's `e935167`; no notebook changes made locally.
For this documentation commit, reuse the author's name/email from that verified
existing user commit with command-local Git options (no global identity change).
This resolves the earlier missing-identity/remote-ahead checkpoint below.

Delivery verification: documentation commit `d9a35a1` was pushed to
`origin/milestone-1-ct-inspection`; local and actual remote head both matched
`d9a35a1de8b497a43abaa4acb45f027702bc0e27`. Working tree was clean and source
CT hash still matched after report generation. This closure checkpoint records
that verification; push and verify its own commit at session end. Next action
remains user review of `outputs/panorama-report-20261028/index.html`.

## Colab output received; local report validation pending (2026-10-28)

The user executed the Colab pilot and downloaded/extracted its output. Reviewed
the bundle at local ignored/untracked-outside-repository path
`C:/Users/Mihir1/Downloads/panorama-output`. Its `run.json` reports successful
pretrained inference with baseline `d08f235`, folds 0-4, Tesla T4 and runtime
167.6979 seconds. Both stage logs end with `done with scan`. All four recorded
output SHA256 checks match the extracted files. The scalar JSON is
0.999536395072937: an uncalibrated model score, not a clinical probability.
These are bundle/provenance checks; local map geometry, voxels and final report
have not yet been independently validated. Historical statements below that no
GPU run exists describe the earlier handoff and are superseded by this receipt.

Colab troubleshooting in this conversation: the source cleanliness guard rejected
an untracked `src/__pycache__/data_utils.cpython-311.pyc`; the user removed that
specific cache and set `PYTHONDONTWRITEBYTECODE=1` in subprocess ENV. Stage 1 then
failed because it inherited Colab's inline Matplotlib backend; setting
`ENV["MPLBACKEND"] = "Agg"` allowed the user to continue. Cell 9 needed to reload
`bundle/run.json` because notebook variable `run` was undefined. These were
runtime workarounds; repository runner/notebook fixes remain pending.

Current checkout is clean before this checkpoint update, HEAD `cb532aa`. Unlike
the historical laptop state, this checkout has no `.venv`, `outputs/` or local
case manifest; the recorded `D:/MiraiData/MSD_Task07` path is absent. Existing
Python processes were inspected and left untouched. No environment was installed
and no input was redownloaded. Asked user for original CT and input-export paths.
Input suitability and training overlap remain unresolved; this is a software
smoke test, not independent disease-performance validation.

Exact next action: locate/recover the original `pancreas_290.nii.gz` and exact
CT-only input export (from the user or still-connected Colab), restore/reuse the
lightweight local environment and manifest as needed, validate/import this bundle
with `mirai_ct.panorama`, then generate and visually inspect `mirai_ct.report`.
Do not rerun successful inference or download weights again for reporting.

## Milestone 3 local integration verified; GPU pilot pending (2026-10-14)

Current delivery state: verified CT-only MHA export, Docker-free five-fold GPU
runner, cleared Colab notebook, prediction import and separate report panels
are implemented. **No real pretrained inference has run and no genuine model
outputs exist locally.** The notebook's GPU cells remain unexecuted. The current
sample's phase/HU/clinical metadata and training overlap are unresolved.
Exact next technical action: connect a free Colab NVIDIA runtime and execute
the nine code cells in `notebooks/02_panorama_inference_colab.ipynb` with the
three existing files in ignored `outputs/milestone-3-input`, then download and
validate/import the genuine output bundle using `docs/milestone-3-demo.md`.

Actual resume review: local HEAD `a072ba0`, branch
`milestone-1-ct-inspection`; only pre-existing inspection notebook outputs are
modified. Reviewed Git diffs/remotes/recent commits, existing artifacts,
processes, problem statement, loader/manifest/report and official baseline.
Preserve that notebook and unrelated processes. No inference has run.

User selected free Colab and confirmed no verified phase/HU/clinical metadata.
These stay unknown; use the public case only as a software smoke test, with
unresolved training overlap. Baseline remains at
`d08f2356fa70d9460881fec0aedba4ebd1566c7e`. Build log gives nnU-Net 2.5.1,
torch 2.4.0, SimpleITK 2.4.0 and report-guided-annotation 0.2.7.
SimpleITK 2.4.0 installed without dependencies into ignored
`outputs/panorama-io`, leaving existing environment packages unchanged.
Initial free RAM about 1.24 GiB; recheck before conversion.

Exact next action: implement/test streamed CT-only MHA export with independent
RAS/LPS geometry and intensity checks, then GPU notebook and prediction import.

2026-10-14 input checkpoint: eight new geometry/export tests passed, including
rotated/reflected anisotropic geometry, translation, scaling and spatial units;
full suite **71 passed**. Ruff/whitespace checks passed. Real public case exported
to ignored `outputs/milestone-3-input`: 512 x 512 x 97; spacing
0.9160159826 x 0.9160159826 x 2.5 mm; LPS origin
[468.08416748, 468.08416748, 0], direction diag(-1,-1,+1).
Independent SimpleITK read found zero maximum physical-corner error and zero
error across 27 representative scaled-intensity samples. Source hash unchanged.
Memory snapshots: before RSS 59.8 MiB/free 1369.2 MiB; after RSS 159.5 MiB/free
1241.2 MiB (not peaks); conservative IO budget 419 MiB. Export did not read mask.
No models/weights/CUDA installed on laptop. Browser inventory returned no enabled
browsers/apps, so no authenticated Colab GPU can currently be controlled here.
Exact next action: implement source-pinned Docker-free notebook/runner, then
output import/report; user will need to connect a free Colab GPU runtime.

2026-10-14 GPU runner checkpoint: 13 new orchestration contract tests passed;
combined export/runner tests 21 passed. Tests cover five-fold commands, all ten
checkpoints, checksum/ZIP safety, empty or invalid pancreas masks, invalid crops,
and stage physical-grid mismatch. Resolved 77 pinned distributions for Linux
x86_64/Python 3.11 with uv 0.8.22, without installing GPU packages or weights.
This checks dependency resolution, not GPU execution/model compatibility.
Zenodo API independently confirms archive checksums/sizes and LICENSE.txt size
19,917 bytes. The source runner calls unchanged baseline helpers. Numerical
version adaptation is documented (scikit-image 0.21.0 vs build-log 0.19.3).
Laptop preflight failed because nvidia-smi is absent, as expected on this hardware.
During small synthetic tests Windows free memory dropped below 512 MiB and the
existing loader emitted its memory warning; no full scan was loaded in those tests.
Exact next action: create cleared notebook pinned to this runner checkpoint,
then implement/test output import and reporting. Genuine GPU run remains pending.

2026-10-14 integration/review checkpoint: local full suite **119 passed**;
Ruff lint/format, pip check and Git whitespace checks passed. The Colab notebook
has cleared outputs and schema/syntax checks (including embedded subprocess
scripts); its GPU cells have not been executed. Import tests use explicitly
synthetic temporary fixtures, including rotation/reflection/translation,
source scaling, wrong geometry, checksum tampering, invalid JSON/range/maximum,
missing outputs and separate display panels. No synthetic fixture was applied
to the real sample or reported as a model run.

Read-only code review found model archive-to-extracted-file integrity, per-case
GPU IO budgets, and external MHA payload hashing gaps. Added failing regressions
and fixes: verify extracted bytes against published-checksum archives; recheck
expected checkpoint/plan hashes before inference; inspect MHA headers and RAM
before allocation; require embedded LOCAL payloads; check crop probability/
postprocessing budget and saved-map voxel equality. Tests now cover these.
Notebook runner pin must be advanced to the reviewed correction commit before
delivery. Exact next action: finish real unavailable-prediction report/manual
synthetic view checks, demo guide, final commits and push; GPU pilot still pending.

2026-10-14 local delivery check: notebook runner pin now points to reviewed
`1157be07c6954d1ec08f95a2b3bbf6d898f6b44d`. Independent code review findings
were addressed with regressions. Real report generated at ignored
`outputs/milestone-3-report-no-inference/index.html`; checked HTML text,
all three real annotation views and all three explicitly synthetic display
fixtures. Report says **Predictions unavailable**; annotation volumes/bounds
match milestone 2. CT and mask hashes still match acquisition provenance.
Real derived MHA is 101,712,190 bytes; no source scan/mask was changed.
Base environment still has no torch, nnU-Net or SimpleITK; optional SimpleITK
is isolated in ignored `outputs/panorama-io`. Existing three Python processes
and pre-existing inspection-notebook changes are preserved.

GPU access attempt: browser inventory had no enabled surfaces; creating a Colab
tab returned `Browser is not available: iab`. Laptop preflight found no
nvidia-smi. No suitable controllable GPU runtime was available, so a model run
could not be attempted. The demo guide lists exact Colab cells/user actions and
Windows import/report commands. GPU compatibility (including the documented
scikit-image wheel adaptation), actual runtime/peaks, real prediction alignment,
input suitability, license permission for commercial company use and dataset
independence remain unverified. No disease accuracy or clinical risk is claimed.
Delivery verification: commits `cb255cc`, `13e112c`, `1157be0` and `4398779`
were pushed to existing `origin/milestone-1-ct-inspection`. Local and actual
remote HEAD both matched `4398779c7cf67b893845dd08e36ea73b548fd277`.
The notebook's immutable runner source URL was fetched from GitHub and matched
the local reviewed runner. Only the pre-existing inspection notebook remained
modified and unstaged. This closure update records that verification; push and
remote-check it as the final delivery commit. Exact next technical action remains
the nine-cell free Colab smoke test, followed by genuine output import/report.

## Milestone 2 completed (2026-09-30)

The user authorized a second milestone: verify official PANORAMA inference requirements,
then implement and run a local CPU annotation report and demo. Initial Git review found
`eb2f5c5` at local and remote branch head. The tracked inspection notebook has saved
outputs from a pre-existing local run and is modified; preserve and exclude it from
milestone commits. An existing VS Code notebook kernel remains running and untouched.
The real CT/mask pair, manifest and ignored inspection outputs remain present.
No inference has run.

2026-09-30 check: reviewed official PANORAMA source at `d08f235`, Zenodo archive
sizes and separate CC BY-NC 4.0 license; wrote `docs/panorama-inference-plan.md`.
The report implementation passed 8 new synthetic tests. Memory snapshot before
the real case: 671.8 MiB available. The case report generated under ignored
`outputs/`, with three native-axis PNGs visually inspected. The real CT was
512 × 512 × 97 RAS, spacing about 0.916 × 0.916 × 2.5 mm, and the mask
geometry matched without warnings. Source CT/mask SHA256 hashes still match
the recorded acquisition provenance. Annotation label 1: 29,162 voxels,
61.1735 mL, bounds [149, 248, 26]–[280, 309, 59]. Annotation label 2:
3,521 voxels, 7.3860 mL, bounds [246, 275, 37]–[283, 303, 44]. Counts sum
to 25,427,968 voxels, the exact CT voxel count; slice 40 contains 633 label-2
voxels. These are dataset annotations, not predictions.

Full local verification: **63 pytest tests passed**, `ruff check .` passed,
`ruff format --check src tests scripts` reported 14 files formatted,
`pip check` found no broken requirements, and `git diff --check` passed.
HTML text and three PNGs were checked. Planning and implementation were
committed as `71ea725` and `ff22e1f`. `git push origin milestone-1-ct-inspection`
succeeded; `git ls-remote` and local `HEAD` both reported full hash
`ff22e1f08450647c58a20862300f8c95c12648d3` immediately afterward.
The original modified notebook remains unstaged and its existing kernel
untouched.
GPU/weight permissions, runtime requirements and model outputs remain unverified.
Exact next technical action: confirm authorized pretrained weights and a
suitable Colab/company GPU, then perform the one-case pilot in
`docs/panorama-inference-plan.md` after checking CT format/geometry and source overlap.

Earlier detailed evidence is preserved in [the milestone 1 history](docs/progress.md).

## Historical milestone 1–3 checkpoint (superseded above)

- **Complete:** milestone 1, CPU-only CT loading and inspection. Four verified
  commits through `bfda5c9` are pushed to `origin/milestone-1-ct-inspection`.
- **Complete locally:** interruption-safe documentation and resume instructions.
  Initial checks: clean Git state, recent commits reviewed, one existing VS Code
  notebook kernel identified and left running. No unfinished implementation found.
  Documentation links and handoff fields verified; Git whitespace and Ruff checks passed.
- **Not started:** PANORAMA inference. No model weights, CUDA, training, predictions
  or disease-performance evaluation have been introduced.
- **Milestone 2 complete:** PANORAMA source/weight/license review and one CPU
  dataset annotation report on the existing public case. The two related
  commits were pushed and remote HEAD verified; this closure update follows.
- **Exact next technical action after delivery:** obtain permitted pretrained
  weights and suitable Colab/company NVIDIA GPU access for one-case pilot,
  confirm source overlap and preserve geometry in input conversion.
- **Milestone 3 local integration verified:** CT-only export tested on the real
  public case; cleared source-pinned GPU notebook; validated prediction importer
  and separate report panels; 119 software tests passed. Real GPU pilot pending;
  execute the nine Colab cells and import outputs using `docs/milestone-3-demo.md`.

## Completed work and evidence

| Milestone | Completed work | Checks performed | Remaining issues |
|---|---|---|---|
| Environment (`4f17cb6`) | Inspected Windows, CPU, RAM, disk and Python; created `.venv`; added privacy exclusions and design/plan | Core imports, `pip check`, Git exclusions | Limited laptop RAM; use one scan at a time |
| CT inspection (`f2f4775`) | NIfTI loading, metadata, local CSVs, CLI and existing-mask overlays | 36 synthetic software tests and Ruff | No model inference implemented |
| Review fixes (`ceb7bbf`) | Bounded storage-slab reads; mask geometry comparisons in millimeters | Failing regressions then passing fixes; independent format/endian/scaling comparisons | Geometry agreement alone cannot establish patient identity |
| Real-data workflow (`bfda5c9`) | Downloaded one public MSD CT/mask pair; created and executed notebook; documented Windows commands | 55 tests total; lint/format/dependencies; real notebook with and without mask; visual inspection; unchanged file hashes | One-case software check is not cancer-detection validation |
| Resume documentation (2026-09-22; find commit in Git log) | Added root handoff and persistent agent rules; linked README; preserved historical log | Reviewed clean initial Git state, recent commits and remote head; inspected running processes; checked local Markdown links, required handoff fields and whitespace | Existing notebook kernel left untouched; future GPU/runtime and inference planning still pending |
| Milestone 2 (2026-09-30; `71ea725`, `ff22e1f`) | Source-checked PANORAMA inference plan; local CPU annotation report and demo | 63 tests; Ruff lint/format; pip check; real-case three-view inspection; counts, slice and source-hash checks; pushed commits through `ff22e1f` and matched remote HEAD | GPU access, weight/use permissions, genuine model outputs, independent evaluation and explanation remain open |
| Milestone 3 integration (2026-10-14; `cb255cc`, `13e112c`, `1157be0`, `4398779`) | CT-only MHA export, pinned five-fold GPU runner/Colab notebook, output importer, separate report panels and demo | 119 tests; Ruff lint/format; pip check; real conversion with zero measured corner/sample errors; original CT/mask hashes; real unavailable-prediction report and synthetic view checks; review fixes; push/remote/source-pin verification | Real GPU execution and compatibility pending; metadata/input suitability, overlap, independent validation and company weight permission unresolved |

Ruff also passed during this documentation milestone. The 55-test result above belongs to
milestone 1; the real scan and notebook were not rerun merely to update documents.

## What already exists locally - do not recreate by default

- Environment: `.venv/Scripts/python.exe` (Python 3.11.1, 64-bit).
- Notebook: `notebooks/01_inspect_ct.ipynb`; choose **Mirai CT (.venv)** in VS Code.
- Ignored case list: `cases.local.csv`. Read its paths locally; do not publish it.
- Public sample directory: `D:/MiraiData/MSD_Task07`, outside Git. Acquisition
  details and hashes are in its `sample_provenance.json`.
- Ignored outputs: executed notebooks with and without mask, plus rendered PNGs
  under `outputs/`. The inspection notebook has pre-existing local saved outputs
  and remains unstaged; the new tracked Colab notebook has cleared outputs.
- Observed real CT: 512 x 512 x 97, approximately 0.916 x 0.916 x 2.5 mm, RAS.
  Supplied mask geometry matches. Notebook RSS snapshots were about 92-113 MiB,
  not peak-memory guarantees. No full-volume array was cached.
- Resource baseline: 5.95 GiB RAM visible to Windows; approximately 0.55 GiB
  initially free. Store scans on D:; see [environment notes](docs/environment.md).

## Resume procedure

Read this file and `AGENTS.md` first. In native PowerShell at the project root:

```powershell
git status --short --branch
git diff --stat
git diff --cached --stat
git log -6 --oneline
git remote -v
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match 'python|jupyter|pytest|git' } |
    Select-Object ProcessId, Name, CommandLine
```

Inspect full diffs for any changed files and identify unfinished work before
editing. Process commands are for local inspection only; do not commit them or
kernel connection files. A running kernel can be idle: process presence alone
does not prove that a notebook cell is running or finished. Check its UI/output
before launching overlapping work. Do not stop existing kernels or unrelated
processes automatically. PIDs change; re-inspect rather than trusting old PIDs.

Preserve local changes and ignored artifacts. Do not reset, clean, reinstall,
redownload data or repeat completed checks without a reason. After relevant
changes, use the checks in README and record actual results here. If push status
is uncertain, compare `git rev-parse HEAD` with
`git ls-remote origin refs/heads/milestone-1-ct-inspection`; do not assume local
remote-tracking information is current.

## Historical next action - prepared GPU pilot (subsequently completed)

The source review is in `docs/panorama-inference-plan.md`; executable preparation
and the exact nine-cell Colab handoff are in `docs/milestone-3-demo.md`. Input
conversion and output-import code are already implemented and locally tested.
Connect an authorized suitable NVIDIA runtime and execute the notebook with the
existing CT export. Do not infer model performance from local software checks.

Then proceed in small milestones:

1. Confirm a suitable Colab or company GPU runtime and permitted pretrained weights.
2. Run one real CT through the unchanged pretrained baseline, recording runtime,
   memory, model version and genuine outputs. No new model training.
3. Map outputs back to original scan geometry and inspect them against an existing
   annotation. Document what the baseline actually provides and any missing
   requirements from the problem statement.
4. Plan and evaluate an appropriate held-out set after checking training overlap;
   only then report supported performance metrics and assemble the demonstration.

GPU access, inference compatibility and evaluation data independence remain
unverified. Schedule later work within the approximately one-month project window;
do not promise clinical performance or infer it from the existing viewer.

## Update rule for every milestone

At its start, set **In progress** and the exact next action. Update after a
meaningful check, blocker or change of direction, not just at session end. At
completion record **completed work, checks and results, unresolved issues, and
the exact next step**. Commit only verified related changes with this record.
Push at session end; verify the remote result. If interrupted before committing
or pushing, leave an honest pending checkpoint for the next session.

2026-10-28 checkpoint delivery: Git whitespace check passed. Commit attempt was blocked by missing local Git author identity; checkpoint remains staged/uncommitted. Remote inspection reports head e935167913491b448873506f71c859da3249cdec while local HEAD is cb532aa; do not assume this checkout includes newer remote changes. Inspect/fetch and reconcile before any subsequent commit/push. No force-push or history rewrite was attempted.
