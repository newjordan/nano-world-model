#!/usr/bin/env python3
"""Run a pre-action branch-choice smoke over Dream Kernel proxy maps.

This consumes a prior ARC-Dream proxy eval, replays each projected map through
the deterministic Dream Kernel, and checks whether the pre-action policy score
selects a branch that matches a shortest-safe-path oracle. The oracle is derived
from the trusted proxy map only; it is diagnostic and is not used by the policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_EVAL = ROOT / "experiments" / "2026-05-06_arc_dream_curriculum_eval_v002_branch_value_projection_repair"
DEFAULT_SOURCE_ROWS = DEFAULT_SOURCE_EVAL / "curriculum_eval_rows.jsonl"
DEFAULT_SOURCE_METRICS = DEFAULT_SOURCE_EVAL / "metrics.json"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_dream_kernel_branch_choice_v037_pre_action_oracle"
KERNEL_MANIFEST = ROOT / "dream_kernel" / "Cargo.toml"
KERNEL_BIN = ROOT / "dream_kernel" / "target" / "debug" / "dream-kernel"
SCHEMA = "dream_kernel.branch_choice_smoke.v001"
DECISION_ROW_SCHEMA = "dream_kernel.branch_choice_decision.v001"
CANDIDATE_ROW_SCHEMA = "dream_kernel.branch_choice_candidate.v001"
NEG_INF = -1_000_000_000.0


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_dirty(*, ignored_paths: list[Path] | None = None) -> bool:
    status = _git(["status", "--short", "--untracked-files=all"])
    if status == "unknown":
        return True
    ignored = [_rel(path).rstrip("/") for path in ignored_paths or []]
    for line in status.splitlines():
        status_path = line[3:].strip()
        if " -> " in status_path:
            status_path = status_path.split(" -> ", 1)[1]
        if any(status_path == item or status_path.startswith(f"{item}/") for item in ignored):
            continue
        return True
    return False


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{_rel(path)}:{line_no} is not valid JSON: {error}") from error
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    _prepare_out_dir(out_dir)
    source_rows_path = args.source_rows.resolve()
    source_metrics_path = args.source_metrics.resolve()
    source_rows = _read_jsonl(source_rows_path)
    if args.max_maps is not None:
        source_rows = source_rows[: args.max_maps]
    if not source_rows:
        raise ValueError(f"no source rows loaded from {_rel(source_rows_path)}")

    build_command = ["cargo", "build", "--manifest-path", str(KERNEL_MANIFEST)]
    subprocess.run(build_command, cwd=ROOT, text=True, check=True)

    decision_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    for source_row in source_rows:
        scenario_row, decisions, candidates = run_source_row(source_row, out_dir, args.max_steps)
        scenario_rows.append(scenario_row)
        decision_rows.extend(decisions)
        candidate_rows.extend(candidates)

    condition = condition_payload(args, out_dir, source_rows_path, source_metrics_path, build_command)
    metrics = {
        "schema": SCHEMA,
        "condition": condition,
        "source_row_count": len(source_rows),
        "scenario_summary": summarize_scenarios(scenario_rows),
        "decision_summary": summarize_decisions(decision_rows),
        "candidate_summary": summarize_candidates(candidate_rows),
        "source_gate_summary": summarize_source_gates(source_rows),
    }

    _write_jsonl(out_dir / "scenario_rows.jsonl", scenario_rows)
    _write_jsonl(out_dir / "branch_choice_rows.jsonl", decision_rows)
    _write_jsonl(out_dir / "branch_choice_candidates.jsonl", candidate_rows)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def _prepare_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty experiment directory: {_rel(out_dir)}")
    (out_dir / "sequences").mkdir(parents=True, exist_ok=True)
    (out_dir / "solver_summaries").mkdir(parents=True, exist_ok=True)


def run_source_row(
    source_row: dict[str, Any],
    out_dir: Path,
    max_steps: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    map_path = (ROOT / source_row["map_path"]).resolve()
    map_rows = read_map_rows(map_path)
    case_id = case_id_from_row(source_row)
    sequence_path = out_dir / "sequences" / f"{case_id}.dream_sequence.json"
    summary_path = out_dir / "solver_summaries" / f"{case_id}.solver_summary.json"
    command = [
        str(KERNEL_BIN),
        "solve-map",
        "--map",
        str(map_path),
        "--sequence-out",
        str(sequence_path),
        "--summary-out",
        str(summary_path),
        "--name",
        str(source_row["challenge_id"]),
        "--max-steps",
        str(max_steps),
        "--expected-reward",
        "1.0",
    ]
    subprocess.run(command, cwd=ROOT, text=True, check=True)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    scenario = summary["scenario"]
    decisions, candidates = decision_rows_from_summary(
        source_row=source_row,
        scenario=scenario,
        map_rows=map_rows,
        sequence_path=sequence_path,
        summary_path=summary_path,
    )
    scenario_row = {
        "schema": "dream_kernel.branch_choice_scenario.v001",
        "challenge_id": source_row["challenge_id"],
        "curriculum_index": source_row["curriculum_index"],
        "tier_label": source_row["tier_label"],
        "map_path": source_row["map_path"],
        "sequence_path": _rel(sequence_path),
        "solver_summary_path": _rel(summary_path),
        "solved": bool(scenario.get("solved")),
        "final_reward": scenario.get("final_reward"),
        "terminal": bool(scenario.get("terminal")),
        "steps": int(scenario.get("steps") or 0),
        "branch_rank_top_match": bool(scenario.get("branch_rank_top_match")),
        "invariant_passed": bool(scenario.get("invariant_passed")),
        "decision_count": len(decisions),
        "policy_oracle_match_count": sum(1 for row in decisions if row["policy_selection_matches_oracle"]),
        "value_oracle_match_count": sum(1 for row in decisions if row["value_selection_matches_oracle"]),
        "training_data_promoted": False,
    }
    return scenario_row, decisions, candidates


def read_map_rows(path: Path) -> list[str]:
    rows = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"{_rel(path)} has no map rows")
    return rows


def decision_rows_from_summary(
    *,
    source_row: dict[str, Any],
    scenario: dict[str, Any],
    map_rows: list[str],
    sequence_path: Path,
    summary_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = []
    candidates_out = []
    for decision in scenario.get("decision_trace") or []:
        tick = int(decision.get("tick_before") or 0)
        current = coord_tuple(decision["agent_position"])
        current_distance = shortest_safe_path_steps(map_rows, current)
        candidates = []
        for candidate in decision.get("candidates") or []:
            candidate_row = enrich_candidate(candidate, map_rows, current_distance)
            candidates.append(candidate_row)
        oracle_best_score = max((row["oracle_safe_progress_score"] for row in candidates), default=NEG_INF)
        oracle_best_action_ids = sorted(
            row["action_id"] for row in candidates if row["oracle_safe_progress_score"] == oracle_best_score
        )
        if oracle_best_score <= NEG_INF / 2:
            oracle_best_action_ids = []
        policy_top = max(candidates, key=lambda row: row["policy_score"])
        value_top_score = max((row["branch_chrono_y_net"] for row in candidates), default=NEG_INF)
        value_top_action_ids = sorted(
            row["action_id"] for row in candidates if row["branch_chrono_y_net"] == value_top_score
        )
        selected_action_id = str(decision["selected_action_id"])
        policy_matches_oracle = selected_action_id in oracle_best_action_ids
        value_matches_oracle = any(action_id in oracle_best_action_ids for action_id in value_top_action_ids)
        decision_id = f"{source_row['curriculum_index']:04d}:tick{tick}"
        decision_row = {
            "schema": DECISION_ROW_SCHEMA,
            "decision_id": decision_id,
            "challenge_id": source_row["challenge_id"],
            "curriculum_index": source_row["curriculum_index"],
            "tier_label": source_row["tier_label"],
            "map_path": source_row["map_path"],
            "sequence_path": _rel(sequence_path),
            "solver_summary_path": _rel(summary_path),
            "tick_before": tick,
            "agent_position": decision["agent_position"],
            "current_shortest_safe_path_steps": current_distance,
            "candidate_count": len(candidates),
            "selected_action_id": selected_action_id,
            "policy_top_action_id": policy_top["action_id"],
            "policy_top_score": policy_top["policy_score"],
            "value_top_action_ids": value_top_action_ids,
            "value_top_score": value_top_score,
            "oracle_best_action_ids": oracle_best_action_ids,
            "oracle_best_score": oracle_best_score if oracle_best_action_ids else None,
            "policy_selection_matches_oracle": policy_matches_oracle,
            "value_selection_matches_oracle": value_matches_oracle,
            "selection_uses_oracle": False,
            "selection_uses_post_action_labels": False,
            "oracle_uses_trusted_proxy_map": True,
            "training_data_promoted": False,
            "candidates": candidates,
        }
        decisions.append(decision_row)
        for candidate in candidates:
            candidate_record = dict(candidate)
            candidate_record.update(
                {
                    "schema": CANDIDATE_ROW_SCHEMA,
                    "decision_id": decision_id,
                    "challenge_id": source_row["challenge_id"],
                    "curriculum_index": source_row["curriculum_index"],
                    "tier_label": source_row["tier_label"],
                    "tick_before": tick,
                    "selected_action_id": selected_action_id,
                    "oracle_best_action_ids": oracle_best_action_ids,
                    "policy_selection_matches_oracle": policy_matches_oracle,
                    "training_data_promoted": False,
                }
            )
            candidates_out.append(candidate_record)
    return decisions, candidates_out


def enrich_candidate(
    candidate: dict[str, Any],
    map_rows: list[str],
    current_distance: int | None,
) -> dict[str, Any]:
    next_position = candidate.get("next_position")
    next_coord = coord_tuple(next_position) if isinstance(next_position, dict) else None
    next_distance = (
        shortest_safe_path_steps(map_rows, next_coord)
        if next_coord is not None and candidate.get("outcome_accepted")
        else None
    )
    progress_delta = (
        current_distance - next_distance
        if current_distance is not None and next_distance is not None
        else None
    )
    oracle_score = oracle_safe_progress_score(candidate, next_distance, progress_delta)
    return {
        "action_id": str(candidate["action_id"]),
        "policy_score": float(candidate.get("policy_score") or 0.0),
        "branch_chrono_y_net": float(candidate.get("branch_chrono_y_net") or 0.0),
        "outcome_accepted": bool(candidate.get("outcome_accepted")),
        "outcome_reward": float(candidate.get("outcome_reward") or 0.0),
        "outcome_terminal": bool(candidate.get("outcome_terminal")),
        "outcome_reason": candidate.get("outcome_reason"),
        "next_position": next_position,
        "next_shortest_safe_path_steps": next_distance,
        "safe_path_progress_delta": progress_delta,
        "oracle_safe_progress_score": oracle_score,
        "revisit_penalty_applied": bool(candidate.get("revisit_penalty_applied")),
        "wait_penalty_applied": bool(candidate.get("wait_penalty_applied")),
        "selected_by_policy": bool(candidate.get("selected")),
    }


def oracle_safe_progress_score(
    candidate: dict[str, Any],
    next_distance: int | None,
    progress_delta: int | None,
) -> float:
    if not candidate.get("outcome_accepted"):
        return NEG_INF
    reward = float(candidate.get("outcome_reward") or 0.0)
    if bool(candidate.get("outcome_terminal")) and reward > 0.0:
        return 1_000_000.0
    if bool(candidate.get("outcome_terminal")) and reward < 0.0:
        return NEG_INF
    if next_distance is None or progress_delta is None:
        return NEG_INF
    return float(progress_delta)


def shortest_safe_path_steps(rows: list[str], start: tuple[int, int] | None) -> int | None:
    if start is None:
        return None
    goals = set()
    blocked = set()
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell == "G":
                goals.add((x, y))
            elif cell in {"#", "H", "O"}:
                blocked.add((x, y))
    if not goals or start in blocked:
        return None
    queue: deque[tuple[tuple[int, int], int]] = deque([(start, 0)])
    seen = {start}
    while queue:
        (x, y), distance = queue.popleft()
        if (x, y) in goals:
            return distance
        for dx, dy in ((1, 0), (0, 1), (0, -1), (-1, 0)):
            candidate = (x + dx, y + dy)
            cx, cy = candidate
            if cy < 0 or cy >= len(rows) or cx < 0 or cx >= len(rows[cy]):
                continue
            if candidate in seen or candidate in blocked:
                continue
            seen.add(candidate)
            queue.append((candidate, distance + 1))
    return None


def coord_tuple(coord: dict[str, Any] | None) -> tuple[int, int] | None:
    if not isinstance(coord, dict):
        return None
    return (int(coord["x"]), int(coord["y"]))


def case_id_from_row(row: dict[str, Any]) -> str:
    suffix = str(row["challenge_id"]).split(":")[-1]
    safe_suffix = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in suffix)
    return f"{int(row['curriculum_index']):04d}_{safe_suffix}"


def summarize_scenarios(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    return {
        "scenario_count": count,
        "solved": sum(1 for row in rows if row["solved"]),
        "terminal": sum(1 for row in rows if row["terminal"]),
        "branch_rank_top_match": sum(1 for row in rows if row["branch_rank_top_match"]),
        "invariant_passed": sum(1 for row in rows if row["invariant_passed"]),
        "total_steps": sum(int(row["steps"]) for row in rows),
        "decision_count": sum(int(row["decision_count"]) for row in rows),
    }


def summarize_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    matched = sum(1 for row in rows if row["policy_selection_matches_oracle"])
    value_matched = sum(1 for row in rows if row["value_selection_matches_oracle"])
    by_tier = {}
    for tier, tier_rows in rows_by(rows, "tier_label").items():
        by_tier[tier] = {
            "decisions": len(tier_rows),
            "policy_oracle_match_rate": rate(tier_rows, "policy_selection_matches_oracle"),
            "value_oracle_match_rate": rate(tier_rows, "value_selection_matches_oracle"),
        }
    return {
        "decisions": count,
        "policy_oracle_match_count": matched,
        "policy_oracle_match_rate": matched / max(1, count),
        "value_oracle_match_count": value_matched,
        "value_oracle_match_rate": value_matched / max(1, count),
        "by_tier": by_tier,
    }


def summarize_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candidates": len(rows),
        "selected_by_policy": sum(1 for row in rows if row["selected_by_policy"]),
        "accepted": sum(1 for row in rows if row["outcome_accepted"]),
        "terminal_positive": sum(1 for row in rows if row["outcome_terminal"] and row["outcome_reward"] > 0.0),
        "outcome_reasons": dict(sorted(Counter(str(row["outcome_reason"]) for row in rows).items())),
    }


def summarize_source_gates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_rows": len(rows),
        "passed_proxy_gate": sum(1 for row in rows if row.get("failure_reason") == "passed_proxy_gate"),
        "branch_rank_top_mismatch": sum(1 for row in rows if row.get("failure_reason") == "branch_rank_top_mismatch"),
        "proxy_goal_unreachable_in_projection": sum(
            1 for row in rows if row.get("failure_reason") == "proxy_goal_unreachable_in_projection"
        ),
        "object_identity_integrity": sum(1 for row in rows if row.get("object_identity_integrity")),
        "ray_contacts_have_object_ids": sum(1 for row in rows if row.get("ray_contacts_have_object_ids")),
        "training_data_promoted": sum(1 for row in rows if row.get("training_data_promoted")),
    }


def rows_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key))].append(row)
    return dict(sorted(grouped.items()))


def rate(rows: list[dict[str, Any]], key: str) -> float:
    return sum(1 for row in rows if row.get(key)) / max(1, len(rows))


def condition_payload(
    args: argparse.Namespace,
    out_dir: Path,
    source_rows_path: Path,
    source_metrics_path: Path,
    build_command: list[str],
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    source_metrics = json.loads(source_metrics_path.read_text(encoding="utf-8"))
    source_condition = source_metrics.get("condition") or {}
    return {
        "schema": SCHEMA,
        "run_label": args.run_label,
        "run_kind": "deterministic_dream_kernel_pre_action_branch_choice_smoke",
        "run_label_semantics": "scout_pre_action_branch_choice_from_v036_proxy_maps",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "source_condition_artifact": _rel(source_metrics_path),
        "source_eval_rows": _rel(source_rows_path),
        "source_eval_rows_sha256": _sha256(source_rows_path),
        "source_eval_metrics": _rel(source_metrics_path),
        "source_eval_metrics_sha256": _sha256(source_metrics_path),
        "source_eval_run_label": source_condition.get("run_label"),
        "source_eval_metric": source_condition.get("metric_to_compare"),
        "dataset_path": _rel(source_rows_path),
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_deterministic_greedy_planner",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": "not_applicable_posthoc_local_replay",
        "loader_mode": "jsonl_arc_dream_eval_rows_with_existing_proxy_maps",
        "loader_settings": {
            "candidate_actions": ["east", "south", "north", "west", "wait"],
            "oracle": "shortest_safe_path_on_trusted_proxy_map",
            "max_ray_range": 16,
            "max_steps": args.max_steps,
        },
        "quantization_policy": "none",
        "compile_kernel_policy": "cargo_dev_profile",
        "kernel_build_command": build_command,
        "metric_to_compare": "pre_action_policy_oracle_match_rate",
        "historical_comparator": "none_first_dream_kernel_pre_action_branch_choice_smoke",
        "historical_comparator_artifact": None,
        "selection_uses_oracle": False,
        "selection_uses_post_action_labels": False,
        "oracle_uses_trusted_proxy_map": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    scenario = metrics["scenario_summary"]
    decision = metrics["decision_summary"]
    source = metrics["source_gate_summary"]
    lines = [
        "# Dream Kernel Branch Choice V037 Results",
        "",
        "Status: deterministic pre-action branch-choice scout. No training data promoted.",
        "",
        "This is not an ARC solve claim. It checks whether the policy score emitted before each action matches a trusted-map shortest-safe-path oracle.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- source eval rows: `{condition['source_eval_rows']}`",
        f"- source eval metrics: `{condition['source_eval_metrics']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        f"- selection uses oracle: `{condition['selection_uses_oracle']}`",
        f"- selection uses post-action labels: `{condition['selection_uses_post_action_labels']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Metrics",
        "",
        f"- scenarios solved: `{scenario['solved']}/{scenario['scenario_count']}`",
        f"- scenario invariants passed: `{scenario['invariant_passed']}/{scenario['scenario_count']}`",
        f"- source passed proxy gate: `{source['passed_proxy_gate']}/{source['source_rows']}`",
        f"- source branch-rank mismatches: `{source['branch_rank_top_mismatch']}`",
        f"- source unreachable projections: `{source['proxy_goal_unreachable_in_projection']}`",
        f"- decisions: `{decision['decisions']}`",
        f"- policy/oracle match rate: `{decision['policy_oracle_match_rate']}`",
        f"- value/oracle match rate: `{decision['value_oracle_match_rate']}`",
        "",
        "## By Tier",
        "",
        "| tier | decisions | policy/oracle | value/oracle |",
        "| --- | ---: | ---: | ---: |",
    ]
    for tier, row in decision["by_tier"].items():
        lines.append(
            f"| {tier} | {row['decisions']} | {row['policy_oracle_match_rate']} | {row['value_oracle_match_rate']} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-rows", type=Path, default=DEFAULT_SOURCE_ROWS)
    parser.add_argument("--source-metrics", type=Path, default=DEFAULT_SOURCE_METRICS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="dream_kernel_branch_choice_v037_pre_action_oracle")
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--max-maps", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "source_rows": metrics["source_row_count"],
                "decisions": metrics["decision_summary"]["decisions"],
                "policy_oracle_match_rate": metrics["decision_summary"]["policy_oracle_match_rate"],
                "value_oracle_match_rate": metrics["decision_summary"]["value_oracle_match_rate"],
                "out_dir": _rel(args.out_dir.resolve()),
                "training_data_promoted": metrics["condition"]["training_data_promoted"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
