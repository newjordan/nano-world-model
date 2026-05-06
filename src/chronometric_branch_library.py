"""Train-built branch library helpers for chronometric calibration outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from chronometric_calibration import action6_time_phase_geometry_key


@dataclass(frozen=True)
class BranchLibraryEntry:
    key: str
    records: int
    signed_y_mean: float


def build_action6_time_phase_branch_library(
    rows: Iterable[dict[str, Any]],
    *,
    split: str = "train",
    min_records: int = 1,
) -> dict[str, BranchLibraryEntry]:
    values: dict[str, list[float]] = {}
    for row in rows:
        if str(row.get("split", "")) != split:
            continue
        key = action6_time_phase_geometry_key(row)
        if key is None:
            continue
        values.setdefault(key, []).append(_number(row.get("target_signed_y", row.get("signed_outcome_y"))))
    return {
        key: BranchLibraryEntry(key=key, records=len(signed_values), signed_y_mean=sum(signed_values) / len(signed_values))
        for key, signed_values in sorted(values.items())
        if len(signed_values) >= min_records
    }


def blend_branch_library_signed_y(
    row: dict[str, Any],
    library: dict[str, BranchLibraryEntry],
    *,
    blend: float,
) -> tuple[float, BranchLibraryEntry | None]:
    raw_prediction = _number(row.get("pred_signed_y"))
    key = action6_time_phase_geometry_key(row)
    if key is None or key not in library:
        return raw_prediction, None
    entry = library[key]
    clamped_blend = min(max(float(blend), 0.0), 1.0)
    return (1.0 - clamped_blend) * raw_prediction + clamped_blend * entry.signed_y_mean, entry


def _number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0
