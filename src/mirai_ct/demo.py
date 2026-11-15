"""Build an offline research demo from genuine PANORAMA output; never run inference."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

from mirai_ct.cases import Case, read_cases
from mirai_ct.panorama import import_predictions
from mirai_ct.panorama_io import sha256_file, write_json
from mirai_ct.report import generate_report


def extract_bundle(archive: Path, destination: Path) -> Path:
    """Extract a bounded flat-root output ZIP into a new directory only."""
    if destination.exists():
        raise ValueError("Bundle destination already exists.")
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if not 1 <= len(members) <= 100:
            raise ValueError("Unexpected bundle file count.")
        size = sum(member.file_size for member in members)
        if size > 2 * 1024**3:
            raise ValueError("Bundle exceeds the one-case 2 GiB extraction budget.")
        seen = set()
        for member in members:
            name = PurePosixPath(member.filename)
            normalized = name.as_posix().casefold()
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.filename
                or ":" in member.filename
                or stat.S_ISLNK(member.external_attr >> 16)
                or normalized in seen
                or not name.parts
                or any(part.endswith((".", " ")) for part in name.parts)
            ):
                raise ValueError("Unsafe or duplicate ZIP member: " + member.filename)
            if member.filename.endswith(".json") and member.file_size > 1024**2:
                raise ValueError("Bundle JSON exceeds 1 MiB metadata budget.")
            seen.add(normalized)
        if "run.json" not in seen:
            raise ValueError("Expected run.json at the bundle root.")
        parent = destination.parent
        parent.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(parent).free < size * 3 + 64 * 1024**2:
            raise OSError("Insufficient disk for extraction, validated import and report.")
        destination.mkdir()
        source.extractall(destination)
    return destination


def build_demo(
    case: Case,
    input_export: Path,
    bundle: Path,
    output: Path,
    *,
    reference_label: int | None = None,
    reference_description: str = "",
    require_model_products: bool = False,
) -> Path:
    """Validate/import, render synchronized viewer, compare explicit labels and ZIP."""
    if output.exists():
        raise ValueError("Demo output directory already exists; choose a new name.")
    if (reference_label is None) != (not reference_description.strip()):
        raise ValueError("Supply both reference label and reference description, or neither.")
    archive_hash = None
    if bundle.is_file():
        archive_hash = sha256_file(bundle)
        bundle = extract_bundle(bundle, output / "bundle")
    else:
        if not (bundle / "run.json").is_file():
            raise ValueError("Bundle must be a PANORAMA ZIP or folder containing run.json.")
        output.mkdir(parents=True)
    try:
        run = json.loads((bundle / "run.json").read_text(encoding="utf-8"))
        if not isinstance(run, dict):
            raise ValueError("Expected a JSON object in the run manifest.")
        if require_model_products and run.get("model_outputs") is None:
            raise ValueError("This older bundle lacks actual segmentation/probability products.")
        imported = import_predictions(case, input_export, bundle, output / "imported")
        report = generate_report(
            case,
            output / "report",
            imported,
            interactive=True,
            measure_candidates=True,
            reference_label=reference_label,
            reference_description=reference_description,
        )
        report_info = json.loads((report.parent / "report.json").read_text(encoding="utf-8"))
        archive = Path(shutil.make_archive(str(output / "demo-report"), "zip", report.parent))
        write_json(
            output / "demo.json",
            {
                "schema_version": 1,
                "status": "success",
                "case_id": case.case_id,
                "source_sha256": report_info["source_sha256"],
                "input_zip_sha256": archive_hash,
                "report": "report/index.html",
                "shareable_report": archive.name,
                "report_zip_sha256": sha256_file(archive),
                "model_segmentation_available": report_info["model_segmentation_available"],
                "raw_probability_available": report_info["raw_probability_available"],
                "attribution_available": False,
                "clinical_validation": "not established",
            },
        )
        return report
    except Exception as exc:
        write_json(output / "demo-failure.json", {"status": "failed", "error": str(exc)})
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--input-export", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True, help="Output ZIP or extracted folder")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-label", type=int)
    parser.add_argument("--reference-description", default="")
    parser.add_argument("--require-model-products", action="store_true")
    args = parser.parse_args()
    try:
        matches = [case for case in read_cases(args.manifest) if case.case_id == args.case_id]
        if not matches:
            raise ValueError("Case ID not present in manifest.")
        print(
            build_demo(
                matches[0],
                args.input_export,
                args.bundle,
                args.output,
                reference_label=args.reference_label,
                reference_description=args.reference_description,
                require_model_products=args.require_model_products,
            )
        )
    except (OSError, ValueError, RuntimeError, MemoryError, zipfile.BadZipFile) as exc:
        print(f"Demo build stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
