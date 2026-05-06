#!/usr/bin/env python3
"""Fail-closed validation for Dream Kernel sequence.v003 consumer scripts."""

from __future__ import annotations

from typing import Any


SYNTHETIC_OBJECT_PREFIXES = ("bounds:", "max_range:")


def require_dream_sequence(payload: Any, *, source: str = "dream_sequence") -> None:
    errors = validate_dream_sequence(payload)
    if errors:
        detail = "; ".join(errors[:12])
        if len(errors) > 12:
            detail += f"; ... {len(errors) - 12} more"
        raise ValueError(f"{source} is not a valid dream_kernel.sequence.v003 payload: {detail}")


def validate_dream_sequence(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["sequence payload must be a JSON object"]

    errors: list[str] = []
    schema = payload.get("schema")
    if not isinstance(schema, str) or not schema.startswith("dream_kernel.sequence."):
        errors.append("schema must start with dream_kernel.sequence.")

    registry_rows = _required_list(payload, "object_registry", errors)
    frames = _required_list(payload, "frames", errors)
    branch_rows = _required_list(payload, "branch_matrix", errors)
    branch_potentials = _required_list(payload, "branch_potentials", errors)
    object_links = _required_list(payload, "object_link_hypotheses", errors)
    nemo_relay = payload.get("nemo_relay")
    if nemo_relay is not None and not isinstance(nemo_relay, dict):
        errors.append("nemo_relay must be an object when present")
        nemo_relay = {}

    object_ids = _indexed_ids(registry_rows, "object_id", "object_registry", errors)
    branch_ids = _indexed_ids(branch_rows, "branch_id", "branch_matrix", errors)
    potential_ids = _indexed_ids(branch_potentials, "potential_id", "branch_potentials", errors)
    link_ids = _indexed_ids(object_links, "link_id", "object_link_hypotheses", errors)

    _validate_sequence_integrity(payload.get("integrity"), len(frames), errors)
    _validate_registry_rows(registry_rows, errors)
    _validate_frame_chain(frames, errors)
    _validate_frames(frames, object_ids, branch_ids, errors)
    _validate_branch_rows(branch_rows, object_ids, errors)
    _validate_branch_potentials(branch_potentials, branch_ids, object_ids, errors)
    _validate_object_links(object_links, branch_ids, object_ids, potential_ids, errors)
    if isinstance(nemo_relay, dict):
        _validate_nemo_relay(nemo_relay, branch_ids, object_ids, potential_ids, link_ids, errors)

    return errors


def _required_list(payload: dict[str, Any], key: str, errors: list[str]) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        errors.append(f"missing or invalid {key} list")
        return []
    return value


def _indexed_ids(rows: list[Any], key: str, label: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        value = row.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{label}[{index}] missing {key}")
            continue
        if value in ids:
            errors.append(f"{label} duplicate {key} {value}")
        ids.add(value)
    return ids


def _validate_sequence_integrity(value: Any, frame_count: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("integrity must be an object")
        return
    if value.get("invariant_passed") is not True:
        errors.append("integrity.invariant_passed must be true")
    sequence_hash = value.get("sequence_hash")
    if not isinstance(sequence_hash, str) or not sequence_hash:
        errors.append("integrity.sequence_hash must be non-empty")
    if value.get("frame_count") not in (None, frame_count):
        errors.append("integrity.frame_count does not match frames length")
    invariant_errors = value.get("invariant_errors")
    if invariant_errors not in (None, []):
        errors.append("integrity.invariant_errors must be empty")


def _validate_registry_rows(rows: list[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        object_id = str(row.get("object_id") or f"object_registry[{index}]")
        for key in ("kind", "category_id", "source"):
            if not row.get(key):
                errors.append(f"object {object_id} missing {key}")
        if not isinstance(row.get("open_tags"), list) or not row.get("open_tags"):
            errors.append(f"object {object_id} missing open_tags")
        _check_probability(row.get("confidence"), f"object {object_id} confidence", errors)
        _check_probability(row.get("category_confidence"), f"object {object_id} category_confidence", errors)
        if not row.get("dynamic", False) and row.get("map_coord") is None:
            errors.append(f"static object {object_id} missing map_coord")


def _validate_frame_chain(frames: list[Any], errors: list[str]) -> None:
    previous_hash: str | None = None
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            errors.append(f"frames[{index}] must be an object")
            continue
        integrity = frame.get("integrity")
        if integrity is None:
            previous_hash = None
            continue
        if not isinstance(integrity, dict):
            errors.append(f"frame {frame.get('tick', index)} integrity must be an object")
            previous_hash = None
            continue
        if integrity.get("invariant_passed") is not True:
            errors.append(f"frame {frame.get('tick', index)} integrity.invariant_passed must be true")
        if integrity.get("invariant_errors") not in (None, []):
            errors.append(f"frame {frame.get('tick', index)} invariant_errors must be empty")
        frame_hash = integrity.get("frame_hash")
        if not isinstance(frame_hash, str) or not frame_hash:
            errors.append(f"frame {frame.get('tick', index)} missing frame_hash")
        if integrity.get("prev_frame_hash") != previous_hash:
            errors.append(f"frame {frame.get('tick', index)} prev_frame_hash does not chain")
        previous_hash = frame_hash if isinstance(frame_hash, str) else None


def _validate_frames(
    frames: list[Any],
    object_ids: set[str],
    branch_ids: set[str],
    errors: list[str],
) -> None:
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue
        label = f"frame {frame.get('tick', index)}"
        outcome = frame.get("outcome")
        if isinstance(outcome, dict):
            _check_known(outcome.get("branch_id"), branch_ids, f"{label} outcome branch_id", errors)
        for ray_index, ray in enumerate(frame.get("rays") or []):
            if not isinstance(ray, dict):
                errors.append(f"{label} rays[{ray_index}] must be an object")
                continue
            contact = ray.get("contact")
            if not isinstance(contact, dict):
                errors.append(f"{label} rays[{ray_index}] missing contact")
                continue
            _check_known_object(contact.get("object_id"), object_ids, f"{label} ray contact", errors)
        for datum_index, datum in enumerate((frame.get("chronometric") or {}).get("potential_datapoints") or []):
            if not isinstance(datum, dict):
                errors.append(f"{label} potential_datapoints[{datum_index}] must be an object")
                continue
            _check_known_object(datum.get("object_id"), object_ids, f"{label} potential datum", errors)
            provenance = datum.get("provenance")
            if not isinstance(provenance, dict):
                errors.append(f"{label} potential datum missing provenance")
            else:
                _check_known(provenance.get("branch_id"), branch_ids, f"{label} potential datum provenance branch_id", errors, allow_none=True)
                _check_probability(provenance.get("confidence"), f"{label} potential datum provenance confidence", errors)


def _validate_branch_rows(rows: list[Any], object_ids: set[str], errors: list[str]) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        branch_id = str(row.get("branch_id") or "unknown_branch")
        if not row.get("action_id"):
            errors.append(f"branch {branch_id} missing action_id")
        for key in ("supporting_objects", "risk_objects"):
            for object_id in row.get(key) or []:
                _check_known_object(object_id, object_ids, f"branch {branch_id} {key}", errors)


def _validate_branch_potentials(
    rows: list[Any],
    branch_ids: set[str],
    object_ids: set[str],
    errors: list[str],
) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        potential_id = str(row.get("potential_id") or "unknown_potential")
        _check_known(row.get("branch_id"), branch_ids, f"branch potential {potential_id} branch_id", errors)
        _check_known_object(row.get("object_id"), object_ids, f"branch potential {potential_id}", errors)
        for key in ("outcome_probability", "positive_probability", "negative_probability", "uncertainty"):
            _check_probability(row.get(key), f"branch potential {potential_id} {key}", errors)
        _check_signed(row.get("chrono_y_correlation"), f"branch potential {potential_id} chrono_y_correlation", errors)


def _validate_object_links(
    rows: list[Any],
    branch_ids: set[str],
    object_ids: set[str],
    potential_ids: set[str],
    errors: list[str],
) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        link_id = str(row.get("link_id") or "unknown_link")
        _check_known(row.get("branch_id"), branch_ids, f"object link {link_id} branch_id", errors)
        _check_known_object(row.get("source_object_id"), object_ids, f"object link {link_id} source_object_id", errors)
        _check_known_object(row.get("target_object_id"), object_ids, f"object link {link_id} target_object_id", errors)
        _check_probability(row.get("probability"), f"object link {link_id} probability", errors)
        _check_signed(row.get("chrono_y_correlation"), f"object link {link_id} chrono_y_correlation", errors)
        for ref in row.get("evidence_sources") or []:
            if isinstance(ref, str) and ref.startswith("bp:") and ref not in potential_ids:
                errors.append(f"object link {link_id} references unknown evidence {ref}")


def _validate_nemo_relay(
    payload: dict[str, Any],
    branch_ids: set[str],
    object_ids: set[str],
    potential_ids: set[str],
    link_ids: set[str],
    errors: list[str],
) -> None:
    for ref in payload.get("branch_potential_ids") or []:
        _check_known(ref, potential_ids, "nemo_relay branch_potential_ids", errors)
    for ref in payload.get("object_link_ids") or []:
        _check_known(ref, link_ids, "nemo_relay object_link_ids", errors)
    for index, question in enumerate(payload.get("open_questions") or []):
        if not isinstance(question, dict):
            errors.append(f"nemo_relay open_questions[{index}] must be an object")
            continue
        label = f"nemo_relay question {question.get('question_id', index)}"
        _check_known(question.get("branch_id"), branch_ids, f"{label} branch_id", errors, allow_none=True)
        _check_known_object(question.get("object_id"), object_ids, f"{label} object_id", errors, allow_none=True)
        _check_known(question.get("link_id"), link_ids, f"{label} link_id", errors, allow_none=True)
        for ref in question.get("hypothesis_refs") or []:
            if ref not in potential_ids and ref not in link_ids:
                errors.append(f"{label} references unknown hypothesis {ref}")


def _check_known(
    value: Any,
    known: set[str],
    label: str,
    errors: list[str],
    *,
    allow_none: bool = False,
) -> None:
    if value is None and allow_none:
        return
    if not isinstance(value, str) or not value:
        errors.append(f"{label} is missing")
    elif value not in known:
        errors.append(f"{label} references unknown id {value}")


def _check_known_object(
    value: Any,
    object_ids: set[str],
    label: str,
    errors: list[str],
    *,
    allow_none: bool = False,
) -> None:
    if value is None and allow_none:
        return
    if not isinstance(value, str) or not value:
        errors.append(f"{label} object_id is missing")
        return
    if value in object_ids or value.startswith(SYNTHETIC_OBJECT_PREFIXES):
        return
    errors.append(f"{label} references unknown object {value}")


def _check_probability(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 1.0:
        errors.append(f"{label} must be in [0, 1]")


def _check_signed(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not -1.0 <= float(value) <= 1.0:
        errors.append(f"{label} must be in [-1, 1]")
