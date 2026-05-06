#!/usr/bin/env python3
"""Build a goal artifact for Dream Kernel branch-rank calibration.

The goal is intentionally narrow: terminal-positive branches in reachable,
solved proxy maps should rank first by internal branch value. This consumes the
ARC-Dream curriculum eval output and does not promote any training data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_ROWS = (
    ROOT
    / "experiments"
    / "2026-05-06_arc_dream_curriculum_eval_v001_v017_support_scout"
    / "curriculum_eval_rows.jsonl"
)
DEFAULT_EVAL_METRICS = (
    ROOT
    / "experiments"
    / "2026-05-06_arc_dream_curriculum_eval_v001_v017_support_scout"
    / "metrics.json"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_goal_v035_dream_kernel_branch_rank_calibration"
GOAL_SCHEMA = "dream_kernel.goal.branch_rank_calibration.v001"
CASE_SCHEMA = "dream_kernel.goal.branch_rank_case.v001"


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
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{_rel(path)}:{line_no} is not valid JSON: {error}") from error
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    _prepare_out_dir(out_dir)
    eval_rows_path = args.eval_rows.resolve()
    eval_metrics_path = args.eval_metrics.resolve()
    rows = _read_jsonl(eval_rows_path)
    eval_metrics = json.loads(eval_metrics_path.read_text(encoding="utf-8"))
    cases = build_cases(rows)
    condition = condition_payload(args, out_dir, eval_rows_path, eval_metrics_path)
    goal = goal_payload(args, rows, cases, eval_metrics)
    metrics = metrics_payload(condition, goal, rows, cases)

    _write_jsonl(out_dir / "calibration_cases.jsonl", cases)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "goal.json").write_text(json.dumps(goal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def _prepare_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty experiment directory: {_rel(out_dir)}")
    out_dir.mkdir(parents=True, exist_ok=True)


def build_cases(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for row in rows:
        if row.get("failure_reason") != "branch_rank_top_mismatch":
            continue
        if not row.get("proxy_goal_reachable_avoiding_hazard") or not row.get("proxy_goal_solved"):
            continue
        rank = int(row["terminal_positive_branch_rank"])
        gap = float(row["branch_rank_gap_to_top"])
        target_delta = gap + 1e-6
        cases.append(
            {
                "schema": CASE_SCHEMA,
                "case_id": f"branch_rank_goal:{int(row['curriculum_index']):04d}",
                "challenge_id": row["challenge_id"],
                "curriculum_index": row["curriculum_index"],
                "tier_label": row["tier_label"],
                "failure_reason": row["failure_reason"],
                "sequence_path": row["sequence_path"],
                "map_path": row["map_path"],
                "source": row["source"],
                "quarantine_status": row["quarantine_status"],
                "training_data_promoted": False,
                "terminal_positive_branch_id": row["terminal_positive_branch_id"],
                "terminal_positive_branch_rank_before": rank,
                "terminal_positive_branch_chrono_y_net_before": row["terminal_positive_branch_chrono_y_net"],
                "top_branch_id_before": row["top_branch_id"],
                "top_branch_chrono_y_net_before": row["top_branch_chrono_y_net"],
                "branch_rank_gap_to_top_before": gap,
                "required_margin_delta": round(target_delta, 9),
                "target_terminal_positive_branch_rank": 1,
                "target_branch_rank_top_match": True,
                "allowed_signal_families": [
                    "distance_to_terminal_goal",
                    "terminal_reward_observed_posthoc_for_calibration",
                    "reachable_safe_path_progress",
                    "ray_beneficial_contact_alignment",
                    "ray_adversarial_exposure",
                    "chronometric_y_calibration_error",
                ],
                "forbidden_inputs": [
                    "source_arc_answer",
                    "training_label_promotion",
                    "direct_heldout_target_leakage",
                    "observed_outcome_as_pre_action_perception",
                ],
            }
        )
    return sorted(cases, key=lambda row: int(row["curriculum_index"]))


def condition_payload(
    args: argparse.Namespace,
    out_dir: Path,
    eval_rows_path: Path,
    eval_metrics_path: Path,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "run_label": args.run_label,
        "run_kind": "dream_kernel_branch_rank_calibration_goal_definition",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": GOAL_SCHEMA,
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "source_eval_rows": _rel(eval_rows_path),
        "source_eval_rows_sha256": _sha256(eval_rows_path),
        "source_eval_metrics": _rel(eval_metrics_path),
        "source_eval_metrics_sha256": _sha256(eval_metrics_path),
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "metric_to_compare": "terminal_positive_branch_rank_1_on_reachable_solved_proxy_maps",
        "goal_stop_rule": "branch_rank_top_mismatch_count == 0 and proxy_goal_unreachable_in_projection_count == 0",
    }


def goal_payload(
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    eval_metrics: dict[str, Any],
) -> dict[str, Any]:
    overall = (eval_metrics.get("aggregate") or {}).get("overall") or {}
    failure_reasons = (eval_metrics.get("aggregate") or {}).get("failure_reasons") or {}
    return {
        "schema": GOAL_SCHEMA,
        "goal_id": args.run_label,
        "goal_name": "Dream Kernel branch-rank calibration",
        "goal_statement": (
            "For every reachable solved ARC-Dream proxy map, the internal branch matrix "
            "must rank the terminal-positive branch first."
        ),
        "why_this_is_good": (
            "The kernel already solves the maps and preserves object/ray integrity. "
            "The remaining failure is therefore a clean value-calibration target."
        ),
        "source_row_count": len(rows),
        "calibration_case_count": len(cases),
        "baseline": {
            "proxy_goal_solve_rate": overall.get("proxy_goal_solve_rate"),
            "planner_integrity_pass_rate": overall.get("planner_integrity_pass_rate"),
            "branch_rank_top_match_rate": overall.get("branch_rank_top_match_rate"),
            "terminal_branch_rank_counts": overall.get("terminal_branch_rank_counts"),
            "failure_reasons": failure_reasons,
        },
        "success_criteria": {
            "branch_rank_top_mismatch_count": 0,
            "planner_integrity_pass_rate": 1.0,
            "terminal_branch_rank_counts_allowed": {"1": "all reachable solved proxy maps"},
            "proxy_goal_unreachable_in_projection_count": 0,
            "training_data_promoted": False,
            "arc_solve_claim": False,
        },
        "iteration_constraints": [
            "Use reachable solved proxy rows as calibration cases, not as ARC answer evidence.",
            "Separate projection-map reachability fixes from branch-value calibration.",
            "Nemo may produce semantic hypotheses, but Dream Kernel branch scoring remains the measured driver.",
            "Do not weaken object identity, ray contact, or invariant gates to improve the score.",
        ],
    }


def metrics_payload(
    condition: dict[str, Any],
    goal: dict[str, Any],
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    rank_counts = Counter(str(row["terminal_positive_branch_rank_before"]) for row in cases)
    tier_counts = Counter(row["tier_label"] for row in cases)
    failure_counts = Counter(row.get("failure_reason") for row in rows)
    gaps = [float(row["branch_rank_gap_to_top_before"]) for row in cases]
    return {
        "schema": GOAL_SCHEMA,
        "condition": condition,
        "goal": goal,
        "source_row_count": len(rows),
        "calibration_case_count": len(cases),
        "case_tier_counts": dict(sorted(tier_counts.items())),
        "case_terminal_rank_counts": dict(sorted(rank_counts.items())),
        "case_failure_counts": dict(sorted(failure_counts.items())),
        "gap_stats": {
            "min": min(gaps) if gaps else None,
            "max": max(gaps) if gaps else None,
            "mean": sum(gaps) / len(gaps) if gaps else None,
        },
        "ready_for_goal_loop": bool(cases),
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    goal = metrics["goal"]
    lines = [
        "# Dream Kernel Branch-Rank Calibration Goal V035",
        "",
        "Status: goal artifact built from ARC-Dream proxy eval. No training data promoted.",
        "",
        "This is not an ARC solve claim. It is a branch-value calibration target.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- source eval rows: `{condition['source_eval_rows']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Goal",
        "",
        goal["goal_statement"],
        "",
        "## Baseline",
        "",
        f"- proxy goal solve rate: `{goal['baseline']['proxy_goal_solve_rate']}`",
        f"- planner integrity pass rate: `{goal['baseline']['planner_integrity_pass_rate']}`",
        f"- branch-rank top-match rate: `{goal['baseline']['branch_rank_top_match_rate']}`",
        f"- terminal branch rank counts: `{goal['baseline']['terminal_branch_rank_counts']}`",
        f"- failure reasons: `{goal['baseline']['failure_reasons']}`",
        "",
        "## Calibration Cases",
        "",
        f"- cases: `{metrics['calibration_case_count']}`",
        f"- by tier: `{metrics['case_tier_counts']}`",
        f"- terminal rank before: `{metrics['case_terminal_rank_counts']}`",
        f"- rank-gap stats: `{metrics['gap_stats']}`",
        "",
        "## Stop Rule",
        "",
        f"`{condition['goal_stop_rule']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-rows", type=Path, default=DEFAULT_EVAL_ROWS)
    parser.add_argument("--eval-metrics", type=Path, default=DEFAULT_EVAL_METRICS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="goal_v035_dream_kernel_branch_rank_calibration")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "calibration_case_count": metrics["calibration_case_count"],
                "case_tier_counts": metrics["case_tier_counts"],
                "ready_for_goal_loop": metrics["ready_for_goal_loop"],
                "out_dir": _rel(args.out_dir.resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
