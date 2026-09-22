# Mirai project working instructions

## Resume before acting

- Read root `PROGRESS.md` first; it is the current checkpoint. `docs/progress.md`
  is historical evidence, not a competing current task list.
- Inspect Git status, staged/unstaged diffs, recent commits and remotes before
  editing. Inspect relevant running processes and existing outputs for unfinished
  work. Preserve changes, active notebook kernels and unrelated processes.
- Continue the recorded exact next step. Do not repeat completed work, reinstall
  the environment or redownload inputs without evidence that it is necessary.

## Work in small milestones

- For nontrivial work, follow specification, architecture/risks, plan, tasks,
  tests, implementation and review. Use relevant Superpowers skills.
- At milestone start and after meaningful checks/blockers, update `PROGRESS.md`.
  Every completed milestone records work done, actual checks/results, unresolved
  issues and an exact actionable next step. Do not rely on a final chat summary.
- Test important features, run available lint/type checks, and manually verify
  changed user-facing flows. Update documentation when behavior changes.
- Commit verified related changes and progress updates with clear messages and
  actual dates. Exclude unrelated changes. Routine commits and pushes are
  authorized; push completed commits at session end and verify the remote head.
  Never force-push, rewrite history, create empty commits or manufacture activity.
- Record pending/failed actions honestly. A previous push result does not prove
  that a later commit is pushed; inspect Git and remote state when resuming.

## Project constraints

- Native Windows/PowerShell, Ryzen 5 3500U, 8 GB installed RAM, integrated graphics.
  Use the existing `.venv`, process one scan at a time and monitor memory.
- Preserve original scan geometry. Keep CT intake/inspection separate from
  inference. Use pretrained PANORAMA later; do not train a new model.
- Do not download a full dataset or model ensemble, or install CUDA, as part of
  preparation. Determine appropriate compute before inference integration.
- Distinguish synthetic software checks, real CT inspection and genuine model
  outputs. Never fabricate predictions or claim untested performance/completion.
- Keep code simple, typed and modular; avoid unnecessary dependencies. Store
  secrets/configuration in environment variables where appropriate.
- Exclude datasets, patient information, weights, credentials, environments,
  private source documents and generated outputs from Git. Clear outputs from
  tracked notebooks. Do not commit `.env`, connection files or copyrighted PDFs.
- The local problem statement defines the broader project; the latest user
  instruction defines the current milestone. Do not expand scope silently.
