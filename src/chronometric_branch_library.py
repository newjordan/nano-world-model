"""Train-built branch library helpers for chronometric calibration outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from chronometric_calibration import action6_time_phase_geometry_key


BRANCH_LIBRARY_SCOPES = (
    "action6_time_phase",
    "dominant_time_phase",
    "dominant_translation",
    "time_phase_translation",
)
GRID_CELL_COUNT = 4096


@dataclass(frozen=True)
class BranchLibraryEntry:
    key: str
    records: int
    signed_y_mean: float


def build_chronometric_branch_library(
    rows: Iterable[dict[str, Any]],
    *,
    split: str = "train",
    min_records: int = 1,
    scope: str = "action6_time_phase",
) -> dict[str, BranchLibraryEntry]:
    if scope not in BRANCH_LIBRARY_SCOPES:
        raise ValueError(f"unknown branch library scope: {scope}")
    values: dict[str, list[float]] = {}
    for row in rows:
        if str(row.get("split", "")) != split:
            continue
        key = branch_library_key(row, scope=scope)
        if key is None:
            continue
        values.setdefault(key, []).append(_number(row.get("target_signed_y", row.get("signed_outcome_y"))))
    return {
        key: BranchLibraryEntry(key=key, records=len(signed_values), signed_y_mean=sum(signed_values) / len(signed_values))
        for key, signed_values in sorted(values.items())
        if len(signed_values) >= min_records
    }


def build_action6_time_phase_branch_library(
    rows: Iterable[dict[str, Any]],
    *,
    split: str = "train",
    min_records: int = 1,
) -> dict[str, BranchLibraryEntry]:
    return build_chronometric_branch_library(
        rows,
        split=split,
        min_records=min_records,
        scope="action6_time_phase",
    )


def branch_library_key(row: dict[str, Any], *, scope: str) -> str | None:
    if scope == "action6_time_phase":
        return action6_time_phase_geometry_key(row)
    if scope == "dominant_time_phase":
        return dominant_time_phase_grid_key(row)
    if scope == "dominant_translation":
        return dominant_translation_grid_key(row)
    if scope == "time_phase_translation":
        return dominant_time_phase_grid_key(row) or dominant_translation_grid_key(row)
    raise ValueError(f"unknown branch library scope: {scope}")


def branch_library_candidate_keys(row: dict[str, Any]) -> list[str]:
    keys = [
        action6_time_phase_geometry_key(row),
        dominant_time_phase_grid_key(row),
        dominant_translation_grid_key(row),
    ]
    unique: list[str] = []
    for key in keys:
        if key is not None and key not in unique:
            unique.append(key)
    return unique


def dominant_time_phase_grid_key(row: dict[str, Any], *, grid_scale: int = 64) -> str | None:
    if str(row.get("control_label", "")) != "dominant_group:time_phase":
        return None
    if _family_lookup(row).get("time_phase.repeated_effect_size", 0.0) <= 0.0:
        return None
    return _action_control_grid_key(row, "dominant_group:time_phase", grid_scale=grid_scale)


def dominant_translation_grid_key(row: dict[str, Any], *, grid_scale: int = 64) -> str | None:
    if str(row.get("control_label", "")) != "dominant_group:translation":
        return None
    if _family_lookup(row).get("transition.changed_cells", 0.0) <= 0.0:
        return None
    return _action_control_grid_key(row, "dominant_group:translation", grid_scale=grid_scale)


def blend_branch_library_signed_y(
    row: dict[str, Any],
    library: dict[str, BranchLibraryEntry],
    *,
    blend: float,
) -> tuple[float, BranchLibraryEntry | None]:
    raw_prediction = _number(row.get("pred_signed_y"))
    entry = None
    for key in branch_library_candidate_keys(row):
        entry = library.get(key)
        if entry is not None:
            break
    if entry is None:
        return raw_prediction, None
    clamped_blend = min(max(float(blend), 0.0), 1.0)
    return (1.0 - clamped_blend) * raw_prediction + clamped_blend * entry.signed_y_mean, entry


def _action_control_grid_key(row: dict[str, Any], control_label: str, *, grid_scale: int) -> str:
    action_id = str(row.get("action_id", "")).upper()
    action_context = row.get("action_context")
    changed_cells = _changed_cells(row)
    if _sequence_number(action_context, 1) > 0.5:
        x_index = round(_sequence_number(action_context, 2) * grid_scale)
        y_index = round(_sequence_number(action_context, 3) * grid_scale)
        return f"{action_id}|{control_label}|coord:x:{x_index}|y:{y_index}|changed:{changed_cells}"
    return f"{action_id}|{control_label}|no_coord|changed:{changed_cells}"


def _changed_cells(row: dict[str, Any]) -> int:
    changed = row.get("changed_cells")
    if isinstance(changed, (int, float)) and not isinstance(changed, bool):
        return int(round(float(changed)))
    action_context = row.get("action_context")
    return int(round(_sequence_number(action_context, 4) * GRID_CELL_COUNT))


def _family_lookup(row: dict[str, Any]) -> dict[str, float]:
    names = row.get("potential_family_names")
    values = row.get("potential_family_vector")
    if not isinstance(names, list) or not isinstance(values, list):
        return {}
    return {str(name): _number(values[index]) for index, name in enumerate(names) if index < len(values)}


def _sequence_number(values: Any, index: int) -> float:
    if isinstance(values, (list, tuple)) and len(values) > index:
        return _number(values[index])
    return 0.0


def _number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0
