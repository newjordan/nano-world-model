"""Feature-coverage diagnostics for chronometric calibration runs."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable

from chronometric_calibration import FEATURE_NAMES, calibration_features


DEFAULT_GROUP_TYPES = ("action", "control_label", "action_control")


def summarize_feature_groups(
    rows: Iterable[dict[str, Any]],
    *,
    group_types: Iterable[str] = DEFAULT_GROUP_TYPES,
) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    grouped: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        split = str(row.get("split", "unknown"))
        for group_type in group_types:
            grouped[group_type][split][_group_label(row, group_type)].append(row)
    return {
        group_type: {
            split: {
                label: summarize_feature_rows(group_rows)
                for label, group_rows in sorted(labels.items(), key=lambda item: item[0])
            }
            for split, labels in sorted(splits.items(), key=lambda item: item[0])
        }
        for group_type, splits in sorted(grouped.items(), key=lambda item: item[0])
    }


def summarize_feature_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("feature rows must not be empty")
    vectors = [calibration_features(row) for row in rows]
    feature_mean = [_mean(column) for column in zip(*vectors, strict=True)]
    signed_targets = [_number(row.get("target_signed_y", row.get("signed_outcome_y"))) for row in rows]
    signed_preds = [_number(row.get("pred_signed_y")) for row in rows if _has_number(row.get("pred_signed_y"))]
    progress_targets = [_number(row.get("target_progress")) for row in rows]
    progress_probs = [_number(row.get("pred_progress_prob")) for row in rows if _has_number(row.get("pred_progress_prob"))]
    signed_mae = None
    signed_bias = None
    if signed_preds and len(signed_preds) == len(signed_targets):
        errors = [pred - target for pred, target in zip(signed_preds, signed_targets, strict=True)]
        signed_mae = sum(abs(error) for error in errors) / len(errors)
        signed_bias = sum(errors) / len(errors)
    return {
        "records": len(rows),
        "positive_records": int(sum(target >= 0.5 for target in progress_targets)),
        "target_signed_mean": sum(signed_targets) / len(signed_targets),
        "pred_signed_mean": (sum(signed_preds) / len(signed_preds)) if signed_preds else None,
        "signed_mae": signed_mae,
        "signed_bias": signed_bias,
        "mean_progress_prob": (sum(progress_probs) / len(progress_probs)) if progress_probs else None,
        "feature_mean": dict(zip(FEATURE_NAMES, feature_mean, strict=True)),
    }


def nearest_train_groups(
    summary: dict[str, dict[str, dict[str, dict[str, Any]]]],
    *,
    group_type: str = "action_control",
) -> dict[str, dict[str, Any]]:
    train = summary.get(group_type, {}).get("train", {})
    heldout = summary.get(group_type, {}).get("heldout", {})
    if not train or not heldout:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for heldout_label, heldout_stats in heldout.items():
        distances = [
            (_feature_distance(heldout_stats, train_label, train_stats), train_label, train_stats)
            for train_label, train_stats in train.items()
        ]
        distance, train_label, train_stats = min(distances, key=lambda item: (item[0], item[1]))
        same_label_distance = None
        if heldout_label in train:
            same_label_distance = _feature_distance(heldout_stats, heldout_label, train[heldout_label])
        result[heldout_label] = {
            "nearest_train_label": train_label,
            "nearest_distance": distance,
            "nearest_train_records": train_stats["records"],
            "same_label_distance": same_label_distance,
            "same_label_train_records": train.get(heldout_label, {}).get("records"),
        }
    return result


def top_heldout_error_groups(
    summary: dict[str, dict[str, dict[str, dict[str, Any]]]],
    *,
    group_type: str = "action_control",
    limit: int = 8,
) -> list[tuple[str, dict[str, Any]]]:
    heldout = summary.get(group_type, {}).get("heldout", {})
    rows = [
        (label, stats)
        for label, stats in heldout.items()
        if isinstance(stats.get("signed_mae"), (int, float))
    ]
    rows.sort(key=lambda item: (-float(item[1]["signed_mae"]), item[0]))
    return rows[:limit]


def _group_label(row: dict[str, Any], group_type: str) -> str:
    action = str(row.get("action_id", "unknown"))
    control = str(row.get("control_label", "unknown"))
    if group_type == "action":
        return f"action:{action}"
    if group_type == "control_label":
        return f"control_label:{control}"
    if group_type == "action_control":
        return f"action:{action}|control_label:{control}"
    raise ValueError(f"unsupported group type: {group_type}")


def _feature_distance(
    heldout_stats: dict[str, Any],
    _train_label: str,
    train_stats: dict[str, Any],
) -> float:
    heldout_features = heldout_stats["feature_mean"]
    train_features = train_stats["feature_mean"]
    squared = [
        (_number(heldout_features[name]) - _number(train_features[name])) ** 2
        for name in FEATURE_NAMES
    ]
    return math.sqrt(sum(squared) / len(squared))


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)


def _has_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _number(value: Any) -> float:
    if _has_number(value):
        return float(value)
    return 0.0
