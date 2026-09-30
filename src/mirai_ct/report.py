"""Local, annotation-only case report; never runs model inference."""

# HTML copy stays on complete lines for review alongside the generated report.
# ruff: noqa: E501

import argparse
import html
import json
import sys
from pathlib import Path

import numpy as np

from mirai_ct.cases import Case, read_cases
from mirai_ct.volume import Volume, check_geometry, load_volume, metadata, read_slice

MSD_LABELS = {0: "Background", 1: "Pancreas", 2: "Cancer"}


def annotation_measurements(scan: Volume, mask: Volume) -> list[dict]:
    """Stream native axis-2 planes and aggregate dataset annotation voxels."""
    check_geometry(scan, mask)
    counts: dict[int, int] = {}
    bounds: dict[int, tuple[list[int], list[int]]] = {}
    for k in range(mask.shape[2]):
        plane = read_slice(mask, 2, k)
        if (plane < 0).any() or (plane > 65535).any() or not np.equal(plane, np.floor(plane)).all():
            raise ValueError("Existing mask must contain nonnegative integer label IDs <= 65535.")
        ids, frequencies = np.unique(plane, return_counts=True)
        for raw_id, frequency in zip(ids, frequencies, strict=True):
            label_id = int(raw_id)
            counts[label_id] = counts.get(label_id, 0) + int(frequency)
            if label_id == 0:
                continue
            coordinates = np.argwhere(plane == raw_id)
            minimum = [int(coordinates[:, 0].min()), int(coordinates[:, 1].min()), k]
            maximum = [int(coordinates[:, 0].max()), int(coordinates[:, 1].max()), k]
            if label_id in bounds:
                old_min, old_max = bounds[label_id]
                minimum = [min(a, b) for a, b in zip(old_min, minimum, strict=True)]
                maximum = [max(a, b) for a, b in zip(old_max, maximum, strict=True)]
            bounds[label_id] = (minimum, maximum)

    unit_factor = {"meter": 1000.0, "mm": 1.0, "micron": 0.001}.get(scan.header.get_xyzt_units()[0])
    mm3_per_voxel = (
        abs(float(np.linalg.det(scan.affine[:3, :3]))) * unit_factor**3
        if unit_factor is not None
        else None
    )
    return [
        {
            "label_id": label_id,
            "voxel_count": count,
            "bbox_min_ijk": bounds[label_id][0] if label_id in bounds else None,
            "bbox_max_ijk": bounds[label_id][1] if label_id in bounds else None,
            "volume_mm3": count * mm3_per_voxel if mm3_per_voxel is not None else None,
            "volume_ml": count * mm3_per_voxel / 1000 if mm3_per_voxel is not None else None,
        }
        for label_id, count in sorted(counts.items())
    ]


def _name(label_id: int, source: str) -> str:
    if "msd task07" in source.lower():
        return MSD_LABELS.get(label_id, "Unknown label")
    return "Unverified label meaning"


