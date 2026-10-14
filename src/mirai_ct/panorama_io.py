"""CT-only PANORAMA input export, with independent physical-space verification."""

import argparse
import hashlib
import itertools
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import psutil

from mirai_ct.cases import Case, read_cases
from mirai_ct.volume import Volume, geometry_warnings, load_volume, memory_status, read_slice

RAS_TO_LPS = np.diag([-1.0, -1.0, 1.0, 1.0])
CLINICAL_FIELDS = ("age", "sex", "study_date", "scanner")


def simpleitk() -> Any:
    """Load optional IO dependency only for conversion/import commands."""
    try:
        import SimpleITK
    except ImportError as exc:
        raise ValueError(
            "Optional SimpleITK is unavailable. See requirements-panorama-io.txt "
            "and docs/milestone-3-demo.md for the separate --target installation."
        ) from exc
    return SimpleITK


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def select_case(manifest: Path, case_id: str) -> Case:
    for case in read_cases(manifest):
        if case.case_id == case_id:
            return case
    raise ValueError(f"Case ID not found in manifest: {case_id}")


def available_bytes() -> int:
    return psutil.virtual_memory().available


def require_memory(shape: tuple[int, ...]) -> int:
    # IO policy: three float32 volumes plus headroom; not an inference minimum.
    required = math.prod(shape) * 12 + 128 * 1024**2
    available = available_bytes()
    if available < required:
        raise MemoryError(
            f"Insufficient available RAM for checked IO: {available / 1024**2:.1f} MiB "
            f"available; conservative IO budget {required / 1024**2:.1f} MiB. "
            "Close unused applications or perform conversion on the GPU host."
        )
    return required


def geometry(scan: Volume) -> dict[str, Any]:
    """Represent native ijk voxel centers in RAS-mm and SimpleITK LPS-mm."""
    issues = geometry_warnings(scan)
    if issues:
        raise ValueError("Ambiguous source geometry: " + " ".join(issues))
    factor = {"mm": 1.0, "meter": 1000.0, "micron": 0.001}.get(scan.header.get_xyzt_units()[0])
    if factor is None:
        raise ValueError("Source spatial units must be known.")
    ras = scan.affine.copy()
    ras[:3] *= factor
    lps = RAS_TO_LPS @ ras
    spacing = np.linalg.norm(lps[:3, :3], axis=0)
    direction = lps[:3, :3] / spacing
    if not np.allclose(direction.T @ direction, np.eye(3), atol=1e-5, rtol=0):
        raise ValueError("Sheared affine cannot be represented as an orthonormal MHA direction.")
    centers = list(itertools.product(*[(0, size - 1) for size in scan.shape]))
    edges = list(itertools.product(*[(-0.5, size - 0.5) for size in scan.shape]))
    return {
        "shape_ijk": list(scan.shape),
        "spacing_mm": spacing.tolist(),
        "origin_lps_mm": lps[:3, 3].tolist(),
        "direction_lps_row_major": direction.ravel().tolist(),
        "affine_ras_mm": ras.tolist(),
        "affine_lps_mm": lps.tolist(),
        "center_corner_indices_ijk": centers,
        "center_corners_lps_mm": [(lps @ [*p, 1])[:3].tolist() for p in centers],
        "edge_corner_indices_ijk": edges,
        "edge_corners_lps_mm": [(lps @ [*p, 1])[:3].tolist() for p in edges],
        "convention": "Native zero-based ijk; centers at integers; edges at -0.5 and size-0.5",
    }


def sitk_affine_lps(image: Any) -> np.ndarray:
    if image.GetDimension() != 3 or image.GetNumberOfComponentsPerPixel() != 1:
        raise ValueError("Expected one scalar 3D MHA image.")
    affine = np.eye(4)
    affine[:3, :3] = np.array(image.GetDirection()).reshape(3, 3) @ np.diag(image.GetSpacing())
    affine[:3, 3] = image.GetOrigin()
    if not np.isfinite(affine).all():
        raise ValueError("MHA geometry contains nonfinite values.")
    return affine


def validate_alignment(image: Any, expected: dict[str, Any]) -> dict[str, float]:
    """No automatic registration/resampling: reject unexplained grid mismatch."""
    if list(image.GetSize()) != expected["shape_ijk"]:
        raise ValueError("Physical alignment failed: dimensions mismatch.")
    actual = sitk_affine_lps(image)
    wanted = np.array(expected["affine_lps_mm"], dtype=float)
    if not np.allclose(actual, wanted, atol=1e-4, rtol=0):
        raise ValueError("Physical alignment failed: origin/direction/spacing mismatch (LPS mm).")
    errors = []
    for group in ("center", "edge"):
        for index, point in zip(
            expected[f"{group}_corner_indices_ijk"],
            expected[f"{group}_corners_lps_mm"],
            strict=True,
        ):
            errors.append(np.linalg.norm((actual @ [*index, 1])[:3] - point))
    maximum = float(max(errors))
    if maximum > 1e-3:
        raise ValueError("Physical alignment failed: physical corners differ by > 0.001 mm.")
    return {"max_corner_error_mm": maximum}


def require_local_mha(path: Path) -> None:
    """Only embedded MHA payloads are covered by a single recorded file hash."""
    with path.open("rb") as stream:
        read_bytes = 0
        while read_bytes < 64 * 1024:
            line = stream.readline(4096)
            read_bytes += len(line)
            if not line:
                break
            if line.strip().startswith(b"ElementDataFile"):
                if line.strip() != b"ElementDataFile = LOCAL":
                    raise ValueError("MHA must embed its voxel payload: ElementDataFile = LOCAL.")
                return
    raise ValueError("Missing/bounded MHA header: expected ElementDataFile = LOCAL.")


