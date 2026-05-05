"""Bridge manifest validation for quarantined ARC-to-NanoWM data.

The bridge manifest is the gate between external control evidence and
chronometric model data. It keeps provenance and event-space interpretation in
the record instead of letting old harness rows silently become training samples.
"""

from __future__ import annotations

import json
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
