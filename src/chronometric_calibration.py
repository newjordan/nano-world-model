"""Leakage-aware calibration heads for chronometric bridge manifests."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

from chronometric_bridge import DEFAULT_POTENTIAL_FAMILY_ORDER, read_jsonl


FEATURE_NAMES = (
    "t_norm",
    "action_value_norm",
    "has_action_data",
    "action_data_x_norm",
    "action_data_y_norm",
    "changed_cells_norm",
    "movement_dx_norm",
    "movement_dy_norm",
    "phase_sin",
    "phase_cos",
    "transition_changed_eta",
    "time_phase_eta",
    "stasis_no_change_eta",
    "loop_repeated_action_eta",
    "mirror_progress_path_eta",
    "mirror_progress_blocker_eta",
    "hazard_env_failure_eta",
    "same_action_streak_norm",
    "same_action_low_change_streak_norm",
)

LEAKAGE_EXCLUDED_FIELDS = (
    "signed_outcome_y",
    "progress_label",
    "control_label",
    "level_delta",
    "levels_completed",
    "next_levels_completed",
    "event_mu[2]",
    "branch_direction_n[2]",
    "action_context[5]",
    "action_context[6]",
    "action_context[7]",
    "goal_progress.level_delta",
)

NEGATIVE_CONTROL_LABELS = (
    "stasis_no_change",
    "dominant_group:stasis_loop",
)


@dataclass(frozen=True)
class CalibrationExample:
    record: dict[str, Any]
    features: list[float]
    signed_y: float
    progress: float
    family_vector: list[float]


@dataclass(frozen=True)
class CalibrationExampleSplit:
    train: list[CalibrationExample]
    heldout: list[CalibrationExample]
    key: str
    holdout_fraction: float
    seed: int
    train_groups: list[str]
    heldout_groups: list[str]


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return default


def _get_sequence_number(values: Any, index: int, default: float = 0.0) -> float:
    if not isinstance(values, list) or index >= len(values):
        return default
    return _number(values[index], default)


def _family_lookup(record: dict[str, Any]) -> dict[str, float]:
    names = record.get("potential_family_names")
    vector = record.get("potential_family_vector")
    if not isinstance(names, list) or not isinstance(vector, list):
        return {}
    return {str(name): _number(vector[index]) for index, name in enumerate(names) if index < len(vector)}


def calibration_features(record: dict[str, Any], *, max_steps: float = 100.0) -> list[float]:
    """Build a calibration input vector without direct outcome-label leakage."""
    action_context = record.get("action_context")
    movement = record.get("dominant_movement_vector")
    shape = record.get("observation_shape") if isinstance(record.get("observation_shape"), list) else [64, 64, 1]
    height = max(_get_sequence_number(shape, 0, 64.0), 1.0)
    width = max(_get_sequence_number(shape, 1, 64.0), 1.0)
    phase_theta = _number(record.get("phase_theta"), 0.0)
    family = _family_lookup(record)

    return [
        min(max(_number(record.get("t")) / max_steps, 0.0), 1.0),
        _get_sequence_number(action_context, 0),
        _get_sequence_number(action_context, 1),
        _get_sequence_number(action_context, 2),
        _get_sequence_number(action_context, 3),
        _get_sequence_number(action_context, 4),
        _get_sequence_number(movement, 0) / width,
        _get_sequence_number(movement, 1) / height,
        math.sin(phase_theta),
        math.cos(phase_theta),
        family.get("transition.changed_cells", 0.0),
        family.get("time_phase.repeated_effect_size", 0.0),
        family.get("stasis.no_change", 0.0),
        family.get("loop.repeated_action", 0.0),
        family.get("mirror.progress_path", 0.0),
        family.get("mirror.progress_blocker", 0.0),
        family.get("hazard.env_failure", 0.0),
        _number(record.get("same_action_streak_norm")),
        _number(record.get("same_action_low_change_streak_norm")),
    ]


def calibration_example(record: dict[str, Any]) -> CalibrationExample:
    family_vector = record.get("potential_family_vector")
    if not isinstance(family_vector, list):
        family_vector = [0.0 for _ in DEFAULT_POTENTIAL_FAMILY_ORDER]
    return CalibrationExample(
        record=record,
        features=calibration_features(record),
        signed_y=_number(record.get("signed_outcome_y")),
        progress=1.0 if record.get("progress_label") == "progress_level_delta_positive" else 0.0,
        family_vector=[_number(value) for value in family_vector],
    )


def load_calibration_examples(path: Path) -> list[CalibrationExample]:
    return [calibration_example(record) for record in records_with_temporal_context(read_jsonl(path))]


def records_with_temporal_context(
    records: list[dict[str, Any]],
    *,
    max_streak: float = 40.0,
    low_change_threshold: float = 0.001,
) -> list[dict[str, Any]]:
    """Add prior-only action streak features within each source branch.

    Streaks are limited to non-coordinate actions. Coordinate-bearing action
    rows can repeat the action id while still pointing at different cells, so
    treating them as a loop signal aliases unrelated targeted moves.
    """
    annotated = [dict(record) for record in records]
    groups: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(annotated):
        source = record.get("source_artifact_path")
        groups[str(source) if source else f"row:{index}"].append(index)

    for indices in groups.values():
        last_action: str | None = None
        action_streak = 0
        low_change_streak = 0
        for index in sorted(indices, key=lambda row_index: int(annotated[row_index].get("t", 0) or 0)):
            record = annotated[index]
            action = str(record.get("action_id", ""))
            has_action_data = _get_sequence_number(record.get("action_context"), 1) > 0.5
            changed_eta = _get_sequence_number(record.get("action_context"), 4)
            if not has_action_data and action and action == last_action:
                action_streak += 1
                if abs(changed_eta) <= low_change_threshold:
                    low_change_streak += 1
                else:
                    low_change_streak = 0
            else:
                action_streak = 0
                low_change_streak = 0
            record["same_action_streak_norm"] = min(action_streak / max_streak, 1.0)
            record["same_action_low_change_streak_norm"] = min(low_change_streak / max_streak, 1.0)
            last_action = None if has_action_data else action
    return annotated


def _stable_group_order(groups: list[str], *, seed: int) -> list[str]:
    return sorted(groups, key=lambda key: hashlib.sha256(f"{seed}:{key}".encode("utf-8")).hexdigest())


def _select_heldout_groups(groups: list[str], *, holdout_fraction: float, seed: int) -> list[str]:
    if len(groups) <= 1:
        return []
    count = max(1, round(len(groups) * holdout_fraction))
    count = min(count, len(groups) - 1)
    return _stable_group_order(groups, seed=seed)[:count]


def split_examples_by_group(
    examples: list[CalibrationExample],
    *,
    key: str = "source_artifact_path",
    holdout_fraction: float = 0.0,
    seed: int = 20260505,
    heldout_group_values: list[str] | None = None,
) -> CalibrationExampleSplit:
    """Deterministically split examples by group, preserving positive-bearing groups when possible."""
    if not examples:
        raise ValueError("calibration examples must not be empty")
    if holdout_fraction < 0.0 or holdout_fraction >= 1.0:
        raise ValueError("holdout_fraction must be in [0.0, 1.0)")
    groups: dict[str, list[CalibrationExample]] = {}
    example_groups: dict[int, str] = {}
    for index, example in enumerate(examples):
        group = example.record.get(key)
        if not isinstance(group, str) or not group:
            group = example.record.get("attempt_id")
        if not isinstance(group, str) or not group:
            group = f"row:{index}"
        example_groups[id(example)] = group
        groups.setdefault(group, []).append(example)

    explicit_heldout = set(heldout_group_values or [])
    missing_explicit = sorted(explicit_heldout - set(groups))
    if missing_explicit:
        raise ValueError(f"explicit heldout groups were not present for key {key!r}: {missing_explicit}")

    if explicit_heldout:
        train = [example for example in examples if example_groups[id(example)] not in explicit_heldout]
        heldout = [example for example in examples if example_groups[id(example)] in explicit_heldout]
        if not train or not heldout:
            raise ValueError("explicit group holdout produced an empty train or heldout split")
        return CalibrationExampleSplit(
            train=train,
            heldout=heldout,
            key=key,
            holdout_fraction=holdout_fraction,
            seed=seed,
            train_groups=sorted(set(groups) - explicit_heldout),
            heldout_groups=sorted(explicit_heldout),
        )

    if holdout_fraction <= 0.0:
        return CalibrationExampleSplit(
            train=list(examples),
            heldout=[],
            key=key,
            holdout_fraction=holdout_fraction,
            seed=seed,
            train_groups=sorted(groups),
            heldout_groups=[],
        )
    if len(groups) <= 1:
        raise ValueError("group holdout requires at least two groups")

    positive_groups = [group for group, rows in groups.items() if any(row.progress > 0.5 for row in rows)]
    nonpositive_groups = [group for group in groups if group not in positive_groups]
    heldout_groups = set(_select_heldout_groups(positive_groups, holdout_fraction=holdout_fraction, seed=seed))
    heldout_groups.update(
        _select_heldout_groups(nonpositive_groups, holdout_fraction=holdout_fraction, seed=seed + 1)
    )
    if not heldout_groups:
        heldout_groups.add(_stable_group_order(sorted(groups), seed=seed)[0])

    train = [example for example in examples if example_groups[id(example)] not in heldout_groups]
    heldout = [example for example in examples if example_groups[id(example)] in heldout_groups]
    if not train or not heldout:
        raise ValueError("group holdout produced an empty train or heldout split")
    return CalibrationExampleSplit(
        train=train,
        heldout=heldout,
        key=key,
        holdout_fraction=holdout_fraction,
        seed=seed,
        train_groups=sorted(set(groups) - heldout_groups),
        heldout_groups=sorted(heldout_groups),
    )


def examples_to_tensors(
    examples: list[CalibrationExample],
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    if not examples:
        raise ValueError("calibration examples must not be empty")
    x = torch.tensor([example.features for example in examples], dtype=torch.float32, device=device)
    signed_y = torch.tensor([[example.signed_y] for example in examples], dtype=torch.float32, device=device)
    progress = torch.tensor([[example.progress] for example in examples], dtype=torch.float32, device=device)
    families = torch.tensor([example.family_vector for example in examples], dtype=torch.float32, device=device)
    return x, signed_y, progress, families


def examples_to_negative_control_mask(
    examples: list[CalibrationExample],
    *,
    device: torch.device,
) -> torch.Tensor:
    return torch.tensor(
        [[1.0 if is_negative_control_record(example.record) else 0.0] for example in examples],
        dtype=torch.float32,
        device=device,
    )


def is_negative_control_record(record: dict[str, Any]) -> bool:
    return str(record.get("control_label", "")) in NEGATIVE_CONTROL_LABELS


class ChronometricCalibrationMLP(nn.Module):
    """Small supervised calibration head over bridge-manifest features."""

    def __init__(self, input_dim: int, family_dim: int, hidden_size: int = 64, *, bounded_outputs: bool = True):
        super().__init__()
        self.bounded_outputs = bounded_outputs
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_size),
            nn.SiLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.SiLU(),
        )
        self.signed_y_head = nn.Linear(hidden_size, 1)
        self.progress_head = nn.Linear(hidden_size, 1)
        self.family_head = nn.Linear(hidden_size, family_dim)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        hidden = self.net(x)
        signed_y = self.signed_y_head(hidden)
        family_vector = self.family_head(hidden)
        if self.bounded_outputs:
            signed_y = torch.tanh(signed_y)
            family_vector = torch.tanh(family_vector)
        return {
            "signed_y": signed_y,
            "progress_logit": self.progress_head(hidden),
            "family_vector": family_vector,
        }
