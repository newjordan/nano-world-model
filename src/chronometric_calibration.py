"""Leakage-aware calibration heads for chronometric bridge manifests."""

from __future__ import annotations

import math
from dataclasses import dataclass
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


@dataclass(frozen=True)
class CalibrationExample:
    record: dict[str, Any]
    features: list[float]
    signed_y: float
    progress: float
    family_vector: list[float]


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
    return [calibration_example(record) for record in read_jsonl(path)]


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


class ChronometricCalibrationMLP(nn.Module):
    """Small supervised calibration head over bridge-manifest features."""

    def __init__(self, input_dim: int, family_dim: int, hidden_size: int = 64):
        super().__init__()
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
        return {
            "signed_y": self.signed_y_head(hidden),
            "progress_logit": self.progress_head(hidden),
            "family_vector": self.family_head(hidden),
        }
