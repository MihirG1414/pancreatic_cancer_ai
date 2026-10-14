# Mirai / Rises.io - resume record

Updated: 2026-10-14 (Asia/Calcutta). This is the authoritative current handoff.

## Milestone 3 in progress (2026-10-14)

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

## Completed work and evidence

| Milestone | Completed work | Checks performed | Remaining issues |
|---|---|---|---|
| Environment (`4f17cb6`) | Inspected Windows, CPU, RAM, disk and Python; created `.venv`; added privacy exclusions and design/plan | Core imports, `pip check`, Git exclusions | Limited laptop RAM; use one scan at a time |
| CT inspection (`f2f4775`) | NIfTI loading, metadata, local CSVs, CLI and existing-mask overlays | 36 synthetic software tests and Ruff | No model inference implemented |
| Review fixes (`ceb7bbf`) | Bounded storage-slab reads; mask geometry comparisons in millimeters | Failing regressions then passing fixes; independent format/endian/scaling comparisons | Geometry agreement alone cannot establish patient identity |
| Real-data workflow (`bfda5c9`) | Downloaded one public MSD CT/mask pair; created and executed notebook; documented Windows commands | 55 tests total; lint/format/dependencies; real notebook with and without mask; visual inspection; unchanged file hashes | One-case software check is not cancer-detection validation |
| Resume documentation (2026-09-22; find commit in Git log) | Added root handoff and persistent agent rules; linked README; preserved historical log | Reviewed clean initial Git state, recent commits and remote head; inspected running processes; checked local Markdown links, required handoff fields and whitespace | Existing notebook kernel left untouched; future GPU/runtime and inference planning still pending |
| Milestone 2 (2026-09-30; `71ea725`, `ff22e1f`) | Source-checked PANORAMA inference plan; local CPU annotation report and demo | 63 tests; Ruff lint/format; pip check; real-case three-view inspection; counts, slice and source-hash checks; pushed commits through `ff22e1f` and matched remote HEAD | GPU access, weight/use permissions, genuine model outputs, independent evaluation and explanation remain open |

Ruff also passed during this documentation milestone. The 55-test result above belongs to
milestone 1; the real scan and notebook were not rerun merely to update documents.

## What already exists locally - do not recreate by default

- Environment: `.venv/Scripts/python.exe` (Python 3.11.1, 64-bit).
- Notebook: `notebooks/01_inspect_ct.ipynb`; choose **Mirai CT (.venv)** in VS Code.
- Ignored case list: `cases.local.csv`. Read its paths locally; do not publish it.
- Public sample directory: `D:/MiraiData/MSD_Task07`, outside Git. Acquisition
  details and hashes are in its `sample_provenance.json`.
- Ignored outputs: executed notebooks with and without mask, plus rendered PNGs
  under `outputs/`. The tracked notebook has no saved output.
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

## Next technical milestone - GPU pilot

The PANORAMA source review is now in `docs/panorama-inference-plan.md`. The next
technical step is to confirm permitted weights/data and a suitable Colab or
company NVIDIA GPU runtime, then run its documented one-case pilot. Do not
infer performance from this milestone's dataset annotation report.

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
