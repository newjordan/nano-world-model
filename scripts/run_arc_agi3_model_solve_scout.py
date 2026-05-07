#!/usr/bin/env python3
"""Run a bounded ARC-AGI-3 offline solve scout through the standard model flow.

This is the first repeated-action test of the connected loop. Every actuator
step must be preceded by a fresh ModelDecision artifact from the Nemo3/world
model path:

observation -> 3D/world state -> chronometric game knowledge -> MLP
consultation -> branch simulation -> trust checks -> internal-thinking lock ->
Nemo3 final confirmation -> ModelDecision -> actuator step -> post-action MLP
update candidate.

The runner keeps one local/offline environment instance alive. It never submits
online, never mutates MLP weights, and records local solve detection separately
from official ARC solve claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_agi3_model_flow import (  # noqa: E402
    MODEL_DECISION_SCHEMA,
    STANDARD_MODEL_FLOW,
    ModelDecisionError,
    actuator_reasoning_from_model_decision,
    load_model_decision,
    require_standard_model_decision,
)
from scripts import run_arc_agi3_model_decision_producer as producer  # noqa: E402
from scripts import run_arc_agi3_model_step as model_step  # noqa: E402
from scripts.run_arc_agi3_io_smoke import (  # noqa: E402
    DEFAULT_ARC_REPO,
    DEFAULT_ENVIRONMENTS_DIR,
    DEFAULT_SOURCE_CONDITION,
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


DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_agi3_model_solve_scout_v054_ls20_live_nemo3_mlp_loop"
SCHEMA = "arc_agi3.model_solve_scout.v001"
TRACE_SCHEMA = "arc_agi3.model_solve_scout_trace_row.v001"
TERMINAL_STATES = {"WIN", "GAME_OVER", "DONE", "COMPLETED", "FAILED", "LOST"}


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    out_dir = args.out_dir.resolve()
    prepare_out_dir(out_dir)
    arc_repo = args.arc_repo.resolve()
    environments_dir = args.environments_dir.resolve()
    source_condition = args.source_condition_artifact.resolve()
    if not source_condition.exists():
        raise FileNotFoundError(source_condition)
    if not environments_dir.exists():
        raise FileNotFoundError(environments_dir)

    Arcade, OperationMode = load_arcade()
    operation_mode = getattr(OperationMode, args.operation_mode)
    arcade = Arcade(operation_mode=operation_mode, environments_dir=str(environments_dir))
    games = normalize_games(arcade.get_environments())
    selected_game = select_game(games, args.game)
    env = arcade.make(selected_game["name"])
    obs = env.reset()
    if obs is None:
        raise RuntimeError(f"{selected_game['name']} reset returned None")

    steps_dir = out_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    condition = condition_payload(
        args,
        out_dir=out_dir,
        arc_repo=arc_repo,
        environments_dir=environments_dir,
        source_condition=source_condition,
        selected_game=selected_game,
        arcade=arcade,
    )

    prior_update_refs: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    all_candidate_packets: list[dict[str, Any]] = []
    final_obs = obs
    stop_reason = "max_steps_exhausted"

    for step_index in range(args.max_steps):
        if offline_solved(obs):
            stop_reason = "offline_solved_before_step"
            break
        if terminal_state(obs):
            stop_reason = f"terminal_state_before_step:{state_name(getattr(obs, 'state', None))}"
            break

        step_label = f"{args.run_label}_step_{step_index:03d}"
        decision_dir = steps_dir / f"{step_index:03d}_model_decision"
        actuator_dir = steps_dir / f"{step_index:03d}_actuator_step"
        prepare_out_dir(decision_dir)
        prepare_out_dir(actuator_dir)

        candidate_packets = candidate_action_packets(
            env=env,
            game_name=selected_game["name"],
            observation_guid=str(getattr(obs, "guid", "")),
            phase=f"solve_scout_step_{step_index}_pre_action",
            max_actions=args.max_candidate_actions,
            packet_offset=len(all_candidate_packets),
        )
        if not candidate_packets:
            stop_reason = "no_available_actions"
            break
        all_candidate_packets.extend(candidate_packets)

        decision_args = decision_args_for(args, run_label=f"{step_label}_decision")
        decision_condition = decision_condition_payload(
            args,
            decision_args=decision_args,
            out_dir=decision_dir,
            arc_repo=arc_repo,
            environments_dir=environments_dir,
            source_condition=source_condition,
            selected_game=selected_game,
            arcade=arcade,
            step_index=step_index,
            prior_update_refs=prior_update_refs,
        )
        decision_metrics = producer.write_model_decision_artifacts(
            args=decision_args,
            out_dir=decision_dir,
            games=games,
            selected_game=selected_game,
            env=env,
            reset_obs=obs,
            candidate_packets=candidate_packets,
            condition=decision_condition,
            prior_post_action_mlp_updates=prior_update_refs,
        )
        decision_path = decision_dir / "model_decision.json"
        model_decision = load_model_decision(decision_path)
        try:
            selected_action = require_standard_model_decision(
                model_decision,
                available_action_values=action_values(getattr(env, "action_space", [])),
                require_internal_solve=not args.allow_unsolved_internal_rollout_for_contract_test,
            )
        except ModelDecisionError as exc:
            stop_reason = "internal_solve_gate_blocked_before_actuator"
            (decision_dir / "actuator_gate_block.json").write_text(
                json.dumps(
                    {
                        "schema": "arc_agi3.actuator_gate_block.v001",
                        "created_at_utc": datetime.now(timezone.utc).isoformat(),
                        "state_id": model_decision.get("state_id"),
                        "decision_id": model_decision.get("decision_id"),
                        "require_internal_solve": (
                            not args.allow_unsolved_internal_rollout_for_contract_test
                        ),
                        "reason": str(exc),
                        "model_decision_artifact": _repo_rel(decision_path),
                        "actuator_steps_executed": len(trace_rows),
                        "arc_solve_claim": False,
                        "online_submission": False,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            break
        action = action_by_value(env.action_space, int(selected_action["action_value"]))
        action_data = selected_action.get("action_data")
        before_summary = summarize_frame_stack(getattr(obs, "frame", None))
        observation_match = model_step.require_observation_artifact_match(
            model_decision=model_decision,
            obs=obs,
            env=env,
            frame_summary=before_summary,
        )
        reasoning = actuator_reasoning_from_model_decision(model_decision)
        reasoning.update(
            {
                "run_label": args.run_label,
                "solve_scout_step_index": step_index,
                "prior_post_action_update_context_count": len(prior_update_refs),
            }
        )

        step_kwargs: dict[str, Any] = {"reasoning": reasoning}
        if action_data is not None:
            step_kwargs["data"] = action_data
        next_obs = env.step(action, **step_kwargs)
        if next_obs is None:
            raise RuntimeError(f"env.step returned None after {action_name(action)}")

        step_args = SimpleNamespace(
            run_label=f"{step_label}_actuator",
            post_action_mlp_update_mode=args.post_action_mlp_update_mode,
        )
        next_summary = summarize_frame_stack(getattr(next_obs, "frame", None))
        post_update_path = actuator_dir / "post_action_mlp_update.json"
        post_update = model_step.build_post_action_mlp_update_artifact(
            args=step_args,
            obs=obs,
            next_obs=next_obs,
            action=action,
            action_data=action_data,
            model_decision=model_decision,
            before_summary=before_summary,
            next_summary=next_summary,
        )
        post_update_path.write_text(json.dumps(post_update, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        post_update_ref = {
            "artifact": _repo_rel(post_update_path),
            "sha256": _sha256(post_update_path),
            "source_step_index": step_index,
            "update_mode": post_update["update_mode"],
            "mlp_weights_updated": post_update["mlp_weights_updated"],
            "training_data_promoted": post_update["training_data_promoted"],
        }
        step_trace_row = model_step.trace_row(
            args=step_args,
            env=env,
            game_name=selected_game["name"],
            obs=obs,
            next_obs=next_obs,
            action=action,
            action_data=action_data,
            model_decision=model_decision,
            before_summary=before_summary,
            next_summary=next_summary,
            observation_match=observation_match,
            post_action_mlp_update_ref=post_update_ref,
            post_action_mlp_update=post_update,
        )
        actuator_condition = actuator_condition_payload(
            args,
            step_args=step_args,
            out_dir=actuator_dir,
            arc_repo=arc_repo,
            environments_dir=environments_dir,
            source_condition=source_condition,
            decision_path=decision_path,
            selected_game=selected_game,
            arcade=arcade,
            step_index=step_index,
        )
        step_metrics = model_step.summarize_model_step(
            condition=actuator_condition,
            games=games,
            trace_rows=[step_trace_row],
            candidate_packets=candidate_packets,
            model_decision=model_decision,
        )
        write_actuator_artifacts(
            actuator_dir=actuator_dir,
            condition=actuator_condition,
            metrics=step_metrics,
            model_decision=model_decision,
            trace_row=step_trace_row,
            candidate_packets=candidate_packets,
        )

        loop_row = loop_trace_row(
            step_index=step_index,
            decision_dir=decision_dir,
            actuator_dir=actuator_dir,
            decision_metrics=decision_metrics,
            step_metrics=step_metrics,
            post_update_ref=post_update_ref,
            obs=obs,
            next_obs=next_obs,
        )
        trace_rows.append(loop_row)
        prior_update_refs.append(post_update_ref)
        final_obs = next_obs
        obs = next_obs

        if offline_solved(next_obs):
            stop_reason = "offline_solved_after_step"
            break
        if terminal_state(next_obs):
            stop_reason = f"terminal_state_after_step:{state_name(getattr(next_obs, 'state', None))}"
            break

    metrics = summarize_loop(
        condition=condition,
        games=games,
        trace_rows=trace_rows,
        candidate_packets=all_candidate_packets,
        initial_obs=final_obs if not trace_rows else None,
        final_obs=final_obs,
        stop_reason=stop_reason,
        prior_update_refs=prior_update_refs,
    )
    if trace_rows:
        first_row = trace_rows[0]
        metrics["levels_completed_start"] = first_row["levels_completed_start"]
        metrics["win_levels_start"] = first_row["win_levels_start"]
    else:
        metrics["levels_completed_start"] = int(getattr(final_obs, "levels_completed", 0))
        metrics["win_levels_start"] = int(getattr(final_obs, "win_levels", 0))

    _write_jsonl(out_dir / "model_solve_scout_trace.jsonl", trace_rows)
    _write_jsonl(out_dir / "candidate_action_packets.jsonl", all_candidate_packets)
    _write_jsonl(out_dir / "post_action_mlp_update_candidates.jsonl", prior_update_refs)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def write_actuator_artifacts(
    *,
    actuator_dir: Path,
    condition: dict[str, Any],
    metrics: dict[str, Any],
    model_decision: dict[str, Any],
    trace_row: dict[str, Any],
    candidate_packets: list[dict[str, Any]],
) -> None:
    (actuator_dir / "model_decision.json").write_text(
        json.dumps(model_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_jsonl(actuator_dir / "model_step_trace.jsonl", [trace_row])
    _write_jsonl(actuator_dir / "candidate_action_packets.jsonl", candidate_packets)
    (actuator_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (actuator_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (actuator_dir / "RESULTS.md").write_text(model_step.format_results(metrics), encoding="utf-8")


def loop_trace_row(
    *,
    step_index: int,
    decision_dir: Path,
    actuator_dir: Path,
    decision_metrics: dict[str, Any],
    step_metrics: dict[str, Any],
    post_update_ref: dict[str, Any],
    obs: Any,
    next_obs: Any,
) -> dict[str, Any]:
    return {
        "schema": TRACE_SCHEMA,
        "step_index": step_index,
        "decision_artifact": decision_metrics["model_decision_artifact"],
        "decision_dir": _repo_rel(decision_dir),
        "actuator_dir": _repo_rel(actuator_dir),
        "decision_id": decision_metrics["decision_id"],
        "valid_standard_model_decision": decision_metrics["valid_standard_model_decision"],
        "valid_standard_model_flow_step": step_metrics["valid_standard_model_flow_step"],
        "nemo3_external_model_invoked": decision_metrics["nemo3_external_model_invoked"],
        "selected_action": decision_metrics["selected_action"],
        "chosen_action": step_metrics["chosen_action"],
        "selected_action_source": decision_metrics["selected_action_source"],
        "mlp_consultation": decision_metrics["mlp_consultation"],
        "mlp_candidate_priors": decision_metrics["mlp_candidate_priors"],
        "mlp_post_action_update_context_count": decision_metrics["mlp_post_action_update_context_count"],
        "post_action_mlp_update_artifact": post_update_ref["artifact"],
        "post_action_mlp_update_sha256": post_update_ref["sha256"],
        "post_action_mlp_update_mode": post_update_ref["update_mode"],
        "mlp_weights_updated": post_update_ref["mlp_weights_updated"],
        "training_data_promoted": post_update_ref["training_data_promoted"],
        "levels_completed_start": int(getattr(obs, "levels_completed", 0)),
        "levels_completed_final": int(getattr(next_obs, "levels_completed", 0)),
        "level_delta": int(getattr(next_obs, "levels_completed", 0)) - int(getattr(obs, "levels_completed", 0)),
        "win_levels_start": int(getattr(obs, "win_levels", 0)),
        "win_levels_final": int(getattr(next_obs, "win_levels", 0)),
        "state_start": state_name(getattr(obs, "state", None)),
        "state_final": state_name(getattr(next_obs, "state", None)),
        "frame_changed": step_metrics["frame_changed"],
        "offline_solved_after_step": offline_solved(next_obs),
        "terminal_after_step": terminal_state(next_obs),
        "online_submission": False,
        "arc_solve_claim": False,
        "scorecard_submission": False,
    }


def summarize_loop(
    *,
    condition: dict[str, Any],
    games: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    candidate_packets: list[dict[str, Any]],
    initial_obs: Any | None,
    final_obs: Any,
    stop_reason: str,
    prior_update_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    final_levels = int(getattr(final_obs, "levels_completed", 0))
    final_win_levels = int(getattr(final_obs, "win_levels", 0))
    has_action_or_solved = bool(trace_rows) or offline_solved(final_obs)
    feedback_context_valid = all(
        int(row["step_index"]) == 0 or int(row["mlp_post_action_update_context_count"]) > 0
        for row in trace_rows
    )
    nemo_required_external = bool(condition.get("nemo_external_model_required"))
    nemo_confirmation_valid = (
        all(row["nemo3_external_model_invoked"] is True for row in trace_rows)
        if nemo_required_external
        else all("nemo3_external_model_invoked" in row for row in trace_rows)
    )
    valid_steps = bool(
        all(row["valid_standard_model_decision"] is True for row in trace_rows)
        and all(row["valid_standard_model_flow_step"] is True for row in trace_rows)
        and nemo_confirmation_valid
        and all(row["mlp_weights_updated"] is False for row in trace_rows)
        and all(row["training_data_promoted"] is False for row in trace_rows)
    )
    return {
        "schema": SCHEMA,
        "condition": condition,
        "available_game_count": len(games),
        "selected_game": condition["selected_game"],
        "valid_model_solve_scout": bool(
            has_action_or_solved
            and valid_steps
            and feedback_context_valid
            and not condition["online_submission"]
            and not condition["scorecard_submission"]
            and not condition["training_data_promoted"]
        ),
        "offline_solve_detected": offline_solved(final_obs),
        "official_arc_solve_claim": False,
        "stop_reason": stop_reason,
        "model_decisions": len(trace_rows),
        "actuator_steps_executed": len(trace_rows),
        "candidate_action_packets": len(candidate_packets),
        "post_action_mlp_update_candidates": len(prior_update_refs),
        "feedback_context_valid": feedback_context_valid,
        "final_state": state_name(getattr(final_obs, "state", None)),
        "levels_completed_final": final_levels,
        "win_levels_final": final_win_levels,
        "levels_completed_delta": (
            0
            if not trace_rows
            else final_levels - int(trace_rows[0]["levels_completed_start"])
        ),
        "selected_actions": [row["selected_action"] for row in trace_rows],
        "changed_frame_steps": sum(1 for row in trace_rows if row["frame_changed"] is True),
        "nemo3_external_model_invocations": sum(1 for row in trace_rows if row["nemo3_external_model_invoked"] is True),
        "nemo3_confirmation_valid": nemo_confirmation_valid,
        "nemo3_external_model_required": nemo_required_external,
        "mlp_weights_updated": False,
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
        "run_kind": "arc_agi3_model_solve_scout",
        "run_label_semantics": "new_experiment_offline_solve_scout_standard_model_loop",
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
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "nemo_mode": args.nemo_mode,
        "nemo_external_model_required": args.nemo_mode == producer.LIVE_NEMO_MODE,
        "nemo_relay_url": args.nemo_relay_url if args.nemo_mode == producer.LIVE_NEMO_MODE else None,
        "nemo_model": args.nemo_model,
        "max_steps": args.max_steps,
        "post_action_mlp_update_mode": args.post_action_mlp_update_mode,
        "allow_unsolved_internal_rollout_for_contract_test": args.allow_unsolved_internal_rollout_for_contract_test,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "deterministic_from_observation_frame_sha_action_values_and_candidate_update_context",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": f"max_steps={args.max_steps}",
        "loader_mode": "arc_agi_offline_local_environment_standard_model_loop",
        "loader_settings": {
            "operation_mode": args.operation_mode,
            "game": args.game,
            "max_candidate_actions": args.max_candidate_actions,
            "max_steps": args.max_steps,
            "branch_ambiguity_gap_threshold": args.branch_ambiguity_gap_threshold,
            "internal_rollout_max_steps": args.internal_rollout_max_steps,
            "arc_grid_agent_label": args.arc_grid_agent_label,
            "arc_grid_goal_label": args.arc_grid_goal_label,
            "arc_grid_wall_labels": args.arc_grid_wall_labels,
            "arc_grid_hazard_labels": args.arc_grid_hazard_labels,
            "allow_unsolved_internal_rollout_for_contract_test": (
                args.allow_unsolved_internal_rollout_for_contract_test
            ),
            "post_action_mlp_update_mode": args.post_action_mlp_update_mode,
            "online_submission": False,
            "scorecard_submission": False,
        },
        "metric_to_compare": "arc_agi3_offline_solve_detected_and_standard_model_loop_validity",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "mandatory_dream_kernel_arc_grid_scout_before_actuator",
        "arc_data_used": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def decision_condition_payload(
    args: argparse.Namespace,
    *,
    decision_args: argparse.Namespace,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    selected_game: dict[str, Any],
    arcade: Any,
    step_index: int,
    prior_update_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": producer.SCHEMA,
        "run_label": decision_args.run_label,
        "run_kind": "arc_agi3_model_solve_scout_decision_step",
        "parent_run_label": args.run_label,
        "step_index": step_index,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _repo_rel(Path(__file__).resolve()),
        "script_sha256": _sha256(Path(__file__).resolve()),
        "producer_module": _repo_rel(Path(producer.__file__).resolve()),
        "producer_module_sha256": _sha256(Path(producer.__file__).resolve()),
        "git_commit": _git(ROOT, ["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ROOT, ignored_paths=[out_dir.parents[1]]),
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
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "nemo_mode": args.nemo_mode,
        "nemo_external_model_required": args.nemo_mode == producer.LIVE_NEMO_MODE,
        "nemo_relay_url": args.nemo_relay_url if args.nemo_mode == producer.LIVE_NEMO_MODE else None,
        "nemo_model": args.nemo_model,
        "actuator_step_count": 0,
        "prior_post_action_update_context_count": len(prior_update_refs),
        "prior_post_action_update_candidates": prior_update_refs,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "deterministic_from_current_frame_sha_action_values_and_candidate_update_context",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": f"parent_max_steps={args.max_steps}",
        "loader_mode": "arc_agi_offline_local_environment_current_observation_decision_step",
        "loader_settings": {
            "operation_mode": args.operation_mode,
            "game": args.game,
            "max_candidate_actions": args.max_candidate_actions,
            "branch_ambiguity_gap_threshold": args.branch_ambiguity_gap_threshold,
            "internal_rollout_max_steps": args.internal_rollout_max_steps,
            "arc_grid_agent_label": args.arc_grid_agent_label,
            "arc_grid_goal_label": args.arc_grid_goal_label,
            "arc_grid_wall_labels": args.arc_grid_wall_labels,
            "arc_grid_hazard_labels": args.arc_grid_hazard_labels,
            "online_submission": False,
            "scorecard_submission": False,
        },
        "metric_to_compare": "arc_agi3_valid_model_decision_artifact_and_zero_actuator_steps",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "mandatory_dream_kernel_arc_grid_scout_before_actuator",
        "arc_data_used": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def actuator_condition_payload(
    args: argparse.Namespace,
    *,
    step_args: argparse.Namespace,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    decision_path: Path,
    selected_game: dict[str, Any],
    arcade: Any,
    step_index: int,
) -> dict[str, Any]:
    return {
        "schema": model_step.SCHEMA,
        "run_label": step_args.run_label,
        "run_kind": "arc_agi3_model_solve_scout_actuator_step",
        "parent_run_label": args.run_label,
        "step_index": step_index,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _repo_rel(Path(__file__).resolve()),
        "script_sha256": _sha256(Path(__file__).resolve()),
        "actuator_module": _repo_rel(Path(model_step.__file__).resolve()),
        "actuator_module_sha256": _sha256(Path(model_step.__file__).resolve()),
        "git_commit": _git(ROOT, ["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ROOT, ignored_paths=[out_dir.parents[1]]),
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
        "model_decision_artifact": _repo_rel(decision_path),
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "actuator_step_count": 1,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "model_decision_artifact_defined",
        "gpu_count": 0,
        "world_size": 1,
        "loader_mode": "arc_agi_offline_local_environment_wrapper_as_actuator",
        "post_action_mlp_update_mode": args.post_action_mlp_update_mode,
        "metric_to_compare": "arc_agi3_standard_model_flow_validity_and_one_step_trace",
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def decision_args_for(args: argparse.Namespace, *, run_label: str) -> argparse.Namespace:
    return SimpleNamespace(
        run_label=run_label,
        branch_ambiguity_gap_threshold=args.branch_ambiguity_gap_threshold,
        nemo_mode=args.nemo_mode,
        nemo_model=args.nemo_model,
        nemo_relay_url=args.nemo_relay_url,
        nemo_timeout=args.nemo_timeout,
        internal_rollout_max_steps=args.internal_rollout_max_steps,
        internal_rollout_kernel_timeout=args.internal_rollout_kernel_timeout,
        arc_grid_agent_label=args.arc_grid_agent_label,
        arc_grid_goal_label=args.arc_grid_goal_label,
        arc_grid_wall_labels=args.arc_grid_wall_labels,
        arc_grid_hazard_labels=args.arc_grid_hazard_labels,
    )


def offline_solved(obs: Any) -> bool:
    state = state_name(getattr(obs, "state", None)).upper()
    levels_completed = int(getattr(obs, "levels_completed", 0))
    win_levels = int(getattr(obs, "win_levels", 0))
    return state == "WIN" or (win_levels > 0 and levels_completed >= win_levels)


def terminal_state(obs: Any) -> bool:
    return state_name(getattr(obs, "state", None)).upper() in TERMINAL_STATES


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC-AGI-3 Model Solve Scout Results",
        "",
        "Status: bounded local/offline solve scout through the standard ModelDecision loop.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- selected game: `{condition['selected_game']['game_id']}`",
        f"- operation mode: `{condition['operation_mode']}`",
        f"- Nemo mode: `{condition['nemo_mode']}`",
        f"- max steps: `{condition['max_steps']}`",
        f"- online submission: `{condition['online_submission']}`",
        f"- official ARC solve claim: `{metrics['official_arc_solve_claim']}`",
        "",
        "## Metrics",
        "",
        f"- valid model solve scout: `{metrics['valid_model_solve_scout']}`",
        f"- offline solve detected: `{metrics['offline_solve_detected']}`",
        f"- stop reason: `{metrics['stop_reason']}`",
        f"- model decisions: `{metrics['model_decisions']}`",
        f"- actuator steps executed: `{metrics['actuator_steps_executed']}`",
        f"- post-action MLP update candidates: `{metrics['post_action_mlp_update_candidates']}`",
        f"- feedback context valid: `{metrics['feedback_context_valid']}`",
        f"- levels completed: `{metrics.get('levels_completed_start')} -> {metrics['levels_completed_final']}`",
        f"- win levels final: `{metrics['win_levels_final']}`",
        f"- final state: `{metrics['final_state']}`",
        f"- selected actions: `{metrics['selected_actions']}`",
        f"- MLP weights updated: `{metrics['mlp_weights_updated']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_agi3_model_solve_scout_v054_ls20_live_nemo3_mlp_loop")
    parser.add_argument("--operation-mode", choices=("OFFLINE",), default="OFFLINE")
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--branch-ambiguity-gap-threshold", type=float, default=0.0)
    parser.add_argument("--internal-rollout-max-steps", type=int, default=32)
    parser.add_argument("--internal-rollout-kernel-timeout", type=int, default=30)
    parser.add_argument("--arc-grid-agent-label", type=int, default=None)
    parser.add_argument("--arc-grid-goal-label", type=int, default=None)
    parser.add_argument("--arc-grid-wall-labels", default="")
    parser.add_argument("--arc-grid-hazard-labels", default="")
    parser.add_argument("--allow-unsolved-internal-rollout-for-contract-test", action="store_true")
    parser.add_argument("--nemo-mode", choices=(producer.LOCAL_NEMO_MODE, producer.LIVE_NEMO_MODE), default=producer.LIVE_NEMO_MODE)
    parser.add_argument("--nemo-relay-url", default="http://127.0.0.1:8000/v1/responses")
    parser.add_argument("--nemo-model", default="nemotron_3_nano_omni")
    parser.add_argument("--nemo-timeout", type=int, default=180)
    parser.add_argument("--post-action-mlp-update-mode", choices=("candidate-only",), default="candidate-only")
    parser.add_argument("--historical-comparator", default="v052_v053_single_step_connected_standard")
    parser.add_argument("--historical-comparator-artifact", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "valid_model_solve_scout": metrics["valid_model_solve_scout"],
                "offline_solve_detected": metrics["offline_solve_detected"],
                "stop_reason": metrics["stop_reason"],
                "actuator_steps_executed": metrics["actuator_steps_executed"],
                "levels_completed_final": metrics["levels_completed_final"],
                "win_levels_final": metrics["win_levels_final"],
                "selected_actions": metrics["selected_actions"],
                "out_dir": _repo_rel(args.out_dir.resolve()),
                "online_submission": metrics["online_submission"],
                "arc_solve_claim": metrics["arc_solve_claim"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
