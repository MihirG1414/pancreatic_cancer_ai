# Milestone 2 Case Report Implementation Plan

**Goal:** Generate one local, annotation-only case report from the existing manifest and real CT sample.

**Architecture:** `report.py` owns streamed annotation calculations and HTML/PNG output. Existing case selection, geometry, slice reading and plotting remain their own modules. The CLI is `python -m mirai_ct.report`.

**Tech Stack:** Python 3.11, NiBabel, NumPy, Matplotlib, pytest, Ruff; existing `.venv` only.

## Tasks

1. Write synthetic tests for streamed counts, inclusive bounding boxes, determinant-based physical volumes, unknown units, invalid labels and geometry mismatch. Run and observe missing-feature failures. Implement calculation with one native axis-2 slice in memory; rerun tests.
2. Write synthetic CLI tests for exact manifest selection, generated HTML and three images, no-label case, refusal to overwrite and failure with bad geometry. Run and observe failures. Implement the entry point, escaped HTML, dataset-specific verified label names, and native-plane images; rerun tests.
3. Run all tests, Ruff lint/format and dependency checks. Generate the report from `cases.local.csv` into ignored `outputs/`, inspect the HTML/three images and independently spot-check sample voxels/measurements. Update README and a short demo guide. Re-run checks and review Git diff for private artifacts.
4. Update `PROGRESS.md` with exact evidence and next GPU action. Commit source-checked plan and verified implementation in meaningful groups, push the existing branch, compare local and remote heads. Exclude the existing modified notebook.
