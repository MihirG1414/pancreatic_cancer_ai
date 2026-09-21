"""Small local case manifests; no patient identifiers or inference labels."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Case:
    case_id: str
    scan_path: Path
    label_path: Path | None
    dataset_source: str


def read_cases(path: str | Path) -> list[Case]:
    """Resolve paths relative to the CSV; do not open every scan."""
    path = Path(path).resolve()
    required = ["case_id", "scan_path", "label_path", "dataset_source"]
    cases = []
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != required:
            raise ValueError("CSV header must be: " + ",".join(required))
        for line_number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row {line_number}.")
            row = {key: value.strip() for key, value in row.items()}
            if not all(row[key] for key in ("case_id", "scan_path", "dataset_source")):
                raise ValueError(f"Missing required value on CSV row {line_number}.")
            if row["case_id"] in seen:
                raise ValueError(f"Duplicate case ID on CSV row {line_number}.")
            seen.add(row["case_id"])
            cases.append(
                Case(
                    row["case_id"],
                    (path.parent / row["scan_path"]).resolve(),
                    (path.parent / row["label_path"]).resolve() if row["label_path"] else None,
                    row["dataset_source"],
                )
            )
    return cases
