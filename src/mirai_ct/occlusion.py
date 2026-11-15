"""Signed block occlusion of a fixed model target; CPU contract, no fake inference."""

import hashlib
import json
import math
import time
from collections.abc import Callable
from itertools import product
from pathlib import Path

import numpy as np

from mirai_ct.panorama_io import write_json

METHOD = "fixed-target-block-occlusion-v2"
TARGET = "mean stage-2 class-1 probability over original predicted class-1 voxels"
BASELINE_POLICY = {
    "max_abs": 0.005,
    "mean_abs": 0.0001,
    "target_mae": 0.0005,
    "target_mean_abs": 0.0001,
}
MIN_CONTROL_FLOOR = 0.0001


def partition_bounds(start: list[int], finish: list[int]) -> list[list[list[int]]]:
    """Eight nonoverlapping xyz boxes with exclusive finish, including odd sizes."""
    if (
        len(start) != 3
        or len(finish) != 3
        or any(type(v) is not int for v in [*start, *finish])
        or any(a < 0 or b - a < 2 for a, b in zip(start, finish, strict=True))
    ):
        raise ValueError("Occlusion region needs three integer bounds at least two voxels wide.")
    axes = [[(a, (a + b) // 2), ((a + b) // 2, b)] for a, b in zip(start, finish, strict=True)]
    return [[list(a), list(b)] for pairs in product(*axes) for a, b in [zip(*pairs, strict=True)]]


def _digest(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def _save(path: Path, result: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    write_json(temporary, result)
    temporary.replace(path)


def validate_blocks(blocks: list, shape_ijk: list[int]) -> None:
    if not isinstance(blocks, list) or len(blocks) != 8:
        raise ValueError("Exactly eight complete occlusion blocks required.")
    try:
        start = [min(b[0][i] for b in blocks) for i in range(3)]
        finish = [max(b[1][i] for b in blocks) for i in range(3)]
        if blocks != partition_bounds(start, finish) or any(
            b > size for b, size in zip(finish, shape_ijk, strict=True)
        ):
            raise ValueError("Invalid occlusion block coverage.")
    except (TypeError, IndexError, KeyError) as exc:
        raise ValueError("Invalid occlusion block bounds.") from exc


def _probability(values: np.ndarray, shape: tuple) -> None:
    if (
        values.shape != shape
        or not np.isfinite(values).all()
        or np.any((values < 0) | (values > 1))
    ):
        raise ValueError("Predictor returned invalid class-1 probabilities.")


def _comparison(values: np.ndarray, reference: np.ndarray, target: np.ndarray) -> dict:
    difference = values.astype(np.float64) - reference
    return {
        "max_abs": float(np.abs(difference).max()),
        "mean_abs": float(np.abs(difference).mean()),
        "target_mae": float(np.abs(difference[target]).mean()),
        "target_mean_abs": abs(float(difference[target].mean())),
    }


def _check_metrics(metrics: dict) -> None:
    if (
        not isinstance(metrics, dict)
        or set(metrics) != set(BASELINE_POLICY)
        or any(
            type(metrics[key]) not in (int, float)
            or not math.isfinite(metrics[key])
            or not 0 <= metrics[key] <= limit
            for key, limit in BASELINE_POLICY.items()
        )
    ):
        raise ValueError("Baseline failed reproduction policy: " + str(metrics))


def validate_controls(result: dict) -> None:
    if result.get("spec", {}).get("baseline_policy") != BASELINE_POLICY:
        raise ValueError("Unsupported unchanged-input control policy.")
    controls = result.get("controls")
    saved = result.get("saved_target_mean")
    if (
        not isinstance(controls, list)
        or len(controls) != 2
        or type(saved) not in (int, float)
        or not math.isfinite(saved)
        or not 0 <= saved <= 1
    ):
        raise ValueError("Two unchanged-input controls and original target mean required.")
    scores = []
    for control in controls:
        if (
            not isinstance(control, dict)
            or type(control.get("score")) not in (int, float)
            or not math.isfinite(control["score"])
            or not 0 <= control["score"] <= 1
        ):
            raise ValueError("Invalid unchanged-input control score.")
        _check_metrics(control.get("to_saved"))
        if not math.isclose(
            abs(control["score"] - saved), control["to_saved"]["target_mean_abs"], abs_tol=1e-8
        ):
            raise ValueError("Control score differs from its reproduction metrics.")
        scores.append(control["score"])
    _check_metrics(result.get("repeatability"))
    if not math.isclose(
        abs(scores[0] - scores[1]), result["repeatability"]["target_mean_abs"], abs_tol=1e-8
    ):
        raise ValueError("Unchanged-input repeatability score mismatch.")
    baseline = sum(scores) / 2
    floor = max(MIN_CONTROL_FLOOR, abs(scores[0] - scores[1]), abs(baseline - saved))
    for key, expected in [
        ("baseline_score", baseline),
        ("control_floor", floor),
        ("baseline_max_error", max(c["to_saved"]["max_abs"] for c in controls)),
    ]:
        value = result.get(key)
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or not math.isclose(value, expected, abs_tol=1e-9)
        ):
            raise ValueError("Control summary mismatch: " + key)


def validate_effects(result: dict, blocks: list, *, complete: bool) -> None:
    validate_controls(result)
    score = result.get("baseline_score")
    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("Invalid occlusion baseline score.")
    error = result.get("baseline_max_error")
    if (
        type(error) not in (int, float)
        or not math.isfinite(error)
        or not 0 <= error <= BASELINE_POLICY["max_abs"]
    ):
        raise ValueError("Baseline reproduction evidence is invalid.")
    rows = result.get("blocks")
    if not isinstance(rows, list) or len(rows) > 8 or (complete and len(rows) != 8):
        raise ValueError("Incomplete occlusion evidence.")
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or row.get("bounds_ijk") != blocks[index]:
            raise ValueError("Occlusion evidence block bounds/order differ.")
        values = [row.get(key) for key in ("occluded_score", "effect", "seconds")]
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError("Nonfinite occlusion evidence.")
        value, effect, seconds = values
        if (
            not 0 <= value <= 1
            or seconds < 0
            or not math.isclose(score - value, effect, abs_tol=1e-9)
        ):
            raise ValueError("Occlusion score/effect mismatch.")


def calculate_effects(
    data_kji: np.ndarray,
    target_kji: np.ndarray,
    reference_probability: np.ndarray,
    blocks: list,
    predict: Callable[[np.ndarray], np.ndarray],
    *,
    journal: Path,
    fill_value: float = 50.0,
    identity: dict | None = None,
) -> dict:
    """Two unchanged controls + eight genuine calls; resume identical passes only."""
    if (
        data_kji.ndim != 3
        or target_kji.shape != data_kji.shape
        or not np.isfinite(data_kji).all()
        or not np.isin(target_kji, [0, 1]).all()
        or not target_kji.any()
        or not math.isfinite(fill_value)
    ):
        raise ValueError("Finite 3D CT and a nonempty fixed binary target required.")
    _probability(reference_probability, data_kji.shape)
    validate_blocks(blocks, list(data_kji.shape[::-1]))
    target = target_kji.astype(bool)
    spec = {
        "method": METHOD,
        "target": TARGET,
        "fill_value": fill_value,
        "data_sha256": _digest(data_kji),
        "target_sha256": _digest(target),
        "reference_probability_sha256": _digest(reference_probability),
        "block_bounds_ijk": blocks,
        "shape_ijk": list(data_kji.shape[::-1]),
        "identity": identity or {},
        "baseline_policy": BASELINE_POLICY,
    }
    fingerprint = hashlib.sha256(
        json.dumps(spec, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    if journal.exists():
        if journal.stat().st_size > 1024**2:
            raise ValueError("Occlusion journal exceeds 1 MiB.")
        result = json.loads(journal.read_text(encoding="utf-8"))
        if (
            not isinstance(result, dict)
            or result.get("fingerprint") != fingerprint
            or result.get("spec") != spec
        ):
            raise ValueError("Resume identity differs; choose a fresh output directory.")
        validate_effects(result, blocks, complete=result.get("status") == "success")
        expected = float(reference_probability[target].mean(dtype=np.float64))
        if abs(result["saved_target_mean"] - expected) > 1e-8:
            raise ValueError("Saved baseline target differs from original probabilities.")
        if result.get("status") not in ("success", "running"):
            raise ValueError("Unsupported occlusion journal state.")
        if result["status"] == "success":
            return result
    else:
        controls = []
        diagnostics = journal.with_name(journal.stem + "-controls.json")
        first = None
        for number in range(2):
            print(f"Unchanged-input control {number + 1}/2", flush=True)
            baseline = np.asarray(predict(data_kji.copy()))
            _probability(baseline, data_kji.shape)
            metrics = _comparison(baseline, reference_probability, target)
            controls.append(
                {"score": float(baseline[target].mean(dtype=np.float64)), "to_saved": metrics}
            )
            _save(
                diagnostics,
                {"status": "checking", "fingerprint": fingerprint, "controls": controls},
            )
            _check_metrics(metrics)
            if number == 0:
                first = baseline.copy()
        repeatability = _comparison(baseline, first, target)
        _save(
            diagnostics,
            {
                "status": "checking",
                "fingerprint": fingerprint,
                "controls": controls,
                "repeatability": repeatability,
            },
        )
        _check_metrics(repeatability)
        saved_mean = float(reference_probability[target].mean(dtype=np.float64))
        baseline_score = sum(c["score"] for c in controls) / 2
        result = {
            "schema_version": 1,
            "status": "running",
            "fingerprint": fingerprint,
            "spec": spec,
            "baseline_score": baseline_score,
            "baseline_max_error": max(c["to_saved"]["max_abs"] for c in controls),
            "saved_target_mean": saved_mean,
            "controls": controls,
            "repeatability": repeatability,
            "control_floor": max(
                MIN_CONTROL_FLOOR,
                repeatability["target_mean_abs"],
                abs(baseline_score - saved_mean),
            ),
            "blocks": [],
        }
        validate_controls(result)
        _save(journal, result)
        _save(
            diagnostics,
            {
                "status": "accepted",
                "fingerprint": fingerprint,
                "controls": controls,
                "repeatability": repeatability,
            },
        )
        del baseline, first
    for bounds in blocks[len(result["blocks"]) :]:
        a, b = bounds
        changed = data_kji.copy()
        changed[a[2] : b[2], a[1] : b[1], a[0] : b[0]] = fill_value
        began = time.monotonic()
        values = np.asarray(predict(changed))
        _probability(values, data_kji.shape)
        score = float(values[target].mean(dtype=np.float64))
        result["blocks"].append(
            {
                "bounds_ijk": bounds,
                "occluded_score": score,
                "effect": result["baseline_score"] - score,
                "seconds": time.monotonic() - began,
            }
        )
        _save(journal, result)
        print(f"Occlusion blocks completed: {len(result['blocks'])}/8", flush=True)
        del changed, values
    result["status"] = "success"
    validate_effects(result, blocks, complete=True)
    _save(journal, result)
    return result