def _report_html(
    case: Case, scan: Volume, rows: list[dict], has_mask: bool, indices: list[int]
) -> str:
    info = metadata(scan)
    source = html.escape(case.dataset_source)
    title = html.escape(case.case_id)
    table_rows = []
    for row in rows:
        name = html.escape(_name(row["label_id"], case.dataset_source))
        bbox = (
            f"{row['bbox_min_ijk']} to {row['bbox_max_ijk']}"
            if row["bbox_min_ijk"] is not None
            else "—"
        )
        volume = (
            f"{row['volume_mm3']:.2f} mm³ ({row['volume_ml']:.4f} mL)"
            if row["volume_mm3"] is not None
            else "Unavailable: spatial units unknown"
        )
        table_rows.append(
            f"<tr><td>{row['label_id']}</td><td>{name}</td><td>{row['voxel_count']:,}</td>"
            f"<td>{bbox}</td><td>{volume}</td></tr>"
        )
    warning_items = "".join(f"<li>{html.escape(w)}</li>" for w in info["warnings"])
    warnings = (
        f"<ul>{warning_items}</ul>" if warning_items else "<p>None reported by geometry checks.</p>"
    )
    views = "".join(
        f'<figure><img src="axis-{axis}.png" alt="Native axis {axis} CT view'
        f'{" with existing dataset annotation overlay" if has_mask else ""}">'
        f"<figcaption>Native axis {axis}, zero-based slice {indices[axis]}</figcaption></figure>"
        for axis in range(3)
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Case report: {title}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#18252b}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #aaa;padding:.4rem;text-align:left}}img{{max-width:100%;height:auto}}figure{{margin:2rem 0}}.notice{{background:#eef5f8;padding:1rem}}</style></head>
<body><h1>CPU case report: {title}</h1>
<p class="notice"><strong>Dataset annotation only; not a model prediction, clinical diagnosis, or performance result.</strong> Original CT and annotation files were read without modification.</p>
<p>Dataset source: {source}</p>
<h2>CT geometry</h2>
<p>Dimensions (i, j, k): {info["shape"]} voxels<br>
Header spacing: {info["spacing"]} {html.escape(info["spatial_units"])}<br>
Affine spacing: {info["affine_spacing"]} {html.escape(info["spatial_units"])}<br>
Increasing voxel-axis directions: {info["orientation"]}<br>
qform code: {info["qform_code"]}; sform code: {info["sform_code"]}; obliquity: {info["obliquity_degrees"]} degrees</p>
<h3>Geometry warnings</h3>{warnings}
<p>Supplied annotation geometry: {"matched CT shape, units, spacing and affine; source pairing still requires dataset verification" if has_mask else "no annotation supplied"}.</p>
<h2>Dataset annotation measurements</h2>
<p>Label meanings follow the MSD Task07 dataset.json only when the manifest names that dataset. Unknown IDs are not interpreted. Voxels are counted in native geometry. Volume uses the absolute affine determinant and documented spatial units; 1 mL = 1,000 mm³. Background is included in counts but has no region box.</p>
<p>Bounding boxes use original NIfTI voxel indices (i, j, k), zero-based with both minimum and maximum <strong>inclusive</strong>. They enclose all voxels of each label, including disconnected regions. They are axis-aligned in voxel space; direction letters above indicate increasing indices. These are not head/body/tail assignments.</p>
<table><thead><tr><th>Label ID</th><th>Meaning</th><th>Voxel count</th><th>Bounding box, inclusive</th><th>Physical volume</th></tr></thead><tbody>{"".join(table_rows) if rows else '<tr><td colspan="5">No annotation supplied</td></tr>'}</tbody></table>
<h2>Native CT views</h2><p>Each image shows CT and, when supplied, an existing annotation overlay. Planes are original voxel axes, not standardized radiological views. Display level 50/window 400 affects appearance only.</p>{views}
</body></html>"""


def generate_report(case: Case, output: Path) -> Path:
    """Write one HTML report and three PNGs into a new local directory."""
    if output.exists():
        raise ValueError("Output directory already exists; choose a new name to preserve it.")
    scan = load_volume(case.scan_path)
    mask = load_volume(case.label_path) if case.label_path is not None else None
    rows = annotation_measurements(scan, mask) if mask is not None else []
    positives = [row for row in rows if row["label_id"] > 0]
    focus = next((row for row in positives if row["label_id"] == 2), None)
    focus = focus or (positives[0] if positives else None)
    indices = (
        [
            (lo + hi) // 2
            for lo, hi in zip(focus["bbox_min_ijk"], focus["bbox_max_ijk"], strict=True)
        ]
        if focus is not None
        else [size // 2 for size in scan.shape]
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from mirai_ct.visualization import plot_slice

    output.mkdir(parents=True)
    for axis in range(3):
        figure = plot_slice(scan, axis=axis, index=indices[axis], mask=mask)
        try:
            figure.savefig(output / f"axis-{axis}.png", dpi=120)
        finally:
            plt.close(figure)
    report = output / "index.html"
    report.write_text(_report_html(case, scan, rows, mask is not None, indices), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-case CPU dataset annotation report; no inference."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", type=Path, required=True, help="New local output directory")
    args = parser.parse_args()
    try:
        matches = [case for case in read_cases(args.manifest) if case.case_id == args.case_id]
        if not matches:
            raise ValueError(f"Case ID not found in manifest: {args.case_id}")
        report = generate_report(matches[0], args.output)
        print(json.dumps({"report": str(report), "kind": "dataset annotation; no inference"}))
        return 0
    except (OSError, ValueError, MemoryError) as exc:
        print(f"Report failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
