"""Docker-free GPU orchestration of the pinned official five-fold PANORAMA baseline.

No baseline functions are copied or altered. This module is intended for a
separate NVIDIA runtime; importing it does not import torch or download weights.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import stat
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import psutil

from mirai_ct.panorama_io import (
    CLINICAL_FIELDS,
    sha256_file,
    simpleitk,
    sitk_affine_lps,
    validate_alignment,
    write_json,
)

BASELINE_REV = "d08f2356fa70d9460881fec0aedba4ebd1566c7e"
NNUNET_REV = "834b80ffa8517e6cd2981982eb7edc75b2d131d8"
STAGES = (
    {
        "dataset": "Dataset103_PANORAMA_baseline_Pancreas_Segmentation",
        "trainer": "nnUNetTrainer",
        "checkpoint": "checkpoint_final.pth",
        "md5": "d4c7e9666157e712f90649086ed395a5",
        "size": 613484406,
    },
    {
        "dataset": "Dataset104_PANORAMA_baseline_PDAC_Detection",
        "trainer": "nnUNetTrainer_Loss_CE_checkpoints",
        "checkpoint": "checkpoint_best_panorama.pth",
        "md5": "ae1bc3ff68e4e0b9f7fa15afca339cf8",
        "size": 1143995491,
    },
)
NUMERICAL_VERSIONS = {
    "torch": "2.4.0",
    "nnunetv2": "2.5.1",
    "numpy": "1.24.4",
    "scipy": "1.10.1",
    "SimpleITK": "2.4.0",
    "report-guided-annotation": "0.2.7",
    "dynamic-network-architectures": "0.3.1",
    "acvl-utils": "0.2",
    "scikit-image": "0.21.0",
}


def preflight(root: Path) -> dict[str, Any]:
    """Conservative pilot policy; measured baseline minimums remain unknown."""
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free,driver_version",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    if len(lines) != 1:
        raise ValueError("Pilot expects one visible NVIDIA GPU; select one runtime GPU.")
    name, total, free, driver = [item.strip() for item in lines[0].split(",")]
    snapshot = {
        "gpu": name,
        "vram_total_mib": float(total),
        "vram_free_mib": float(free),
        "driver": driver,
        "host_available_mib": psutil.virtual_memory().available / 1024**2,
        "host_total_mib": psutil.virtual_memory().total / 1024**2,
        "disk_free_gib": shutil.disk_usage(root).free / 1024**3,
        "policy": "free VRAM >=12 GiB, host available >=8 GiB, disk >=15 GiB; not measured minima",
    }
    if (
        float(free) < 12 * 1024
        or snapshot["host_available_mib"] < 8 * 1024
        or snapshot["disk_free_gib"] < 15
    ):
        raise ValueError("Runtime below conservative pilot resource gate: " + json.dumps(snapshot))
    return snapshot


def verify_archive(path: Path, md5: str, size: int) -> None:
    if path.stat().st_size != size:
        raise ValueError(f"Archive size mismatch: {path.name}")
    digest = hashlib.md5()  # Published Zenodo checksum, not a security signature.
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != md5:
        raise ValueError(f"Published checksum mismatch: {path.name}")


def safe_extract(archive: Path, destination: Path) -> None:
    """Reject traversal, symlinks and oversized archives before extracting."""
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if sum(member.file_size for member in members) > 5 * 1024**3:
            raise ValueError("Archive exceeds 5 GiB extraction budget.")
        for member in members:
            name = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.filename
                or ":" in member.filename
                or stat.S_ISLNK(mode)
            ):
                raise ValueError("Unsafe ZIP member: " + member.filename)
        destination.mkdir(parents=True, exist_ok=True)
        zipped.extractall(destination)


def _download(url: str, destination: Path, md5: str, size: int) -> None:
    if destination.exists():
        verify_archive(destination, md5, size)
        return
    partial = destination.with_suffix(destination.suffix + ".part")
    if partial.exists():
        raise ValueError(
            f"Incomplete download exists: {partial.name}; remove that partial and retry."
        )
    request = urllib.request.Request(url, headers={"User-Agent": "Mirai-PANORAMA-pilot/1"})
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("xb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    verify_archive(partial, md5, size)
    partial.rename(destination)


def prepare_weights(root: Path, permitted: bool) -> Path:
    if not permitted:
        raise ValueError("Confirm permitted CC BY-NC 4.0 weight use before downloading.")
    preflight(root)
    downloads, models = root / "archives", root / "models"
    downloads.mkdir(exist_ok=True)
    license_file = downloads / "LICENSE.txt"
    _download(
        "https://zenodo.org/records/11160381/files/LICENSE.txt?download=1",
        license_file,
        "bd06674082883348303979bec15d9c2c",
        19917,
    )
    records = []
    for stage in STAGES:
        filename = stage["dataset"] + ".zip"
        archive = downloads / filename
        _download(
            f"https://zenodo.org/records/11160381/files/{filename}?download=1",
            archive,
            stage["md5"],
            stage["size"],
        )
        folder = models / stage["dataset"]
        if not folder.exists():
            safe_extract(archive, models)
        records.append(
            {
                "filename": filename,
                "published_md5": stage["md5"],
                "size": stage["size"],
                "sha256": sha256_file(archive),
            }
        )
    validate_models(models)
    write_json(
        root / "weight-provenance.json",
        {
            "record": "https://zenodo.org/records/11160381",
            "license": "CC BY-NC 4.0",
            "permission_confirmed_by_operator": True,
            "archives": records,
            "license_sha256": sha256_file(license_file),
        },
    )
    return models


def validate_models(root: Path) -> dict[str, str]:
    hashes = {}
    for stage in STAGES:
        folder = root / stage["dataset"] / f"{stage['trainer']}__nnUNetPlans__3d_fullres"
        paths = [folder / name for name in ("plans.json", "dataset.json")]
        paths += [folder / f"fold_{fold}" / stage["checkpoint"] for fold in range(5)]
        for path in paths:
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"Missing model checkpoint/metadata: {path.relative_to(root)}")
            hashes[path.relative_to(root).as_posix()] = sha256_file(path)
    return hashes


def prediction_command(stage: dict, input_dir: Path, output_dir: Path) -> list[str]:
    return [
        "nnUNetv2_predict",
        "-d",
        stage["dataset"],
        "-i",
        str(input_dir),
        "-o",
        str(output_dir),
        "-c",
        "3d_fullres",
        "-tr",
        stage["trainer"],
        "--disable_progress_bar",
        "--continue_prediction",
        "-f",
        "0",
        "1",
        "2",
        "3",
        "4",
        "-chk",
        stage["checkpoint"],
        "--save_probabilities",
        "-npp",
        "1",
        "-nps",
        "1",
        "-device",
        "cuda",
    ]


def validate_pancreas(values: np.ndarray) -> None:
    # Preserve official CropPancreasROI's requirement: binary with both labels.
    if not np.array_equal(np.unique(values), [0, 1]):
        raise ValueError("Stage 1 predicted pancreas mask is empty or not binary with background.")


def validate_crop(crop: dict, full_size: tuple, cropped_size: tuple) -> None:
    for axis, size, extent in zip("xyz", full_size, cropped_size, strict=True):
        lo, hi = crop[f"{axis}_start"], crop[f"{axis}_finish"]
        if (
            not isinstance(lo, int)
            or not isinstance(hi, int)
            or not 0 <= lo < hi <= size
            or hi - lo != extent
        ):
            raise ValueError("Stage 1 produced an invalid or empty pancreas crop.")


def validate_stage_grid(image: Any, expected_size: tuple, reference: Any) -> None:
    if tuple(image.GetSize()) != tuple(expected_size) or not np.allclose(
        sitk_affine_lps(image), sitk_affine_lps(reference), rtol=0, atol=1e-4
    ):
        raise ValueError("Stage output grid differs from its input physical grid.")


def _versions() -> dict[str, str]:
    versions = {name: importlib.metadata.version(name) for name in NUMERICAL_VERSIONS}
    for name, expected in NUMERICAL_VERSIONS.items():
        if versions[name].split("+")[0] != expected:
            raise ValueError(
                f"Unsupported dependency version: {name}={versions[name]}; expected {expected}"
            )
    direct = json.loads(
        importlib.metadata.distribution("nnunetv2").read_text("direct_url.json") or "{}"
    )
    if direct.get("vcs_info", {}).get("commit_id") != NNUNET_REV:
        raise ValueError("nnU-Net must be installed from the pinned source revision.")
    return versions


class ResourceMonitor:
    """Sample host process-tree RSS and whole-device GPU use; not exact peaks."""

    def __init__(self) -> None:
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.result = {
            "samples": 0,
            "interval_seconds": 1,
            "max_tree_rss_mib": 0.0,
            "max_device_used_mib": 0.0,
            "min_host_available_mib": float("inf"),
        }

    def _sample(self) -> None:
        while not self.stop.is_set():
            try:
                parent = psutil.Process()
                rss = parent.memory_info().rss
                for child in parent.children(recursive=True):
                    try:
                        rss += child.memory_info().rss
                    except psutil.Error:
                        pass
                used = float(
                    subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                        text=True,
                        timeout=5,
                    ).strip()
                )
                self.result["samples"] += 1
                self.result["max_tree_rss_mib"] = max(
                    self.result["max_tree_rss_mib"], rss / 1024**2
                )
                self.result["max_device_used_mib"] = max(self.result["max_device_used_mib"], used)
                self.result["min_host_available_mib"] = min(
                    self.result["min_host_available_mib"],
                    psutil.virtual_memory().available / 1024**2,
                )
            except (psutil.Error, OSError, ValueError, subprocess.SubprocessError):
                pass
            self.stop.wait(1)

    def __enter__(self) -> "ResourceMonitor":
        self.thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop.set()
        self.thread.join(timeout=6)
        if not self.result["samples"]:
            self.result["min_host_available_mib"] = None


def run_pilot(input_dir: Path, baseline: Path, root: Path, run_dir: Path) -> Path:
    """Run two original pretrained stages, then package only validated outputs."""
    if run_dir.exists():
        raise ValueError("Run directory exists; choose a fresh path to exclude stale outputs.")
    resources = preflight(root)
    versions = _versions()
    import torch

    if not torch.cuda.is_available():
        raise ValueError("PyTorch cannot access the selected NVIDIA GPU.")
    revision = subprocess.check_output(
        ["git", "-C", str(baseline), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != BASELINE_REV:
        raise ValueError("Baseline source revision differs from the reviewed pin.")
    if subprocess.check_output(
        ["git", "-C", str(baseline), "status", "--porcelain"], text=True
    ).strip():
        raise ValueError("Baseline source contains local modifications; use the unmodified pin.")
    model_hashes = validate_models(root / "models")
    weights = json.loads((root / "weight-provenance.json").read_text())
    provenance = json.loads((input_dir / "input-provenance.json").read_text())
    if provenance.get("annotation_used") is not False:
        raise ValueError("Input must be a CT-only export.")
    if sha256_file(input_dir / "ct.mha") != provenance["mha_sha256"]:
        raise ValueError("Exported CT checksum mismatch.")
    clinical = json.loads((input_dir / "clinical-information-pancreatic-ct.json").read_text())
    if not isinstance(clinical, dict) or set(clinical) != set(CLINICAL_FIELDS):
        raise ValueError("Clinical input fields are missing.")
    import nnunetv2

    trainer = (
        Path(nnunetv2.__file__).parent / "training/nnUNetTrainer/customTrainerCEcheckpoints.py"
    )
    source_trainer = baseline / "src/customTrainerCEcheckpoints.py"
    if trainer.exists() and sha256_file(trainer) != sha256_file(source_trainer):
        raise ValueError("A conflicting custom trainer is already installed.")
    shutil.copyfile(source_trainer, trainer)
    # nnU-Net paths are initialized in child processes after setting these vars.
    os.environ.update(
        nnUNet_results=str(root / "models"),
        nnUNet_raw=str(root / "raw"),
        nnUNet_preprocessed=str(root / "preprocessed"),
        nnUNet_compile="false",
    )
    sys.path.insert(0, str(baseline / "src"))
    from data_utils import CropPancreasROI, GetFullSizDetectionMap, PostProcessing, resample_img

    sitk = simpleitk()
    ct = sitk.ReadImage(str(input_dir / "ct.mha"), sitk.sitkFloat32)
    validate_alignment(ct, provenance["geometry"])
    run_dir.mkdir(parents=True)
    bundle = run_dir / "bundle"
    bundle.mkdir()
    record = {
        "schema_version": 1,
        "status": "running",
        "execution_kind": "pretrained-inference",
        "started_utc": datetime.now(UTC).isoformat(),
        "baseline_revision": revision,
        "nnunet_revision": NNUNET_REV,
        "folds": [0, 1, 2, 3, 4],
        "versions": versions,
        "resources_before": resources,
        "model_sha256": model_hashes,
        "weights": weights,
        "input_mha_sha256": provenance["mha_sha256"],
        "source_sha256": provenance["source_sha256"],
        "clinical_unknown_fields": [key for key, value in clinical.items() if value is None],
        "clinical_consumed_by_model": False,
        "licenses": {
            "baseline_code": "Apache-2.0",
            "weights": "CC BY-NC 4.0",
            "dataset": provenance["dataset_source"],
        },
        "adaptations": [
            "Docker-free paths; calls unchanged official data_utils",
            "one preprocessing/export worker; all five folds and default TTA/step size",
            "clinical nulls retained and not printed; baseline only prints those fields",
            "scikit-image 0.21.0 wheel replaces build-log 0.19.3; GPU compatibility pending",
        ],
        "mirai_runner_sha256": sha256_file(Path(__file__)),
        "stages": [],
    }
    write_json(bundle / "run.json", record)
    start = time.monotonic()
    monitor = ResourceMonitor()
    try:
        with monitor:
            for name in ("input_lowres", "output_lowres", "input_fullres", "output_fullres"):
                (run_dir / name).mkdir()
            resampled = resample_img(ct, (4.5, 4.5, 9.0), is_label=False, out_size=[])
            if any(size < 1 for size in resampled.GetSize()):
                raise ValueError("Low-resolution CT is empty.")
            sitk.WriteImage(resampled, str(run_dir / "input_lowres/scan_0000.nii.gz"))
            for number, stage in enumerate(STAGES):
                suffix = "lowres" if number == 0 else "fullres"
                cmd = prediction_command(
                    stage, run_dir / f"input_{suffix}", run_dir / f"output_{suffix}"
                )
                began = time.monotonic()
                with (run_dir / f"stage-{number + 1}.log").open("w", encoding="utf-8") as log:
                    subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
                record["stages"].append(
                    {"stage": number + 1, "command": cmd, "seconds": time.monotonic() - began}
                )
                if number == 0:
                    mask = sitk.ReadImage(str(run_dir / "output_lowres/scan.nii.gz"))
                    validate_stage_grid(mask, resampled.GetSize(), resampled)
                    validate_pancreas(sitk.GetArrayViewFromImage(mask))
                    crop, coordinates = CropPancreasROI(ct, mask, [100, 50, 15])
                    validate_crop(coordinates, ct.GetSize(), crop.GetSize())
                    record["crop_coordinates_ijk_exclusive_finish"] = coordinates
                    sitk.WriteImage(crop, str(run_dir / "input_fullres/scan_0000.nii.gz"))
                    del mask, resampled
            predicted = run_dir / "output_fullres/scan.nii.gz"
            fullres_mask = sitk.ReadImage(str(predicted))
            validate_stage_grid(fullres_mask, crop.GetSize(), crop)
            del fullres_mask, crop
            with np.load(run_dir / "output_fullres/scan.npz", allow_pickle=False) as prediction:
                postprocessed = PostProcessing(prediction, str(predicted))
            detection, score = GetFullSizDetectionMap(postprocessed, coordinates, ct)
            validate_alignment(detection, provenance["geometry"])
            values = sitk.GetArrayViewFromImage(detection)
            if not np.isfinite(values).all() or np.min(values) < 0 or np.max(values) > 1:
                raise ValueError("Detection map contains invalid values.")
            if (
                not np.isfinite(score)
                or not 0 <= score <= 1
                or not np.isclose(score, values.max(), atol=1e-6)
            ):
                raise ValueError("Invalid baseline patient-level score.")
            map_dir = bundle / "images/pdac-detection-map"
            map_dir.mkdir(parents=True)
            sitk.WriteImage(detection, str(map_dir / "detection_map.mha"))
            write_json(bundle / "pdac-likelihood.json", score)
            # Confirm actual on-disk output, not just an in-memory result.
            restored = sitk.ReadImage(str(map_dir / "detection_map.mha"))
            validate_alignment(restored, provenance["geometry"])
            shutil.copyfile(input_dir / "input-provenance.json", bundle / "input-provenance.json")
            shutil.copyfile(root / "archives/LICENSE.txt", bundle / "WEIGHTS-LICENSE.txt")
            record["output_sha256"] = {
                name: sha256_file(bundle / name)
                for name in (
                    "images/pdac-detection-map/detection_map.mha",
                    "pdac-likelihood.json",
                    "input-provenance.json",
                    "WEIGHTS-LICENSE.txt",
                )
            }
            record["status"] = "success"
    except Exception as exc:
        record["status"] = "failed"
        record["failure_type"] = type(exc).__name__
        record["failure_message"] = str(exc)
        raise
    finally:
        record["runtime_seconds"] = time.monotonic() - start
        record["finished_utc"] = datetime.now(UTC).isoformat()
        record["resource_samples"] = monitor.result
        write_json(bundle / "run.json", record)
        with (run_dir / "environment.txt").open("w", encoding="utf-8") as environment:
            subprocess.run([sys.executable, "-m", "pip", "freeze"], check=True, stdout=environment)
    shutil.copyfile(run_dir / "environment.txt", bundle / "environment.txt")
    for path in run_dir.glob("stage-*.log"):
        shutil.copyfile(path, bundle / path.name)
    archive = run_dir / "panorama-output.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(bundle))
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description="NVIDIA GPU-only PANORAMA five-fold pilot")
    parser.add_argument("action", choices=("preflight", "weights", "run"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--permitted-noncommercial-use", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "preflight":
            print(json.dumps(preflight(args.root), indent=2))
        elif args.action == "weights":
            print(prepare_weights(args.root, args.permitted_noncommercial_use))
        else:
            if not all((args.input, args.baseline, args.run_dir)):
                raise ValueError("run requires --input, --baseline and --run-dir")
            print(
                run_pilot(
                    args.input.resolve(),
                    args.baseline.resolve(),
                    args.root.resolve(),
                    args.run_dir.resolve(),
                )
            )
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"GPU pilot failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
