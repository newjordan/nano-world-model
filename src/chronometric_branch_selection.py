"""Branch/action selection over chronometric planner scores."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Sequence


DEFAULT_GROUP_FIELDS = ("split", "task_id", "frame_hash", "t")
SCORE_POLICIES = ("planner", "library_or_calibration")


def select_chronometric_branches(
    rows: Iterable[dict[str, Any]],
    *,
    group_fields: Sequence[str] = DEFAULT_GROUP_FIELDS,
    score_policy: str = "library_or_calibration",
    min_group_size: int = 2,
) -> list[dict[str, Any]]:
    """Select the best branch per state group using chronometric scores.

    Selection never reads target labels. Labels are copied into the selected
    rows only so a later diagnostic summary can evaluate what happened.
    """
    if score_policy not in SCORE_POLICIES:
        raise ValueError(f"unknown score policy: {score_policy}")
    if min_group_size <= 0:
        raise ValueError("min_group_size must be positive")

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_group_key(row, group_fields)].append(row)

    selected: list[dict[str, Any]] = []
    for key, candidates in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        if len(candidates) < min_group_size:
            continue
        ranked = sorted(
            candidates,
            key=lambda row: (
                branch_selection_score(row, score_policy=score_policy),
                _number(row.get("pred_progress_prob")),
                str(row.get("action_id", "")),
            ),
            reverse=True,
        )
        best = ranked[0]
        target_best = max(_number(row.get("target_signed_y")) for row in candidates)
        output = dict(best)
        output["selection_group_key"] = _format_group_key(key)
        output["selection_group_fields"] = list(group_fields)
        output["selection_group_size"] = len(candidates)
        output["selection_score_policy"] = score_policy
        output["selection_score"] = branch_selection_score(best, score_policy=score_policy)
        output["selection_rank"] = 1
        output["selection_oracle_best_signed_y"] = target_best
        output["selection_matches_oracle_signed_best"] = _number(best.get("target_signed_y")) >= target_best - 1e-9
        selected.append(output)
    return selected


def branch_selection_score(row: dict[str, Any], *, score_policy: str = "library_or_calibration") -> float:
    if score_policy == "planner":
        return _number(row.get("planner_pred_signed_y"))
    if score_policy == "library_or_calibration":
        if row.get("planner_branch_library_applied"):
            return _number(row.get("planner_pred_signed_y"))
        return _number(row.get("pred_signed_y"))
    raise ValueError(f"unknown score policy: {score_policy}")


def summarize_branch_selection(
    selected_rows: Iterable[dict[str, Any]],
    *,
    candidate_rows: Iterable[dict[str, Any]],
    group_fields: Sequence[str] = DEFAULT_GROUP_FIELDS,
    min_group_size: int = 2,
) -> dict[str, Any]:
    selected = list(selected_rows)
    candidates = list(candidate_rows)
    all_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        all_groups[_group_key(row, group_fields)].append(row)
    selectable = [rows for rows in all_groups.values() if len(rows) >= min_group_size]

    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        by_split[str(row.get("split", "unknown"))].append(row)
    candidate_splits = sorted({str(row.get("split", "unknown")) for row in candidates} | set(by_split))
    selectable_by_split: dict[str, int] = defaultdict(int)
    for group_rows in selectable:
        split = str(group_rows[0].get("split", "unknown"))
        selectable_by_split[split] += 1
    candidate_records_by_split: dict[str, int] = defaultdict(int)
    for row in candidates:
        candidate_records_by_split[str(row.get("split", "unknown"))] += 1

    return {
        "candidate_records": len(candidates),
        "candidate_records_by_split": dict(sorted(candidate_records_by_split.items())),
        "groups": len(all_groups),
        "selectable_groups": len(selectable),
        "selectable_groups_by_split": dict(sorted(selectable_by_split.items())),
        "selected_records": len(selected),
        "skipped_groups": len(all_groups) - len(selectable),
        "by_split": {split: _summarize_selected(by_split.get(split, [])) for split in candidate_splits},
        "overall": _summarize_selected(selected),
    }


def _summarize_selected(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "selected_records": 0,
            "mean_selection_score": None,
            "mean_target_signed_y": None,
            "oracle_signed_best_match_rate": None,
            "progress_positive_selected": 0,
        }
    return {
        "selected_records": len(rows),
        "mean_selection_score": _mean([row.get("selection_score") for row in rows]),
        "mean_target_signed_y": _mean([row.get("target_signed_y") for row in rows]),
        "oracle_signed_best_match_rate": _mean(
            [1.0 if row.get("selection_matches_oracle_signed_best") else 0.0 for row in rows]
        ),
        "progress_positive_selected": sum(1 for row in rows if _number(row.get("target_progress")) >= 0.5),
        "branch_library_applied_selected": sum(1 for row in rows if row.get("planner_branch_library_applied")),
        "fallback_selected": sum(1 for row in rows if row.get("planner_branch_library_fallback_applied")),
    }


def _group_key(row: dict[str, Any], fields: Sequence[str]) -> tuple[Any, ...]:
    return tuple(row.get(field) for field in fields)


def _format_group_key(key: tuple[Any, ...]) -> str:
    return "|".join(str(part) for part in key)


def _mean(values: list[Any]) -> float | None:
    numeric = [_number(value) for value in values]
    if not numeric:
        return None
    return sum(numeric) / len(numeric)


def _number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0