def read_aligned_mha(path: Path, grid: dict) -> Any:
    """Check embedded payload, scalar header, dimensions and RAM before reading."""
    require_local_mha(path)
    sitk = simpleitk()
    reader = sitk.ImageFileReader()
    reader.SetFileName(str(path))
    reader.ReadImageInformation()
    if reader.GetDimension() != 3 or reader.GetNumberOfComponents() != 1:
        raise ValueError("Detection/input MHA must be scalar 3D.")
    if list(reader.GetSize()) != grid["shape_ijk"]:
        raise ValueError("Physical alignment failed: MHA dimensions mismatch.")
    require_memory(tuple(reader.GetSize()))
    reader.SetOutputPixelType(sitk.sitkFloat32)
    image = reader.Execute()
    validate_alignment(image, grid)
    return image


def _write_mha(scan: Volume, destination: Path, grid: dict[str, Any]) -> None:
    # MetaImage serializes direction columns; SimpleITK GetDirection uses rows.
    direction_columns = np.array(grid["direction_lps_row_major"]).reshape(3, 3).T.ravel()
    fields = {
        "ObjectType": "Image",
        "NDims": "3",
        "BinaryData": "True",
        "BinaryDataByteOrderMSB": "False",
        "CompressedData": "False",
        "TransformMatrix": " ".join(format(x, ".17g") for x in direction_columns),
        "Offset": " ".join(format(x, ".17g") for x in grid["origin_lps_mm"]),
        "ElementSpacing": " ".join(format(x, ".17g") for x in grid["spacing_mm"]),
        "DimSize": " ".join(map(str, scan.shape)),
        "ElementType": "MET_FLOAT",
        "ElementDataFile": "LOCAL",
    }
    with destination.open("xb") as stream:
        stream.write("".join(f"{key} = {value}\n" for key, value in fields.items()).encode("ascii"))
        for k in range(scan.shape[2]):
            plane = read_slice(scan, 2, k)
            if not np.isfinite(plane).all():
                raise ValueError("CT contains nonfinite scaled intensities.")
            stream.write(np.asarray(plane, dtype="<f4").tobytes(order="F"))


def export_case(case: Case, output: Path, clinical: Path | None = None) -> Path:
    """Export only CT, retaining native voxel order; annotation is never read."""
    if output.exists():
        raise ValueError("Output directory already exists; choose a new directory.")
    sitk = simpleitk()
    scan = load_volume(case.scan_path)
    grid = geometry(scan)
    required = require_memory(scan.shape)
    existing_parent = output.resolve().parent
    while not existing_parent.exists():
        existing_parent = existing_parent.parent
    if shutil.disk_usage(existing_parent).free < math.prod(scan.shape) * 4 + 16 * 1024**2:
        raise ValueError("Insufficient disk space for derived MHA.")
    clinical_info = dict.fromkeys(CLINICAL_FIELDS)
    if clinical is not None:
        clinical_info = json.loads(clinical.read_text(encoding="utf-8-sig"))
        if not isinstance(clinical_info, dict) or set(clinical_info) != set(CLINICAL_FIELDS):
            raise ValueError("Clinical JSON must contain exactly age, sex, study_date, scanner.")
    source_hash = sha256_file(case.scan_path)
    before = memory_status()
    output.mkdir(parents=True)
    mha = output / "ct.mha"
    _write_mha(scan, mha, grid)
    image = sitk.ReadImage(str(mha), sitk.sitkFloat32)
    verified = validate_alignment(image, grid)
    samples = sorted(set(itertools.product(*[(0, size // 2, size - 1) for size in scan.shape])))
    errors, recorded = [], []
    for index in samples:
        expected = float(read_slice(scan, 2, index[2])[index[0], index[1]])
        actual = float(image[index])
        errors.append(abs(actual - expected))
        recorded.append({"ijk": index, "source_scaled": expected, "mha": actual})
    verified["max_intensity_error"] = float(max(errors))
    verified["intensity_samples"] = recorded
    if max(errors) > 1e-5:
        raise ValueError("Conversion changed representative scaled CT intensities.")
    if sha256_file(case.scan_path) != source_hash:
        raise ValueError("Source CT changed during export.")
    write_json(output / "clinical-information-pancreatic-ct.json", clinical_info)
    provenance = {
        "schema_version": 1,
        "case_id": case.case_id,
        "dataset_source": case.dataset_source,
        "source_sha256": source_hash,
        "mha_sha256": sha256_file(mha),
        "annotation_used": False,
        "geometry": grid,
        "verification": verified,
        "suitability": {"contrast_phase": "unknown", "hu_calibration": "unknown"},
        "clinical_metadata": "supplied" if clinical is not None else "unknown; JSON nulls",
        "purpose": "software smoke test; training-data overlap unresolved",
        "memory_before": before,
        "memory_after": memory_status(),
        "io_budget_bytes": required,
        "simpleitk_version": sitk.Version_VersionString(),
    }
    write_json(output / "input-provenance.json", provenance)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Export and verify one CT-only PANORAMA MHA input")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--clinical-json", type=Path, help="Verified local metadata, if available")
    args = parser.parse_args()
    try:
        result = export_case(
            select_case(args.manifest, args.case_id), args.output, args.clinical_json
        )
        print(json.dumps({"export": str(result), "annotation_used": False}))
        return 0
    except (OSError, ValueError, MemoryError, RuntimeError) as exc:
        print(f"Input export failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
