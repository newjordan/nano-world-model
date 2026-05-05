"""Bucketed diagnostics for chronometric calibration predictions."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable


EPS = 1e-8


def prediction_join_key(record: dict[str, Any]) -> tuple[str, int, str]:
    return (
        str(record.get("source_artifact_path", "")),
        int(record.get("t", 0) or 0),
        str(record.get("action_id", "")),
    )


def join_predictions_to_manifest(
    manifest_records: Iterable[dict[str, Any]],
    prediction_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Join predictions back to bridge rows by source file, step, and action."""
    manifest_by_key: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for record in manifest_records:
        manifest_by_key[prediction_join_key(record)].append(record)

    joined: list[dict[str, Any]] = []
    missing: list[tuple[str, int, str]] = []
    for prediction in prediction_records:
        key = prediction_join_key(prediction)
        matches = manifest_by_key.get(key)
        if not matches:
            missing.append(key)
            continue
        manifest = matches[0]
        joined.append({**manifest, **prediction})
    if missing:
        sample = ", ".join(str(key) for key in missing[:3])
        raise ValueError(f"{len(missing)} prediction rows did not match manifest rows: {sample}")
    return joined


def signed_outcome_bucket(value: float) -> str:
    if value >= 0.95:
        return "signed:progress_positive_y"
    if value > 0.05:
        return "signed:minor_positive_y"
    if value >= 0.0:
        return "signed:near_zero_y"
    return "signed:negative_y"


def movement_axis_bucket(record: dict[str, Any]) -> str:
    vector = record.get("dominant_movement_vector")
    if not isinstance(vector, list) or len(vector) < 2:
        return "movement:unknown"
    dx = _number(vector[0])
    dy = _number(vector[1])
    if abs(dx) < 1e-8 and abs(dy) < 1e-8:
        return "movement:none"
    if abs(dx) >= abs(dy):
        return "movement:x_positive" if dx >= 0 else "movement:x_negative"
    return "movement:y_positive" if dy >= 0 else "movement:y_negative"


def time_window_bucket(record: dict[str, Any], *, progress_step: int = 26) -> str:
    t = int(record.get("t", 0) or 0)
    if t < progress_step:
        return "time:pre_progress_step"
    if t == progress_step:
        return "time:progress_step"
    return "time:post_progress_step"


def change_bucket(record: dict[str, Any]) -> str:
    changed = _number(record.get("changed_cells"))
    if changed <= 0:
        return "change:stasis"
    if changed <= 4:
        return "change:tiny"
    if changed <= 32:
        return "change:small"
    if changed <= 128:
        return "change:medium"
    return "change:large"


def bucket_labels(record: dict[str, Any]) -> dict[str, str]:
    control_label = str(record.get("control_label", "unknown"))
    progress_label = str(record.get("progress_label", "unknown"))
    action_id = str(record.get("action_id", "unknown"))
    dominant_group = str(record.get("dominant_group", "unknown"))
    return {
        "split": f"split:{record.get('split', 'unknown')}",
        "progress_label": f"progress_label:{progress_label}",
        "control_label": f"control_label:{control_label}",
        "action": f"action:{action_id}",
        "dominant_group": f"dominant_group:{dominant_group}",
        "signed_outcome": signed_outcome_bucket(_number(record.get("target_signed_y", record.get("signed_outcome_y")))),
        "movement_axis": movement_axis_bucket(record),
        "time_window": time_window_bucket(record),
        "change": change_bucket(record),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "records": 0,
            "positive_records": 0,
            "progress_accuracy": None,
            "progress_bce": None,
            "signed_mae": None,
        }

    progress_targets = [_number(row.get("target_progress")) for row in rows]
    progress_probs = [_number(row.get("pred_progress_prob")) for row in rows]
    signed_targets = [_number(row.get("target_signed_y")) for row in rows]
    signed_preds = [_number(row.get("pred_signed_y")) for row in rows]
    positive_ranks = [
        int(row.get("pred_progress_rank"))
        for row in rows
        if _number(row.get("target_progress")) >= 0.5 and isinstance(row.get("pred_progress_rank"), int)
    ]
    progress_accuracy = sum(
        int((prob >= 0.5) == (target >= 0.5)) for prob, target in zip(progress_probs, progress_targets)
    ) / len(rows)
    progress_bce = sum(_bce(target, prob) for target, prob in zip(progress_targets, progress_probs)) / len(rows)
    signed_errors = [abs(pred - target) for pred, target in zip(signed_preds, signed_targets)]
    false_positive_rows = [row for row in rows if _number(row.get("target_progress")) < 0.5]
    top_false_positive = max(false_positive_rows, key=lambda row: _number(row.get("pred_progress_prob")), default=None)
    worst_signed = max(rows, key=lambda row: abs(_number(row.get("pred_signed_y")) - _number(row.get("target_signed_y"))))
    return {
        "records": len(rows),
        "positive_records": int(sum(target >= 0.5 for target in progress_targets)),
        "progress_accuracy": progress_accuracy,
        "progress_bce": progress_bce,
        "signed_mae": sum(signed_errors) / len(rows),
        "signed_bias": sum(pred - target for pred, target in zip(signed_preds, signed_targets)) / len(rows),
        "mean_progress_prob": sum(progress_probs) / len(rows),
        "max_progress_prob": max(progress_probs),
        "positive_best_rank": min(positive_ranks) if positive_ranks else None,
        "positive_mean_rank": (sum(positive_ranks) / len(positive_ranks)) if positive_ranks else None,
        "top_false_positive": _compact_row(top_false_positive) if top_false_positive else None,
        "worst_signed_error": _compact_row(worst_signed),
    }


def summarize_buckets(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for bucket_type, label in bucket_labels(row).items():
            grouped[bucket_type][label].append(row)
    return {
        bucket_type: {
            label: summarize_rows(bucket_rows)
            for label, bucket_rows in sorted(labels.items(), key=lambda item: item[0])
        }
        for bucket_type, labels in sorted(grouped.items(), key=lambda item: item[0])
    }


def _bce(target: float, prob: float) -> float:
    prob = min(1.0 - EPS, max(EPS, prob))
    return -(target * math.log(prob) + (1.0 - target) * math.log(1.0 - prob))


def _number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _compact_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "split": row.get("split"),
        "source_artifact_path": row.get("source_artifact_path"),
        "t": row.get("t"),
        "action_id": row.get("action_id"),
        "control_label": row.get("control_label"),
        "progress_label": row.get("progress_label"),
        "target_progress": row.get("target_progress"),
        "pred_progress_prob": row.get("pred_progress_prob"),
        "target_signed_y": row.get("target_signed_y"),
        "pred_signed_y": row.get("pred_signed_y"),
        "pred_progress_rank": row.get("pred_progress_rank"),
    }
