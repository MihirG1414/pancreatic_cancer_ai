# Mirai / Rises.io - resume record

Updated: 2026-10-28 (Asia/Calcutta). This is the authoritative current handoff.

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

## Current checkpoint

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

## Next technical action - execute the prepared GPU pilot

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
