# Mirai / Rises.io - resume record

Updated: 2026-09-22 (Asia/Calcutta). This is the authoritative current handoff.
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
- **Exact next technical action:** prepare the planning-only PANORAMA inference
  document described below. Inference execution is outside this documentation milestone.
- **Delivery checkpoint:** documentation is ready to commit and push. On resume,
  inspect Git and remote HEAD to determine whether delivery finished; do not
  repeat these edits because this pre-commit checkpoint says delivery was pending.

## Completed work and evidence

| Milestone | Completed work | Checks performed | Remaining issues |
|---|---|---|---|
| Environment (`4f17cb6`) | Inspected Windows, CPU, RAM, disk and Python; created `.venv`; added privacy exclusions and design/plan | Core imports, `pip check`, Git exclusions | Limited laptop RAM; use one scan at a time |
| CT inspection (`f2f4775`) | NIfTI loading, metadata, local CSVs, CLI and existing-mask overlays | 36 synthetic software tests and Ruff | No model inference implemented |
| Review fixes (`ceb7bbf`) | Bounded storage-slab reads; mask geometry comparisons in millimeters | Failing regressions then passing fixes; independent format/endian/scaling comparisons | Geometry agreement alone cannot establish patient identity |
| Real-data workflow (`bfda5c9`) | Downloaded one public MSD CT/mask pair; created and executed notebook; documented Windows commands | 55 tests total; lint/format/dependencies; real notebook with and without mask; visual inspection; unchanged file hashes | One-case software check is not cancer-detection validation |
| Resume documentation (2026-09-22; find commit in Git log) | Added root handoff and persistent agent rules; linked README; preserved historical log | Reviewed clean initial Git state, recent commits and remote head; inspected running processes; checked local Markdown links, required handoff fields and whitespace | Existing notebook kernel left untouched; future GPU/runtime and inference planning still pending |

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

## Next technical milestone - planning only

**Exact next step after this documentation milestone:** read the local problem
statement and existing scope, inspect the official PANORAMA baseline's current
inference code/configuration, and write `docs/panorama-inference-plan.md`.
Record the required input/preprocessing, actual model outputs, dependency and
weight sizes, licensing, compute requirements, data-overlap risks, and one-case
acceptance checks. Do not install inference frameworks or download weights as
part of that planning step.

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
