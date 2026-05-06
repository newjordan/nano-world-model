"""Bridge manifest validation for quarantined ARC-to-NanoWM data.

The bridge manifest is the gate between external control evidence and
chronometric model data. It keeps provenance and event-space interpretation in
the record instead of letting old harness rows silently become training samples.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable


REQUIRED_BRIDGE_FIELDS = (
    "source_repo",
    "source_commit",
    "source_artifact_path",
    "source_condition_artifact",
    "quarantine_status",
    "split",
    "task_id",
    "attempt_id",
    "t",
    "observation_shape",
    "action_id",
    "action_context",
    "event_mu",
    "branch_direction_n",
    "potential_family_vector",
    "signed_outcome_y",
    "progress_label",
    "control_label",
    "chronometric_transform_version",
)


VECTOR4_FIELDS = ("event_mu", "branch_direction_n")
SEQUENCE_FIELDS = ("observation_shape", "action_context", "potential_family_vector")
DEFAULT_POTENTIAL_FAMILY_ORDER = (
    "transition.changed_cells",
    "time_phase.repeated_effect_size",
    "goal_progress.level_delta",
    "stasis.no_change",
    "loop.repeated_action",
    "mirror.progress_path",
    "mirror.progress_blocker",
    "hazard.env_failure",
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_bridge_record(record: dict[str, Any], *, row_index: int | None = None) -> list[str]:
    """Return validation errors for one manifest record."""
    prefix = f"row {row_index}: " if row_index is not None else ""
    errors: list[str] = []

    missing = [field for field in REQUIRED_BRIDGE_FIELDS if field not in record]
    for field in missing:
        errors.append(f"{prefix}missing required field {field!r}")
    if missing:
        return errors

    for field in (
        "source_repo",
        "source_commit",
        "source_artifact_path",
        "source_condition_artifact",
        "quarantine_status",
        "split",
        "task_id",
        "attempt_id",
        "action_id",
        "progress_label",
        "control_label",
        "chronometric_transform_version",
    ):
        if not isinstance(record[field], str) or len(record[field]) == 0:
            errors.append(f"{prefix}{field!r} must be a non-empty string")

    if not isinstance(record["t"], int) or record["t"] < 0:
        errors.append(f"{prefix}'t' must be a non-negative integer")

    if not _is_number(record["signed_outcome_y"]):
        errors.append(f"{prefix}'signed_outcome_y' must be numeric")

    for field in VECTOR4_FIELDS:
        value = record[field]
        if not isinstance(value, list) or len(value) != 4 or not all(_is_number(v) for v in value):
            errors.append(f"{prefix}{field!r} must be a numeric length-4 list")

    for field in SEQUENCE_FIELDS:
        value = record[field]
        if not isinstance(value, list) or len(value) == 0:
            errors.append(f"{prefix}{field!r} must be a non-empty list")
        elif field != "observation_shape" and not all(_is_number(v) for v in value):
            errors.append(f"{prefix}{field!r} must contain only numeric values")

    if "quarantine" not in record["quarantine_status"] and "control_source" not in record["quarantine_status"]:
        errors.append(f"{prefix}'quarantine_status' must explicitly preserve quarantine/control status")

    return errors


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            records.append(value)
    return records


def validate_bridge_manifest(path: Path) -> dict[str, Any]:
    records = read_jsonl(path)
    errors: list[str] = []
    for index, record in enumerate(records):
        errors.extend(validate_bridge_record(record, row_index=index))
    return {
        "path": str(path),
        "records": len(records),
        "valid": len(errors) == 0 and len(records) > 0,
        "errors": errors,
    }


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def normalized_grid_delta(value: Any, span: int | float | None) -> float:
    if not _is_number(value):
        return 0.0
    denominator = float(span or 64)
    if denominator <= 0:
        denominator = 64.0
    return clamp(float(value) / denominator)


def signed_outcome_from_arc_transition(row: dict[str, Any]) -> float:
    level_delta = row.get("level_delta", 0) or 0
    if level_delta > 0:
        return 1.0
    if level_delta < 0:
        return -1.0
    next_state = str(row.get("next_state", "")).upper()
    if next_state in {"GAME_OVER", "FAILED", "LOST"}:
        return -1.0
    eta_total = row.get("eta_total", 0.0) or 0.0
    if _is_number(eta_total) and abs(float(eta_total)) > 0:
        return clamp(float(eta_total))
    changed_cells = row.get("changed_cells", 0) or 0
    if changed_cells == 0:
        return -0.25
    return 0.0


def dominant_movement_vector(row: dict[str, Any]) -> tuple[float, float]:
    movement = row.get("movement") or {}
    vector = movement.get("dominant_vector") or {}
    dx = vector.get("dx", 0.0)
    dy = vector.get("dy", 0.0)
    return (float(dx) if _is_number(dx) else 0.0, float(dy) if _is_number(dy) else 0.0)


def branch_direction_from_arc_transition(row: dict[str, Any], signed_outcome_y: float) -> list[float]:
    width = row.get("width", 64)
    height = row.get("height", 64)
    dx, dy = dominant_movement_vector(row)
    x = normalized_grid_delta(dx, width)
    z = normalized_grid_delta(dy, height)
    spatial_norm = math.sqrt(x * x + signed_outcome_y * signed_outcome_y + z * z)
    if spatial_norm <= 1e-8:
        return [0.0, 0.0, 1.0, 0.0]
    return [0.0, x / spatial_norm, signed_outcome_y / spatial_norm, z / spatial_norm]


def event_mu_from_arc_transition(row: dict[str, Any], signed_outcome_y: float) -> list[float]:
    width = row.get("width", 64)
    height = row.get("height", 64)
    dx, dy = dominant_movement_vector(row)
    return [
        float(row.get("step_idx", 0) or 0),
        normalized_grid_delta(dx, width),
        signed_outcome_y,
        normalized_grid_delta(dy, height),
    ]


def action_context_from_arc_transition(row: dict[str, Any]) -> list[float]:
    width = row.get("width", 64)
    height = row.get("height", 64)
    action_data = row.get("action_data") if isinstance(row.get("action_data"), dict) else {}
    changed_cells = row.get("changed_cells", 0) or 0
    cell_events = row.get("cell_events", (width or 64) * (height or 64)) or 4096
    action_value = row.get("action_value", 0) or 0
    level_delta = row.get("level_delta", 0) or 0
    eta_total = row.get("eta_total", 0.0) or 0.0
    outcome_sign = row.get("outcome_sign", 0) or 0
    return [
        clamp(float(action_value) / 10.0) if _is_number(action_value) else 0.0,
        1.0 if action_data else 0.0,
        normalized_grid_delta(action_data.get("x"), width),
        normalized_grid_delta(action_data.get("y"), height),
        clamp(float(changed_cells) / float(cell_events)) if _is_number(changed_cells) else 0.0,
        clamp(float(level_delta)) if _is_number(level_delta) else 0.0,
        clamp(float(eta_total)) if _is_number(eta_total) else 0.0,
        clamp(float(outcome_sign)) if _is_number(outcome_sign) else 0.0,
    ]


def potential_family_vector_from_arc_transition(
    row: dict[str, Any],
    family_order: Iterable[str] = DEFAULT_POTENTIAL_FAMILY_ORDER,
) -> list[float]:
    family_eta = row.get("family_eta") if isinstance(row.get("family_eta"), dict) else {}
    return [float(family_eta.get(name, 0.0) or 0.0) for name in family_order]


def progress_label_from_arc_transition(row: dict[str, Any]) -> str:
    level_delta = row.get("level_delta", 0) or 0
    if level_delta > 0:
        return "progress_level_delta_positive"
    if level_delta < 0:
        return "progress_level_delta_negative"
    return "no_level_progress"


def control_label_from_arc_transition(row: dict[str, Any]) -> str:
    next_state = str(row.get("next_state", "")).upper()
    if next_state in {"GAME_OVER", "FAILED", "LOST"}:
        return "terminal_or_failure"
    if (row.get("changed_cells", 0) or 0) == 0:
        return "stasis_no_change"
    dominant_group = row.get("dominant_group")
    if isinstance(dominant_group, str) and dominant_group:
        return f"dominant_group:{dominant_group}"
    return "arc_transition_control"


def bridge_record_from_arc_transition(
    row: dict[str, Any],
    *,
    source_repo: str,
    source_commit: str,
    source_artifact_path: str,
    source_condition_artifact: str,
    quarantine_status: str = "control_source: arc_scaffold_non_chronometric",
    split: str = "arc_sprint0_bridge_v001",
    family_order: Iterable[str] = DEFAULT_POTENTIAL_FAMILY_ORDER,
    transform_version: str = "arc_grid_transition_to_chronometric_bridge_v001",
) -> dict[str, Any]:
    signed_outcome_y = signed_outcome_from_arc_transition(row)
    family_names = list(family_order)
    record = {
        "source_repo": source_repo,
        "source_commit": source_commit,
        "source_artifact_path": source_artifact_path,
        "source_condition_artifact": source_condition_artifact,
        "quarantine_status": quarantine_status,
        "split": split,
        "task_id": str(row.get("task_id", "")),
        "attempt_id": str(row.get("attempt_id", "")),
        "t": int(row.get("step_idx", 0) or 0),
        "observation_shape": [int(row.get("height", 0) or 0), int(row.get("width", 0) or 0), 1],
        "action_id": str(row.get("action", "")),
        "action_context": action_context_from_arc_transition(row),
        "event_mu": event_mu_from_arc_transition(row, signed_outcome_y),
        "branch_direction_n": branch_direction_from_arc_transition(row, signed_outcome_y),
        "potential_family_vector": potential_family_vector_from_arc_transition(row, family_names),
        "signed_outcome_y": signed_outcome_y,
        "progress_label": progress_label_from_arc_transition(row),
        "control_label": control_label_from_arc_transition(row),
        "chronometric_transform_version": transform_version,
        "source_schema": row.get("schema"),
        "transition_id": row.get("transition_id"),
        "frame_hash": row.get("frame_hash"),
        "next_frame_hash": row.get("next_frame_hash"),
        "phase_theta": row.get("phase_theta"),
        "changed_cells": row.get("changed_cells"),
        "level_delta": row.get("level_delta"),
        "levels_completed": row.get("levels_completed"),
        "next_levels_completed": row.get("next_levels_completed"),
        "dominant_family": row.get("dominant_family"),
        "dominant_group": row.get("dominant_group"),
        "dominant_movement_vector": list(dominant_movement_vector(row)),
        "potential_family_names": family_names,
        "raw_scores": row.get("scores", []),
    }
    return record


def bridge_records_from_dream_sequence(
    sequence: dict[str, Any],
    *,
    source_repo: str,
    source_commit: str,
    source_artifact_path: str,
    source_condition_artifact: str,
    quarantine_status: str = "quarantine: dream_kernel_deterministic_no_training",
    split: str = "dream_kernel_sequence_v003",
    transform_version: str = "dream_kernel_sequence_to_chronometric_bridge_v001",
) -> list[dict[str, Any]]:
    """Convert Dream Kernel branch rows into chronometric bridge records.

    The output is a deterministic bridge diagnostic, not ARC solve evidence and
    not training data promotion. Branch IDs and Dream Kernel source hashes are
    preserved so downstream consumers can keep this split separate.
    """
    frames = {
        int(frame.get("tick")): frame
        for frame in sequence.get("frames") or []
        if isinstance(frame, dict) and isinstance(frame.get("tick"), int)
    }
    first_render = next(
        (frame.get("render_top_down") for frame in sequence.get("frames") or [] if isinstance(frame, dict)),
        [],
    )
    height = len(first_render) if isinstance(first_render, list) else 0
    width = max((len(str(row)) for row in first_render), default=0) if isinstance(first_render, list) else 0
    sequence_hash = (sequence.get("integrity") or {}).get("sequence_hash")
    records: list[dict[str, Any]] = []
    for branch in sequence.get("branch_matrix") or []:
        if not isinstance(branch, dict):
            continue
        end_tick = int(branch.get("end_tick") or 0)
        frame = frames.get(end_tick, {})
        chronometric = frame.get("chronometric") if isinstance(frame, dict) else {}
        if not isinstance(chronometric, dict):
            chronometric = {}
        outcome = frame.get("outcome") if isinstance(frame, dict) else {}
        if not isinstance(outcome, dict):
            outcome = {}
        branch_id = str(branch.get("branch_id") or f"dream_branch_{len(records)}")
        signed_outcome_y = _number_or_default(chronometric.get("signed_outcome_y"), branch.get("chrono_y_net", 0.0))
        support_count = len(branch.get("supporting_objects") or [])
        risk_count = len(branch.get("risk_objects") or [])
        record = {
            "source_repo": source_repo,
            "source_commit": source_commit,
            "source_artifact_path": source_artifact_path,
            "source_condition_artifact": source_condition_artifact,
            "quarantine_status": quarantine_status,
            "split": split,
            "task_id": f"dream_kernel:{sequence_hash or 'unknown_sequence'}",
            "attempt_id": branch_id,
            "branch_id": branch_id,
            "t": end_tick,
            "observation_shape": [height, width, 1],
            "action_id": str(branch.get("action_id") or ""),
            "action_context": [
                clamp(float(branch.get("chrono_y_net") or 0.0)),
                clamp(float(branch.get("chrono_y_min") or 0.0)),
                clamp(float(branch.get("positive_mass") or 0.0)),
                clamp(float(branch.get("negative_exposure") or 0.0)),
                clamp(support_count / 16.0, 0.0, 1.0),
                clamp(risk_count / 16.0, 0.0, 1.0),
                1.0 if outcome.get("terminal") else 0.0,
                clamp(float(outcome.get("reward") or 0.0)),
            ],
            "event_mu": _numeric_sequence(chronometric.get("event_mu"), 4),
            "branch_direction_n": _numeric_sequence(chronometric.get("branch_direction_n"), 4),
            "potential_family_vector": _numeric_sequence(
                chronometric.get("potential_family_vector"),
                len(chronometric.get("potential_family_names") or DEFAULT_POTENTIAL_FAMILY_ORDER),
            ),
            "signed_outcome_y": signed_outcome_y,
            "progress_label": _dream_progress_label(branch, outcome),
            "control_label": "dream_kernel_deterministic_branch",
            "chronometric_transform_version": transform_version,
            "source_schema": sequence.get("schema"),
            "sequence_hash": sequence_hash,
            "frame_hash": branch.get("frame_hash"),
            "potential_family_names": chronometric.get("potential_family_names") or list(DEFAULT_POTENTIAL_FAMILY_ORDER),
            "target_signed_y": signed_outcome_y,
            "terminal": bool(outcome.get("terminal")),
            "reward": outcome.get("reward"),
            "supporting_objects": branch.get("supporting_objects") or [],
            "risk_objects": branch.get("risk_objects") or [],
        }
        records.append(record)
    return records


def _dream_progress_label(branch: dict[str, Any], outcome: dict[str, Any]) -> str:
    reward = _number_or_default(outcome.get("reward"), 0.0)
    if reward > 0:
        return "dream_kernel_goal_terminal_positive"
    if reward < 0:
        return "dream_kernel_hazard_terminal_negative"
    if _number_or_default(branch.get("positive_mass"), 0.0) > 0:
        return "dream_kernel_positive_potential"
    return "dream_kernel_no_terminal_progress"


def _number_or_default(value: Any, default: Any) -> float:
    return float(value) if _is_number(value) else float(default or 0.0)


def _numeric_sequence(value: Any, length: int) -> list[float]:
    if not isinstance(value, list):
        return [0.0] * max(1, length)
    out = [float(item) if _is_number(item) else 0.0 for item in value[:length]]
    return out + [0.0] * max(0, length - len(out))


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def synthetic_bridge_records() -> list[dict[str, Any]]:
    """Small non-ARC manifest used only to smoke-test the bridge schema."""
    base = {
        "source_repo": "synthetic://chronometric_mechanics_smoke",
        "source_commit": "synthetic",
        "source_artifact_path": "synthetic://chronometric/event_pair",
        "source_condition_artifact": "condition.json",
        "quarantine_status": "control_source: synthetic_chronometric_smoke",
        "split": "mechanics_smoke",
        "task_id": "synthetic_event_branch",
        "attempt_id": "synthetic_attempt_000",
        "observation_shape": [4, 4, 3],
        "action_context": [0.0, 1.0, 0.0, 0.0],
        "potential_family_vector": [1.0, 0.0, 0.0, 0.0],
        "progress_label": "synthetic",
        "control_label": "schema_only_no_arc_ingest",
        "chronometric_transform_version": "chronometric_bridge_v001",
    }
    return [
        {
            **base,
            "t": 0,
            "action_id": "MOVE_POSITIVE_Y",
            "event_mu": [0.0, 0.0, 0.0, 0.0],
            "branch_direction_n": [0.0, 0.0, 1.0, 0.0],
            "signed_outcome_y": 1.0,
        },
        {
            **base,
            "t": 1,
            "action_id": "MOVE_NEGATIVE_Y",
            "event_mu": [1.0, 0.0, 1.0, 0.0],
            "branch_direction_n": [0.0, 0.0, -1.0, 0.0],
            "signed_outcome_y": -1.0,
        },
    ]
