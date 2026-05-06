#!/usr/bin/env python3
"""Run a guarded ARC-AGI-3 actuator-only smoke.

This consumes the same local/offline ARC-AGI-3 environment surface as the V041
I/O smoke, but it is not the Nemo3/world-model flow and must not be used as a
model attempt. The standard model path is observation -> 3D/world state ->
branch simulation -> trust checks -> model decision -> actuator step.

This script is guarded so it can only be used as an explicit one-step actuator
plumbing smoke. It is not an online submission and not an ARC solve claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_arc_agi3_io_smoke import (  # noqa: E402
    _git,
    _git_dirty,
    _rel,
    _repo_rel,
    _sha256,
    _write_jsonl,
    action_by_value,
    action_name,
    action_value,
    action_values,
    candidate_action_packets,
    load_arcade,
    normalize_games,
    package_version,
    prepare_out_dir,
    select_game,
    state_name,
    summarize_frame_stack,
)


DEFAULT_ARC_REPO = Path("/home/frosty40/world_model_1")
DEFAULT_ENVIRONMENTS_DIR = DEFAULT_ARC_REPO / "environment_files"
DEFAULT_SOURCE_CONDITION = DEFAULT_ARC_REPO / "docs" / "arc-agi-3-env.md"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_agi3_closed_loop_v042_ls20_repeat_capped_cycle"
SCHEMA = "arc_agi3.closed_loop_smoke.v001"
TRACE_SCHEMA = "arc_agi3.closed_loop_trace_row.v001"
TERMINAL_STATES = {"WIN", "GAME_OVER"}
MODEL_FLOW_ERROR = (
    "refusing actuator-only ARC rollout: this script does not invoke the Nemo3/world-model "
    "flow, 3D geometry, ray gates, temporal simulation, or ModelDecision path"
)


@dataclass(frozen=True)
class RepeatCappedCycleState:
    cursor: int = 0
    last_action_value: int | None = None
    repeat_run: int = 0
    previous_frame_changed: bool = True


def choose_repeat_capped_cycle_action(
    available_action_values: list[int],
    state: RepeatCappedCycleState,
    *,
    max_repeat: int,
) -> tuple[int, dict[str, Any]]:
    values = sorted(int(value) for value in available_action_values)
    if not values:
        raise RuntimeError("environment exposed no available actions")
    if max_repeat < 1:
        raise ValueError("max_repeat must be at least 1")

    can_repeat = (
        state.last_action_value in values
        and state.previous_frame_changed
        and state.repeat_run < max_repeat
    )
    if can_repeat:
        chosen = int(state.last_action_value)
        reason = "repeat_after_changed_frame"
    else:
        cursor = state.cursor % len(values)
        chosen = values[cursor]
        if chosen == state.last_action_value and len(values) > 1:
            cursor = (cursor + 1) % len(values)
            chosen = values[cursor]
        reason = "initial_cycle" if state.last_action_value is None else "cycle_after_stasis_or_cap"

    return chosen, {
        "policy": "repeat_capped_cycle",
        "reason": reason,
        "max_repeat": max_repeat,
        "prior_state": asdict(state),
        "available_action_values": values,
    }


def update_repeat_capped_cycle_state(
    state: RepeatCappedCycleState,
    *,
    chosen_action_value: int,
    available_action_values: list[int],
    frame_changed: bool,
    max_repeat: int,
) -> RepeatCappedCycleState:
    values = sorted(int(value) for value in available_action_values)
    if chosen_action_value not in values:
        raise ValueError(f"chosen action {chosen_action_value} is not in the available action set")
    repeat_run = state.repeat_run + 1 if chosen_action_value == state.last_action_value else 1
    index = values.index(chosen_action_value)
    cursor = index if frame_changed and repeat_run < max_repeat else (index + 1) % len(values)
    return RepeatCappedCycleState(
        cursor=cursor,
        last_action_value=chosen_action_value,
        repeat_run=repeat_run,
        previous_frame_changed=frame_changed,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    validate_actuator_only_scope(args)
    out_dir = args.out_dir.resolve()
    prepare_out_dir(out_dir)
    arc_repo = args.arc_repo.resolve()
    environments_dir = args.environments_dir.resolve()
    source_condition = args.source_condition_artifact.resolve()
    if not source_condition.exists():
        raise FileNotFoundError(source_condition)
    if not environments_dir.exists():
        raise FileNotFoundError(environments_dir)
    if args.max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    Arcade, OperationMode = load_arcade()
    operation_mode = getattr(OperationMode, args.operation_mode)
    arcade = Arcade(operation_mode=operation_mode, environments_dir=str(environments_dir))
    games = normalize_games(arcade.get_environments())
    selected_game = select_game(games, args.game)
    env = arcade.make(selected_game["name"])
    obs = env.reset()
    if obs is None:
        raise RuntimeError(f"{selected_game['name']} reset returned None")

    trace_rows: list[dict[str, Any]] = []
    all_candidate_packets: list[dict[str, Any]] = []
    policy_state = RepeatCappedCycleState()
    executed_steps = 0
    final_obs = obs

    for step_index in range(args.max_steps):
        current_state = state_name(getattr(obs, "state", None))
        if current_state in TERMINAL_STATES:
            break

        packets = candidate_action_packets(
            env=env,
            game_name=selected_game["name"],
            observation_guid=str(getattr(obs, "guid", "")),
            phase=f"closed_loop_step_{step_index}",
            max_actions=args.max_candidate_actions,
            packet_offset=len(all_candidate_packets),
        )
        all_candidate_packets.extend(packets)
        available_values = action_values(getattr(env, "action_space", []))
        chosen_value, rationale = choose_repeat_capped_cycle_action(
            available_values,
            policy_state,
            max_repeat=args.max_repeat,
        )
        action = action_by_value(env.action_space, chosen_value)
        action_data = default_action_data(action)
        before_summary = summarize_frame_stack(getattr(obs, "frame", None))

        step_kwargs: dict[str, Any] = {
            "reasoning": {
                "run_label": args.run_label,
                "policy": args.policy,
                "policy_rationale": rationale,
                "step_index": step_index,
                "submit_online": False,
                "scorecard_submission": False,
                "arc_solve_claim": False,
            }
        }
        if action_data is not None:
            step_kwargs["data"] = action_data
        next_obs = env.step(action, **step_kwargs)
        executed_steps += 1
        if next_obs is None:
            raise RuntimeError(f"env.step returned None after {action_name(action)}")

        next_summary = summarize_frame_stack(getattr(next_obs, "frame", None))
        frame_changed = before_summary["latest_frame_sha256"] != next_summary["latest_frame_sha256"]
        row = trace_row(
            args=args,
            env=env,
            game_name=selected_game["name"],
            step_index=step_index,
            obs=obs,
            next_obs=next_obs,
            action=action,
            action_data=action_data,
            rationale=rationale,
            before_summary=before_summary,
            next_summary=next_summary,
            frame_changed=frame_changed,
        )
        trace_rows.append(row)
        policy_state = update_repeat_capped_cycle_state(
            policy_state,
            chosen_action_value=chosen_value,
            available_action_values=available_values,
            frame_changed=frame_changed,
            max_repeat=args.max_repeat,
        )
        final_obs = next_obs
        obs = next_obs

    condition = condition_payload(
        args,
        out_dir=out_dir,
        arc_repo=arc_repo,
        environments_dir=environments_dir,
        source_condition=source_condition,
        selected_game=selected_game,
        arcade=arcade,
    )
    metrics = summarize_closed_loop(
        condition=condition,
        games=games,
        trace_rows=trace_rows,
        candidate_packets=all_candidate_packets,
        executed_steps=executed_steps,
        final_obs=final_obs,
    )
    _write_jsonl(out_dir / "closed_loop_trace.jsonl", trace_rows)
    _write_jsonl(out_dir / "candidate_action_packets.jsonl", all_candidate_packets)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def validate_actuator_only_scope(args: argparse.Namespace) -> None:
    if not getattr(args, "allow_actuator_only", False):
        raise RuntimeError(f"{MODEL_FLOW_ERROR}; pass --allow-actuator-only only for explicit interface plumbing")
    if int(args.max_steps) != 1:
        raise RuntimeError(
            f"{MODEL_FLOW_ERROR}; actuator-only smoke is capped at one step, "
            "and multi-step ARC runs must enter through the standard model flow"
        )


def default_action_data(action: Any) -> dict[str, int] | None:
    is_complex = getattr(action, "is_complex", None)
    if callable(is_complex) and is_complex():
        return {"x": 32, "y": 32}
    return None


def trace_row(
    *,
    args: argparse.Namespace,
    env: Any,
    game_name: str,
    step_index: int,
    obs: Any,
    next_obs: Any,
    action: Any,
    action_data: dict[str, int] | None,
    rationale: dict[str, Any],
    before_summary: dict[str, Any],
    next_summary: dict[str, Any],
    frame_changed: bool,
) -> dict[str, Any]:
    levels_completed = int(getattr(obs, "levels_completed", 0))
    next_levels_completed = int(getattr(next_obs, "levels_completed", 0))
    return {
        "schema": TRACE_SCHEMA,
        "run_label": args.run_label,
        "game_name": game_name,
        "game_id": str(getattr(obs, "game_id", getattr(env.info, "game_id", ""))),
        "step_index": step_index,
        "observation_guid": str(getattr(obs, "guid", "")),
        "next_observation_guid": str(getattr(next_obs, "guid", "")),
        "state": state_name(getattr(obs, "state", None)),
        "next_state": state_name(getattr(next_obs, "state", None)),
        "levels_completed": levels_completed,
        "next_levels_completed": next_levels_completed,
        "level_delta": next_levels_completed - levels_completed,
        "win_levels": int(getattr(obs, "win_levels", 0)),
        "next_win_levels": int(getattr(next_obs, "win_levels", 0)),
        "available_action_values": action_values(getattr(env, "action_space", [])),
        "chosen_action_name": action_name(action),
        "chosen_action_value": action_value(action),
        "action_data": action_data,
        "policy": args.policy,
        "policy_rationale": rationale,
        "frame_stack_len": before_summary["frame_stack_len"],
        "frame_shape": before_summary["latest_frame_shape"],
        "frame_min": before_summary["latest_frame_min"],
        "frame_max": before_summary["latest_frame_max"],
        "frame_sha256": before_summary["latest_frame_sha256"],
        "next_frame_stack_len": next_summary["frame_stack_len"],
        "next_frame_shape": next_summary["latest_frame_shape"],
        "next_frame_min": next_summary["latest_frame_min"],
        "next_frame_max": next_summary["latest_frame_max"],
        "next_frame_sha256": next_summary["latest_frame_sha256"],
        "frame_changed": frame_changed,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def condition_payload(
    args: argparse.Namespace,
    *,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    selected_game: dict[str, Any],
    arcade: Any,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "run_label": args.run_label,
        "run_kind": "arc_agi3_actuator_interface_smoke_guarded",
        "run_label_semantics": "actuator_only_not_model_attempt",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _repo_rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(ROOT, ["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ROOT, ignored_paths=[out_dir]),
        "source_condition_artifact": _rel(arc_repo, source_condition),
        "source_condition_sha256": _sha256(source_condition),
        "source_repo_path": str(arc_repo),
        "source_repo_commit": _git(arc_repo, ["rev-parse", "HEAD"]),
        "source_repo_dirty": _git_dirty(arc_repo),
        "dataset_path": _rel(arc_repo, environments_dir),
        "environments_dir": str(environments_dir),
        "selected_game": selected_game,
        "operation_mode": args.operation_mode,
        "toolkit": "arc_agi.Arcade",
        "toolkit_versions": {
            "arc_agi": package_version("arc_agi"),
            "arcengine": package_version("arcengine"),
        },
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_deterministic_policy",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": f"max_steps={args.max_steps}",
        "loader_mode": "arc_agi_offline_local_environment_wrapper",
        "loader_settings": {
            "operation_mode": args.operation_mode,
            "game": args.game,
            "max_steps": args.max_steps,
            "max_candidate_actions": args.max_candidate_actions,
            "policy": args.policy,
            "max_repeat": args.max_repeat,
            "allow_actuator_only": args.allow_actuator_only,
            "online_submission": False,
            "scorecard_submission": False,
        },
        "metric_to_compare": "arc_agi3_offline_closed_loop_level_progress_and_trace_validity",
        "standard_model_flow_invoked": False,
        "nemo3_invoked": False,
        "chronometric_3d_geometry_invoked": False,
        "ray_gate_invoked": False,
        "temporal_simulation_invoked": False,
        "model_decision_artifact_required_for_real_rollout": True,
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "not_applicable_python_sdk_offline_policy",
        "arc_data_used": True,
        "valid_model_attempt": False,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def summarize_closed_loop(
    *,
    condition: dict[str, Any],
    games: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    candidate_packets: list[dict[str, Any]],
    executed_steps: int,
    final_obs: Any,
) -> dict[str, Any]:
    frame_shapes = sorted(
        {
            tuple(shape)
            for row in trace_rows
            for shape in (row["frame_shape"], row["next_frame_shape"])
            if shape
        }
    )
    available_action_counts = [len(row["available_action_values"]) for row in trace_rows]
    states = sorted({state for row in trace_rows for state in (row["state"], row["next_state"])})
    levels_seen = [row["levels_completed"] for row in trace_rows] + [row["next_levels_completed"] for row in trace_rows]
    win_levels_seen = [row["win_levels"] for row in trace_rows] + [row["next_win_levels"] for row in trace_rows]
    frame_hashes = {
        frame_hash
        for row in trace_rows
        for frame_hash in (row["frame_sha256"], row["next_frame_sha256"])
        if frame_hash
    }
    action_counts: dict[str, int] = {}
    for row in trace_rows:
        key = f"{row['chosen_action_name']}:{row['chosen_action_value']}"
        action_counts[key] = action_counts.get(key, 0) + 1

    levels_start = trace_rows[0]["levels_completed"] if trace_rows else int(getattr(final_obs, "levels_completed", 0))
    levels_final = int(getattr(final_obs, "levels_completed", 0))
    win_levels_final = int(getattr(final_obs, "win_levels", 0))
    final_state = state_name(getattr(final_obs, "state", None))
    local_environment_win = final_state == "WIN" or (win_levels_final > 0 and levels_final >= win_levels_final)
    valid = bool(
        executed_steps == len(trace_rows)
        and executed_steps > 0
        and candidate_packets
        and all(row["chosen_action_value"] in row["available_action_values"] for row in trace_rows)
        and all(shape == (64, 64) for shape in frame_shapes)
        and all(row["frame_min"] is None or 0 <= row["frame_min"] <= 15 for row in trace_rows)
        and all(row["next_frame_min"] is None or 0 <= row["next_frame_min"] <= 15 for row in trace_rows)
        and all(row["frame_max"] is None or 0 <= row["frame_max"] <= 15 for row in trace_rows)
        and all(row["next_frame_max"] is None or 0 <= row["next_frame_max"] <= 15 for row in trace_rows)
        and not condition["training_data_promoted"]
        and not condition["arc_solve_claim"]
        and not condition["online_submission"]
        and not condition["scorecard_submission"]
    )
    return {
        "schema": SCHEMA,
        "condition": condition,
        "available_game_count": len(games),
        "selected_game": condition["selected_game"],
        "policy": condition["loader_settings"]["policy"],
        "max_steps": condition["loader_settings"]["max_steps"],
        "max_repeat": condition["loader_settings"]["max_repeat"],
        "trace_rows": len(trace_rows),
        "candidate_action_packets": len(candidate_packets),
        "steps_executed": executed_steps,
        "frame_shapes": [list(shape) for shape in frame_shapes],
        "available_action_count_min": min(available_action_counts) if available_action_counts else 0,
        "available_action_count_max": max(available_action_counts) if available_action_counts else 0,
        "states_observed": states,
        "levels_completed_start": levels_start,
        "levels_completed_final": levels_final,
        "levels_completed_max": max(levels_seen, default=levels_final),
        "levels_completed_delta": levels_final - levels_start,
        "win_levels_final": win_levels_final,
        "win_levels_max": max(win_levels_seen, default=win_levels_final),
        "final_state": final_state,
        "terminal_state_reached": final_state in TERMINAL_STATES,
        "local_environment_win": local_environment_win,
        "unique_frame_hashes": len(frame_hashes),
        "changed_frame_steps": sum(1 for row in trace_rows if row["frame_changed"]),
        "no_change_steps": sum(1 for row in trace_rows if not row["frame_changed"]),
        "action_counts": dict(sorted(action_counts.items())),
        "valid_closed_loop_smoke": valid,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC-AGI-3 Closed-Loop V042 Results",
        "",
        "Status: explicit actuator-only ARC-AGI-3 plumbing smoke. This is not a model attempt. No online submission, no score claim, no training data promoted.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- source condition: `{condition['source_condition_artifact']}`",
        f"- environments dir: `{condition['dataset_path']}`",
        f"- operation mode: `{condition['operation_mode']}`",
        f"- selected game: `{condition['selected_game']['game_id']}`",
        f"- policy: `{metrics['policy']}`",
        f"- max steps: `{metrics['max_steps']}`",
        f"- standard model flow invoked: `{condition['standard_model_flow_invoked']}`",
        f"- Nemo3 invoked: `{condition['nemo3_invoked']}`",
        f"- 3D geometry invoked: `{condition['chronometric_3d_geometry_invoked']}`",
        f"- ray gate invoked: `{condition['ray_gate_invoked']}`",
        f"- valid model attempt: `{condition['valid_model_attempt']}`",
        f"- max repeat: `{metrics['max_repeat']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        f"- historical comparator: `{condition['historical_comparator']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        f"- ARC solve claim: `{condition['arc_solve_claim']}`",
        f"- online submission: `{condition['online_submission']}`",
        "",
        "## Metrics",
        "",
        f"- valid closed-loop smoke: `{metrics['valid_closed_loop_smoke']}`",
        f"- available games: `{metrics['available_game_count']}`",
        f"- trace rows: `{metrics['trace_rows']}`",
        f"- candidate action packets: `{metrics['candidate_action_packets']}`",
        f"- steps executed: `{metrics['steps_executed']}`",
        f"- frame shapes: `{metrics['frame_shapes']}`",
        f"- unique frame hashes: `{metrics['unique_frame_hashes']}`",
        f"- changed/no-change steps: `{metrics['changed_frame_steps']}/{metrics['no_change_steps']}`",
        f"- action count range: `{metrics['available_action_count_min']}..{metrics['available_action_count_max']}`",
        f"- action counts: `{metrics['action_counts']}`",
        f"- states observed: `{metrics['states_observed']}`",
        f"- levels completed: `{metrics['levels_completed_start']} -> {metrics['levels_completed_final']}`",
        f"- max levels completed: `{metrics['levels_completed_max']}`",
        f"- win levels: `{metrics['win_levels_final']}`",
        f"- final state: `{metrics['final_state']}`",
        f"- local environment win: `{metrics['local_environment_win']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_agi3_closed_loop_v042_ls20_repeat_capped_cycle")
    parser.add_argument("--operation-mode", choices=("OFFLINE",), default="OFFLINE")
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--policy", choices=("repeat_capped_cycle",), default="repeat_capped_cycle")
    parser.add_argument("--max-steps", type=int, default=1)
    parser.add_argument("--max-repeat", type=int, default=2)
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument(
        "--allow-actuator-only",
        action="store_true",
        help="Acknowledge this is a one-step actuator plumbing smoke, not the Nemo3/world-model flow.",
    )
    parser.add_argument("--historical-comparator", default="arc_agi3_io_v041_offline_smoke")
    parser.add_argument("--historical-comparator-artifact", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "valid_closed_loop_smoke": metrics["valid_closed_loop_smoke"],
                "selected_game": metrics["selected_game"],
                "policy": metrics["policy"],
                "steps_executed": metrics["steps_executed"],
                "levels_completed_final": metrics["levels_completed_final"],
                "levels_completed_delta": metrics["levels_completed_delta"],
                "win_levels_final": metrics["win_levels_final"],
                "final_state": metrics["final_state"],
                "local_environment_win": metrics["local_environment_win"],
                "out_dir": _repo_rel(args.out_dir.resolve()),
                "training_data_promoted": metrics["training_data_promoted"],
                "arc_solve_claim": metrics["arc_solve_claim"],
                "online_submission": metrics["online_submission"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
