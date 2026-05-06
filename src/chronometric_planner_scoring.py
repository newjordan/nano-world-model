"""Planner-facing chronometric branch scoring helpers.

These helpers adapt row-like branch contexts from the chronometric bridge into
the same ``score_chronometric_branch`` surface exposed by NanoWM. They are a
harness bridge, not a replacement for real visual tokens from a trained model.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

import torch

from chronometric_branch_library import BranchLibraryEntry, blend_branch_library_signed_y


DEFAULT_HIDDEN_SIZE = 32
DEFAULT_FRAMES = 4
GRID_CELL_COUNT = 4096.0


def score_chronometric_branch_rows(
    scorer: Any,
    rows: Iterable[dict[str, Any]],
    *,
    branch_library: dict[str, BranchLibraryEntry] | None = None,
    branch_library_blend: float = 1.0,
    branch_library_fallback_scope: str = "none",
    hidden_size: int = DEFAULT_HIDDEN_SIZE,
    frames: int = DEFAULT_FRAMES,
    batch_size: int = 512,
    device: str | torch.device = "cpu",
    dtype: torch.dtype = torch.float32,
) -> list[dict[str, Any]]:
    """Score branch rows through a NanoWM-compatible chronometric scorer.

    ``scorer`` may be a NanoWM-like object exposing ``score_chronometric_branch``
    or a raw ``ChronometricContortionLayer`` exposing ``score_branch``. The
    returned rows include the raw scorer mean, adjusted scorer mean, and the
    branch-library entry that explains any adjustment.
    """
    row_list = list(rows)
    if hidden_size <= 0:
        raise ValueError("hidden_size must be positive")
    if frames <= 0:
        raise ValueError("frames must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    scorer_fn = _resolve_scorer(scorer)
    device = torch.device(device)
    output_rows: list[dict[str, Any]] = []
    lookup_library = branch_library or {}

    for start in range(0, len(row_list), batch_size):
        batch_rows = row_list[start : start + batch_size]
        tokens = branch_context_tokens(batch_rows, hidden_size=hidden_size, frames=frames, device=device, dtype=dtype)
        action_context = branch_action_context_tokens(
            batch_rows,
            hidden_size=hidden_size,
            frames=frames,
            device=device,
            dtype=dtype,
        )
        branch_direction = branch_direction_tensor(batch_rows, device=device, dtype=dtype)

        with torch.no_grad():
            raw_output = scorer_fn(
                tokens,
                branch_direction,
                action_context=action_context,
            )
            raw_signed = raw_output.outcome_y.mean(dim=(1, 2)).detach().cpu().tolist()

        contexts: list[dict[str, Any]] = []
        reference_values: list[float] = []
        entries: list[BranchLibraryEntry | None] = []
        for row, raw_value in zip(batch_rows, raw_signed):
            context = dict(row)
            context["pred_signed_y"] = float(raw_value)
            reference, entry = blend_branch_library_signed_y(
                context,
                lookup_library,
                blend=branch_library_blend,
                fallback_scope=branch_library_fallback_scope,
            )
            contexts.append(context)
            reference_values.append(reference)
            entries.append(entry)

        with torch.no_grad():
            adjusted_output = scorer_fn(
                tokens,
                branch_direction,
                action_context=action_context,
                branch_library=lookup_library,
                branch_library_contexts=contexts,
                branch_library_blend=branch_library_blend,
                branch_library_fallback_scope=branch_library_fallback_scope,
            )
            adjusted_signed = adjusted_output.outcome_y.mean(dim=(1, 2)).detach().cpu().tolist()

        for offset, (row, raw_value, adjusted_value, reference_value, entry) in enumerate(
            zip(batch_rows, raw_signed, adjusted_signed, reference_values, entries)
        ):
            fallback_applied = entry is not None and entry.records == 0 and entry.key.startswith("fallback:")
            output = dict(row)
            output["planner_row_index"] = start + offset
            output["planner_pred_signed_y_raw"] = float(raw_value)
            output["planner_pred_signed_y"] = float(adjusted_value)
            output["planner_reference_signed_y"] = float(reference_value)
            output["planner_reference_abs_diff"] = abs(float(adjusted_value) - float(reference_value))
            output["planner_branch_library_applied"] = entry is not None
            output["planner_branch_library_fallback_applied"] = fallback_applied
            output["planner_branch_library_key"] = entry.key if entry is not None else None
            output["planner_branch_library_records"] = entry.records if entry is not None else 0
            output["planner_branch_library_signed_y"] = entry.signed_y_mean if entry is not None else None
            output_rows.append(output)

    return output_rows


def summarize_planner_branch_scores(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    row_list = list(rows)
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in row_list:
        by_split[str(row.get("split", "unknown"))].append(row)
    return {
        "records": len(row_list),
        "applied_records": sum(1 for row in row_list if row.get("planner_branch_library_applied")),
        "fallback_records": sum(1 for row in row_list if row.get("planner_branch_library_fallback_applied")),
        "by_split": {split: _summarize_score_rows(split_rows) for split, split_rows in sorted(by_split.items())},
        "overall": _summarize_score_rows(row_list),
    }


def branch_context_tokens(
    rows: Iterable[dict[str, Any]],
    *,
    hidden_size: int,
    frames: int,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    features = [_row_feature_vector(row, hidden_size=hidden_size) for row in rows]
    tensor = torch.tensor(features, device=device, dtype=dtype)
    return tensor.unsqueeze(1).expand(len(features), frames, hidden_size).clone()


def branch_action_context_tokens(
    rows: Iterable[dict[str, Any]],
    *,
    hidden_size: int,
    frames: int,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    features = [_row_action_feature_vector(row, hidden_size=hidden_size) for row in rows]
    tensor = torch.tensor(features, device=device, dtype=dtype)
    return tensor.unsqueeze(1).expand(len(features), frames, hidden_size).clone()


def branch_direction_tensor(
    rows: Iterable[dict[str, Any]],
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    vectors = [_branch_direction(row) for row in rows]
    return torch.tensor(vectors, device=device, dtype=dtype)


def _resolve_scorer(scorer: Any) -> Callable[..., Any]:
    score_chronometric_branch = getattr(scorer, "score_chronometric_branch", None)
    if callable(score_chronometric_branch):
        return score_chronometric_branch
    score_branch = getattr(scorer, "score_branch", None)
    if callable(score_branch):
        return score_branch
    raise TypeError("scorer must expose score_chronometric_branch or score_branch")


def _summarize_score_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    applied = [row for row in rows if row.get("planner_branch_library_applied")]
    fallback = [row for row in rows if row.get("planner_branch_library_fallback_applied")]
    return {
        "records": len(rows),
        "applied_records": len(applied),
        "fallback_records": len(fallback),
        "unapplied_records": len(rows) - len(applied),
        "applied_reference_mae": _mean([row.get("planner_reference_abs_diff") for row in applied]),
        "applied_reference_max_abs_diff": _max([row.get("planner_reference_abs_diff") for row in applied]),
        "applied_target_signed_mae": _mean(
            [
                abs(_number(row.get("planner_pred_signed_y")) - _number(row.get("target_signed_y")))
                for row in applied
            ]
        ),
    }


def _row_feature_vector(row: dict[str, Any], *, hidden_size: int) -> list[float]:
    values = [
        _number(row.get("t")) / 200.0,
        _action_value(row.get("action_id")),
        _number(row.get("changed_cells")) / GRID_CELL_COUNT,
    ]
    values.extend(_sequence(row.get("event_mu"), 4))
    values.extend(_sequence(row.get("branch_direction_n"), 4))
    values.extend(_sequence(row.get("dominant_movement_vector"), 2))
    values.extend(_sequence(row.get("action_context"), 8))
    values.extend(_sequence(row.get("potential_family_vector"), 8))
    return _fit(values, hidden_size)


def _row_action_feature_vector(row: dict[str, Any], *, hidden_size: int) -> list[float]:
    values = [
        _action_value(row.get("action_id")),
        1.0 if _number(row.get("target_progress")) >= 0.5 else 0.0,
        _number(row.get("changed_cells")) / GRID_CELL_COUNT,
    ]
    values.extend(_sequence(row.get("action_context"), 8))
    values.extend(_sequence(row.get("potential_family_vector"), 8))
    return _fit(values, hidden_size)


def _branch_direction(row: dict[str, Any]) -> list[float]:
    direction = _sequence(row.get("branch_direction_n"), 4)
    if any(abs(value) > 0.0 for value in direction):
        return direction
    movement = _sequence(row.get("dominant_movement_vector"), 2)
    if any(abs(value) > 0.0 for value in movement):
        return [0.0, movement[0], movement[1], 0.0]
    return [0.0, 0.0, 1.0, 0.0]


def _sequence(value: Any, length: int) -> list[float]:
    if isinstance(value, (list, tuple)):
        return [_number(item) for item in value[:length]] + [0.0] * max(0, length - len(value))
    return [0.0] * length


def _fit(values: list[float], hidden_size: int) -> list[float]:
    if len(values) >= hidden_size:
        return values[:hidden_size]
    return values + [0.0] * (hidden_size - len(values))


def _action_value(value: Any) -> float:
    text = str(value).upper()
    if text.startswith("ACTION"):
        try:
            return float(text.replace("ACTION", "")) / 10.0
        except ValueError:
            return 0.0
    return 0.0


def _mean(values: list[Any]) -> float | None:
    numeric = [_number(value) for value in values]
    if not numeric:
        return None
    return sum(numeric) / len(numeric)


def _max(values: list[Any]) -> float | None:
    numeric = [_number(value) for value in values]
    if not numeric:
        return None
    return max(numeric)


def _number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0
