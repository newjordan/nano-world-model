#!/usr/bin/env python3
"""Run ARC-to-Dream proxy curriculum maps through the deterministic Dream Kernel.

This runner evaluates the projected known maps created by
build_arc_dream_curriculum.py. It is a simulator/proxy gate, not an ARC answer
benchmark and not training-data promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRICULUM = (
    ROOT
    / "experiments"
    / "2026-05-06_arc_dream_curriculum_v001_v017_support_scout"
    / "curriculum_challenges.jsonl"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_dream_curriculum_eval_v001_v017_support_scout"
KERNEL_MANIFEST = ROOT / "dream_kernel" / "Cargo.toml"
KERNEL_MAIN = ROOT / "dream_kernel" / "src" / "main.rs"
KERNEL_LIB = ROOT / "dream_kernel" / "src" / "lib.rs"
KERNEL_BIN = ROOT / "dream_kernel" / "target" / "debug" / "dream-kernel"
EVAL_SCHEMA = "dream_kernel.arc_dream_curriculum_eval.v001"
ROW_SCHEMA = "dream_kernel.arc_dream_curriculum_eval_row.v001"


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
    curriculum_path = args.curriculum.resolve()
    out_dir = args.out_dir.resolve()
    _prepare_out_dir(out_dir)

    challenges = _read_jsonl(curriculum_path)
    if args.max_challenges is not None:
        challenges = challenges[: args.max_challenges]
    if not challenges:
        raise ValueError(f"no challenges loaded from {_rel(curriculum_path)}")

    build_command = ["cargo", "build", "--manifest-path", str(KERNEL_MANIFEST)]
    subprocess.run(build_command, cwd=ROOT, text=True, check=True)

    rows = []
    for challenge in challenges:
        rows.append(_run_challenge(challenge, out_dir, args.max_steps))

    condition = _condition(args, out_dir, curriculum_path, challenges, build_command)
    metrics = {
        "schema": EVAL_SCHEMA,
        "condition": condition,
        "row_count": len(rows),
        "aggregate": aggregate_rows(rows),
    }

    _write_jsonl(out_dir / "curriculum_eval_rows.jsonl", rows)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def _prepare_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty experiment directory: {_rel(out_dir)}")
    (out_dir / "maps").mkdir(parents=True, exist_ok=True)
    (out_dir / "sequences").mkdir(parents=True, exist_ok=True)
    (out_dir / "solver_summaries").mkdir(parents=True, exist_ok=True)


def _run_challenge(challenge: dict[str, Any], out_dir: Path, max_steps: int) -> dict[str, Any]:
    case_id = _case_id(challenge)
    projection = challenge["dream_kernel_projection"]
    map_path = out_dir / "maps" / f"{case_id}.map.txt"
    sequence_path = out_dir / "sequences" / f"{case_id}.dream_sequence.json"
    summary_path = out_dir / "solver_summaries" / f"{case_id}.solver_summary.json"
    write_map(map_path, projection["known_map_ascii"])
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
        str(challenge["challenge_id"]),
        "--max-steps",
        str(max_steps),
        "--expected-reward",
        "1.0",
    ]
    subprocess.run(command, cwd=ROOT, text=True, check=True)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    sequence = json.loads(sequence_path.read_text(encoding="utf-8"))
    return eval_row_from_outputs(challenge, summary, sequence, map_path, sequence_path, summary_path, max_steps)


def write_map(path: Path, rows: list[str]) -> None:
    if not rows or not all(isinstance(row, str) and row for row in rows):
        raise ValueError("known_map_ascii must contain non-empty string rows")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("known_map_ascii rows must have equal width")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def eval_row_from_outputs(
    challenge: dict[str, Any],
    solver_summary: dict[str, Any],
    sequence: dict[str, Any],
    map_path: Path,
    sequence_path: Path,
    summary_path: Path,
    max_steps: int,
) -> dict[str, Any]:
    scenario = solver_summary["scenario"]
    projection = challenge["dream_kernel_projection"]
    expected_ids = set(projection.get("object_ids_expected") or [])
    observed_ids = {entry.get("object_id") for entry in sequence.get("object_registry") or []}
    observed_ids.discard(None)
    missing_expected_ids = sorted(expected_ids - observed_ids)
    reachability = map_reachability(projection["known_map_ascii"])
    branch_diagnostic = branch_rank_diagnostic(sequence)
    ray_network_counts = _ray_network_counts(sequence)
    ray_contacts_have_ids = _ray_contacts_have_ids(sequence)
    object_identity_integrity = not missing_expected_ids and ray_contacts_have_ids
    expected_class = projection.get("expected_outcome_class")
    source_outcome_tested = expected_class == "positive_goal_progress"
    source_outcome_aligned = None
    if source_outcome_tested:
        source_outcome_aligned = bool(scenario.get("solved")) and float(scenario.get("final_reward") or 0.0) > 0.0
    policy_callback_required = bool((challenge.get("nemo_callback_policy") or {}).get("callback_required"))
    kernel_nemo_questions = ((sequence.get("nemo_relay") or {}).get("open_questions") or [])
    kernel_nemo_relay_required = bool(kernel_nemo_questions)
    branch_potentials = sequence.get("branch_potentials") or []
    branch_potentials_requiring_nemo = sum(1 for row in branch_potentials if row.get("nemo_relay_required"))
    planner_integrity_passed = bool(
        scenario.get("solved")
        and reachability["goal_reachable_avoiding_hazard"]
        and scenario.get("invariant_passed")
        and object_identity_integrity
        and scenario.get("branch_rank_top_match")
    )
    return {
        "schema": ROW_SCHEMA,
        "challenge_id": challenge["challenge_id"],
        "curriculum_index": challenge["curriculum_index"],
        "tier_index": challenge["tier_index"],
        "tier_label": challenge["tier_label"],
        "difficulty_score": challenge["difficulty_score"],
        "source": challenge["source"],
        "quarantine_status": challenge["quarantine_status"],
        "training_data_promoted": False,
        "map_path": _rel(map_path),
        "sequence_path": _rel(sequence_path),
        "solver_summary_path": _rel(summary_path),
        "max_steps": max_steps,
        "proxy_goal_solved": bool(scenario.get("solved")),
        "proxy_goal_reachable_avoiding_hazard": reachability["goal_reachable_avoiding_hazard"],
        "proxy_goal_shortest_safe_path_steps": reachability["shortest_safe_path_steps"],
        "terminal": bool(scenario.get("terminal")),
        "final_reward": scenario.get("final_reward"),
        "final_reason": scenario.get("final_reason"),
        "steps": int(scenario.get("steps") or 0),
        "planned_actions": scenario.get("planned_actions") or [],
        "accepted_steps": int(scenario.get("accepted_steps") or 0),
        "rejected_steps": int(scenario.get("rejected_steps") or 0),
        "branch_rank_top_match": bool(scenario.get("branch_rank_top_match")),
        "terminal_positive_branch_id": branch_diagnostic["terminal_positive_branch_id"],
        "terminal_positive_branch_rank": branch_diagnostic["terminal_positive_branch_rank"],
        "terminal_positive_branch_chrono_y_net": branch_diagnostic["terminal_positive_branch_chrono_y_net"],
        "top_branch_id": branch_diagnostic["top_branch_id"],
        "top_branch_chrono_y_net": branch_diagnostic["top_branch_chrono_y_net"],
        "branch_rank_gap_to_top": branch_diagnostic["branch_rank_gap_to_top"],
        "invariant_passed": bool(scenario.get("invariant_passed")),
        "sequence_hash": scenario.get("sequence_hash"),
        "object_identity_integrity": object_identity_integrity,
        "missing_expected_object_ids": missing_expected_ids,
        "ray_contacts_have_object_ids": ray_contacts_have_ids,
        "ray_network_counts": ray_network_counts,
        "branch_potential_count": len(branch_potentials),
        "branch_potentials_requiring_nemo": branch_potentials_requiring_nemo,
        "nemo_policy_callback_required": policy_callback_required,
        "kernel_nemo_relay_required": kernel_nemo_relay_required,
        "kernel_nemo_open_question_count": len(kernel_nemo_questions),
        "nemo_callback_available_for_policy": (not policy_callback_required) or kernel_nemo_relay_required,
        "source_expected_outcome_class": expected_class,
        "source_expected_outcome_tested": source_outcome_tested,
        "source_expected_outcome_aligned": source_outcome_aligned,
        "planner_integrity_passed": planner_integrity_passed,
        "failure_reason": failure_reason(
            scenario,
            object_identity_integrity,
            reachability["goal_reachable_avoiding_hazard"],
            source_outcome_tested,
            source_outcome_aligned,
        ),
    }


def aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "overall": _aggregate_subset(rows),
        "by_tier": {tier: _aggregate_subset(tier_rows) for tier, tier_rows in _rows_by_tier(rows).items()},
        "failure_reasons": dict(sorted(Counter(row["failure_reason"] for row in rows).items())),
        "ray_network_totals": _sum_ray_networks(rows),
    }


def _aggregate_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    accepted = sum(int(row.get("accepted_steps") or 0) for row in rows)
    rejected = sum(int(row.get("rejected_steps") or 0) for row in rows)
    tested = [row for row in rows if row.get("source_expected_outcome_tested")]
    aligned = [row for row in tested if row.get("source_expected_outcome_aligned")]
    return {
        "challenge_count": count,
        "proxy_goal_solved": sum(1 for row in rows if row.get("proxy_goal_solved")),
        "proxy_goal_solve_rate": _rate(rows, "proxy_goal_solved"),
        "planner_integrity_passed": sum(1 for row in rows if row.get("planner_integrity_passed")),
        "planner_integrity_pass_rate": _rate(rows, "planner_integrity_passed"),
        "invariant_pass_rate": _rate(rows, "invariant_passed"),
        "object_identity_pass_rate": _rate(rows, "object_identity_integrity"),
        "branch_rank_top_match_rate": _rate(rows, "branch_rank_top_match"),
        "accepted_step_rate": accepted / max(1, accepted + rejected),
        "total_steps": sum(int(row.get("steps") or 0) for row in rows),
        "rejected_steps": rejected,
        "nemo_policy_callback_required": sum(1 for row in rows if row.get("nemo_policy_callback_required")),
        "kernel_nemo_relay_required": sum(1 for row in rows if row.get("kernel_nemo_relay_required")),
        "nemo_callback_available_for_policy_rate": _rate(rows, "nemo_callback_available_for_policy"),
        "source_expected_outcome_tested": len(tested),
        "source_expected_outcome_alignment_rate": len(aligned) / max(1, len(tested)),
        "proxy_goal_reachable_avoiding_hazard": sum(
            1 for row in rows if row.get("proxy_goal_reachable_avoiding_hazard")
        ),
        "proxy_goal_reachable_avoiding_hazard_rate": _rate(rows, "proxy_goal_reachable_avoiding_hazard"),
        "terminal_branch_rank_counts": _terminal_branch_rank_counts(rows),
    }


def _rows_by_tier(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    tiers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        tiers[row["tier_label"]].append(row)
    return dict(sorted(tiers.items()))


def _sum_ray_networks(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.get("ray_network_counts") or {})
    return dict(sorted(counter.items()))


def _terminal_branch_rank_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        rank = row.get("terminal_positive_branch_rank")
        counter["none" if rank is None else str(rank)] += 1
    return dict(sorted(counter.items()))


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    return sum(1 for row in rows if row.get(key)) / max(1, len(rows))


def failure_reason(
    scenario: dict[str, Any],
    object_identity_integrity: bool,
    proxy_goal_reachable: bool,
    source_outcome_tested: bool,
    source_outcome_aligned: bool | None,
) -> str:
    if not scenario.get("invariant_passed"):
        return "invariant_failed"
    if not object_identity_integrity:
        return "object_identity_failed"
    if not proxy_goal_reachable and not scenario.get("solved"):
        return "proxy_goal_unreachable_in_projection"
    if not scenario.get("solved"):
        return f"proxy_goal_unsolved:{scenario.get('final_reason') or 'unknown'}"
    if not scenario.get("branch_rank_top_match"):
        return "branch_rank_top_mismatch"
    if source_outcome_tested and not source_outcome_aligned:
        return "source_expected_outcome_mismatch"
    return "passed_proxy_gate"


def map_reachability(rows: list[str]) -> dict[str, Any]:
    starts = []
    goals = set()
    blocked = set()
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell == "A":
                starts.append((x, y))
            elif cell == "G":
                goals.add((x, y))
            elif cell in {"#", "H", "O"}:
                blocked.add((x, y))
    if len(starts) != 1 or not goals:
        return {"goal_reachable_avoiding_hazard": False, "shortest_safe_path_steps": None}
    start = starts[0]
    queue = [(start, 0)]
    seen = {start}
    while queue:
        (x, y), distance = queue.pop(0)
        if (x, y) in goals:
            return {"goal_reachable_avoiding_hazard": True, "shortest_safe_path_steps": distance}
        for dx, dy in ((1, 0), (0, 1), (0, -1), (-1, 0)):
            candidate = (x + dx, y + dy)
            cx, cy = candidate
            if cy < 0 or cy >= len(rows) or cx < 0 or cx >= len(rows[cy]):
                continue
            if candidate in seen or candidate in blocked:
                continue
            seen.add(candidate)
            queue.append((candidate, distance + 1))
    return {"goal_reachable_avoiding_hazard": False, "shortest_safe_path_steps": None}


def branch_rank_diagnostic(sequence: dict[str, Any]) -> dict[str, Any]:
    branches = sequence.get("branch_matrix") or []
    ranked = sorted(branches, key=lambda row: float(row.get("chrono_y_net") or 0.0), reverse=True)
    top = ranked[0] if ranked else {}
    terminal_branch_id = None
    for frame in sequence.get("frames") or []:
        outcome = frame.get("outcome") or {}
        if float(outcome.get("reward") or 0.0) > 0.0:
            terminal_branch_id = outcome.get("branch_id")
            break
    terminal_branch = None
    terminal_rank = None
    if terminal_branch_id is not None:
        for index, branch in enumerate(ranked, start=1):
            if branch.get("branch_id") == terminal_branch_id:
                terminal_branch = branch
                terminal_rank = index
                break
    top_score = top.get("chrono_y_net")
    terminal_score = None if terminal_branch is None else terminal_branch.get("chrono_y_net")
    gap = None
    if top_score is not None and terminal_score is not None:
        gap = float(top_score) - float(terminal_score)
    return {
        "terminal_positive_branch_id": terminal_branch_id,
        "terminal_positive_branch_rank": terminal_rank,
        "terminal_positive_branch_chrono_y_net": terminal_score,
        "top_branch_id": top.get("branch_id"),
        "top_branch_chrono_y_net": top_score,
        "branch_rank_gap_to_top": gap,
    }


def _ray_network_counts(sequence: dict[str, Any]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for frame in sequence.get("frames") or []:
        for ray in frame.get("rays") or []:
            counter[str(ray.get("network") or "unknown")] += 1
    return dict(sorted(counter.items()))


def _ray_contacts_have_ids(sequence: dict[str, Any]) -> bool:
    for frame in sequence.get("frames") or []:
        for ray in frame.get("rays") or []:
            contact = ray.get("contact") or {}
            if not contact.get("object_id") or not contact.get("category_id"):
                return False
    return True


def _case_id(challenge: dict[str, Any]) -> str:
    suffix = str(challenge["challenge_id"]).split(":")[-1]
    safe_suffix = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in suffix)
    return f"{int(challenge['curriculum_index']):04d}_{safe_suffix}"


def _condition(
    args: argparse.Namespace,
    out_dir: Path,
    curriculum_path: Path,
    challenges: list[dict[str, Any]],
    build_command: list[str],
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    command_template = [
        _rel(KERNEL_BIN),
        "solve-map",
        "--map",
        "<map_path>",
        "--sequence-out",
        "<sequence_path>",
        "--summary-out",
        "<summary_path>",
        "--name",
        "<challenge_id>",
        "--max-steps",
        str(args.max_steps),
        "--expected-reward",
        "1.0",
    ]
    return {
        "run_label": args.run_label,
        "run_kind": "deterministic_arc_dream_curriculum_proxy_eval_no_training",
        "run_label_semantics": "scout_curriculum_proxy_eval",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": EVAL_SCHEMA,
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "kernel_manifest": _rel(KERNEL_MANIFEST),
        "kernel_manifest_sha256": _sha256(KERNEL_MANIFEST),
        "kernel_main": _rel(KERNEL_MAIN),
        "kernel_main_sha256": _sha256(KERNEL_MAIN),
        "kernel_lib": _rel(KERNEL_LIB),
        "kernel_lib_sha256": _sha256(KERNEL_LIB),
        "kernel_build_command": build_command,
        "kernel_command_template": command_template,
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "curriculum_path": _rel(curriculum_path),
        "curriculum_sha256": _sha256(curriculum_path),
        "challenge_count": len(challenges),
        "max_challenges": args.max_challenges,
        "max_steps": args.max_steps,
        "arc_data_used": True,
        "training_data_promoted": False,
        "quarantine_status_required": "control_source: arc_scaffold_non_chronometric",
        "dataset_path": _rel(curriculum_path),
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_deterministic_greedy_planner",
        "gpu_count": 0,
        "world_size": 1,
        "loader_mode": "jsonl_arc_dream_curriculum_proxy_maps",
        "loader_settings": {
            "candidate_actions": ["east", "south", "north", "west", "wait"],
            "ray_directions": "compass_8",
            "max_ray_range": 16,
            "single_map_cli": "dream-kernel solve-map",
        },
        "quantization_policy": "none",
        "compile_kernel_policy": "cargo_dev_profile",
        "metric_to_compare": "proxy_goal_solve_rate_and_planner_integrity_by_tier",
        "historical_comparator": "none_first_arc_dream_curriculum_eval",
        "historical_comparator_artifact": None,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    overall = metrics["aggregate"]["overall"]
    lines = [
        "# ARC Dream Curriculum Eval V001 Results",
        "",
        "Status: deterministic Dream Kernel proxy curriculum eval. No training data promoted.",
        "",
        "This is not an ARC solve claim. It tests projected known-map simulation, ray/object integrity, branch ranking, and Nemo relay availability.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- curriculum: `{condition['curriculum_path']}`",
        f"- challenges: `{condition['challenge_count']}`",
        f"- max steps: `{condition['max_steps']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Overall",
        "",
        f"- proxy goal solved: `{overall['proxy_goal_solved']}/{overall['challenge_count']}`",
        f"- proxy goal solve rate: `{overall['proxy_goal_solve_rate']:.6f}`",
        f"- proxy goal reachable avoiding hazard: `{overall['proxy_goal_reachable_avoiding_hazard']}/{overall['challenge_count']}`",
        f"- planner integrity pass rate: `{overall['planner_integrity_pass_rate']:.6f}`",
        f"- invariant pass rate: `{overall['invariant_pass_rate']:.6f}`",
        f"- object identity pass rate: `{overall['object_identity_pass_rate']:.6f}`",
        f"- branch-rank top-match rate: `{overall['branch_rank_top_match_rate']:.6f}`",
        f"- terminal branch rank counts: `{overall['terminal_branch_rank_counts']}`",
        f"- accepted step rate: `{overall['accepted_step_rate']:.6f}`",
        f"- Nemo callback policy required: `{overall['nemo_policy_callback_required']}`",
        f"- kernel Nemo relay required: `{overall['kernel_nemo_relay_required']}`",
        "",
        "## By Tier",
        "",
        "| tier | count | reachable | solve rate | planner pass | branch top match | rejected steps | Nemo policy required |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for tier, row in metrics["aggregate"]["by_tier"].items():
        lines.append(
            "| {tier} | {count} | {reachable:.6f} | {solve:.6f} | {planner:.6f} | {branch:.6f} | {rejected} | {nemo} |".format(
                tier=tier,
                count=row["challenge_count"],
                reachable=row["proxy_goal_reachable_avoiding_hazard_rate"],
                solve=row["proxy_goal_solve_rate"],
                planner=row["planner_integrity_pass_rate"],
                branch=row["branch_rank_top_match_rate"],
                rejected=row["rejected_steps"],
                nemo=row["nemo_policy_callback_required"],
            )
        )
    lines.extend(
        [
            "",
            "## Failure Reasons",
            "",
            f"`{metrics['aggregate']['failure_reasons']}`",
            "",
            "## Ray Networks",
            "",
            f"`{metrics['aggregate']['ray_network_totals']}`",
            "",
            "## Interpretation",
            "",
            "- `proxy_goal_solve_rate` means the Dream Kernel solved the projected map, not the source ARC task.",
            "- `proxy_goal_reachable_avoiding_hazard` is a map-integrity preflight that treats walls, hazards, and objects as blockers.",
            "- `planner_integrity_pass_rate` requires solve, invariant integrity, ubiquitous object IDs, and branch-rank top-match.",
            "- Nemo remains a relay: callback needs are recorded, but the deterministic kernel action sequence is the evaluated driver.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_dream_curriculum_eval_v001_v017_support_scout")
    parser.add_argument("--max-challenges", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    overall = metrics["aggregate"]["overall"]
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "row_count": metrics["row_count"],
                "proxy_goal_solve_rate": overall["proxy_goal_solve_rate"],
                "planner_integrity_pass_rate": overall["planner_integrity_pass_rate"],
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
