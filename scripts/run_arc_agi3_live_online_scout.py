#!/usr/bin/env python3
"""Run a guarded ARC-AGI-3 online scout through the standard world-model loop.

This is the official-interaction boundary. It keeps an ONLINE/COMPETITION ARC
environment as the actuator and a local OFFLINE mirror as the source-world-model
dynamics surface. Every online action must pass the same ModelDecision contract
used by the offline solve scout before it is submitted.
"""

from __future__ import annotations

import argparse
import json
import os
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
from scripts.run_arc_agi3_model_solve_scout import offline_solved, terminal_state  # noqa: E402


DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_agi3_live_online_scout_v061_ls20_guarded"
DEFAULT_ARC_ENV_FILE = DEFAULT_ARC_REPO / ".env.arc"
DEFAULT_MODEL_NAME = "Dreamweaver"
SCHEMA = "arc_agi3.live_online_scout.v001"
TRACE_SCHEMA = "arc_agi3.live_online_scout_trace_row.v001"
FRAME_SCHEMA = "arc_agi3.live_online_frame.v001"
REPLAY_SCHEMA = "arc_agi3.compiled_live_replay.v001"
WATCH_SCHEMA = "arc_agi3.live_watch_snapshot.v001"


def run(args: argparse.Namespace) -> dict[str, Any]:
    loaded_env_keys = load_env_file(args.arc_env_file)
    args.arc_api_key_loaded_from_env_file = "ARC_API_KEY" in loaded_env_keys
    args.arc_api_key_source = arc_api_key_source(args, loaded_env_keys=loaded_env_keys)
    if not args.confirm_online_actions:
        raise RuntimeError("refusing to spend online ARC actions without --confirm-online-actions")
    if args.require_explicit_arc_api_key and not (args.arc_api_key or os.environ.get("ARC_API_KEY")):
        raise RuntimeError("refusing online run without explicit ARC_API_KEY; pass --allow-anonymous-api-key to override")
    if args.max_real_steps < 1:
        raise ValueError("max-real-steps must be at least 1")

    out_dir = args.out_dir.resolve()
    prepare_out_dir(out_dir)
    (out_dir / "steps").mkdir(parents=True, exist_ok=True)
    (out_dir / "watch").mkdir(parents=True, exist_ok=True)
    arc_repo = args.arc_repo.resolve()
    environments_dir = args.environments_dir.resolve()
    source_condition = args.source_condition_artifact.resolve()
    if not source_condition.exists():
        raise FileNotFoundError(source_condition)
    if not environments_dir.exists():
        raise FileNotFoundError(environments_dir)

    Arcade, OperationMode = load_arcade()
    operation_mode = getattr(OperationMode, args.operation_mode)
    mirror_mode = getattr(OperationMode, "OFFLINE")
    live_arcade = Arcade(
        arc_api_key=args.arc_api_key or os.environ.get("ARC_API_KEY", ""),
        operation_mode=operation_mode,
        environments_dir=str(environments_dir),
        recordings_dir=str(args.recordings_dir.resolve()),
    )
    mirror_arcade = Arcade(operation_mode=mirror_mode, environments_dir=str(environments_dir))

    games = normalize_games(live_arcade.get_environments())
    selected_game = select_game(games, args.game)
    scorecard_id = args.scorecard_id or create_scorecard(live_arcade, args=args)
    live_env = live_arcade.make(
        selected_game["name"],
        seed=args.seed,
        scorecard_id=scorecard_id,
        save_recording=args.save_recording,
        include_frame_data=True,
        render_mode=args.render_mode,
    )
    if live_env is None:
        raise RuntimeError(f"online Arcade.make({selected_game['name']!r}) returned None")
    mirror_env = mirror_arcade.make(selected_game["name"], seed=args.seed, include_frame_data=True)
    if mirror_env is None:
        raise RuntimeError(f"offline mirror Arcade.make({selected_game['name']!r}) returned None")

    live_obs = live_env.reset()
    mirror_obs = mirror_env.reset()
    if live_obs is None or mirror_obs is None:
        raise RuntimeError("live or mirror reset returned None")

    condition = condition_payload(
        args,
        out_dir=out_dir,
        arc_repo=arc_repo,
        environments_dir=environments_dir,
        source_condition=source_condition,
        selected_game=selected_game,
        live_arcade=live_arcade,
        mirror_arcade=mirror_arcade,
        scorecard_id=scorecard_id,
    )
    write_json(out_dir / "condition.json", condition)

    trace_rows: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = [
        frame_row(
            step_index=-1,
            phase="reset",
            obs=live_obs,
            mirror_obs=mirror_obs,
            action=None,
            action_data=None,
            env=live_env,
            selected_game=selected_game,
        )
    ]
    prior_update_refs: list[dict[str, Any]] = []
    all_candidate_packets: list[dict[str, Any]] = []
    stop_reason = "max_real_steps_exhausted"
    final_scorecard = None

    try:
        for step_index in range(args.max_real_steps):
            if offline_solved(live_obs):
                stop_reason = "online_solved_before_step"
                break
            if terminal_state(live_obs):
                stop_reason = f"terminal_state_before_step:{state_name(getattr(live_obs, 'state', None))}"
                break
            if not mirror_matches(live_obs, mirror_obs):
                stop_reason = "mirror_desync_before_step"
                break

            step_label = f"{args.run_label}_step_{step_index:03d}"
            decision_dir = out_dir / "steps" / f"{step_index:03d}_model_decision"
            actuator_dir = out_dir / "steps" / f"{step_index:03d}_online_actuator_step"
            prepare_out_dir(decision_dir)
            prepare_out_dir(actuator_dir)

            candidate_packets = candidate_action_packets(
                env=live_env,
                game_name=selected_game["name"],
                observation_guid=str(getattr(live_obs, "guid", "")),
                phase=f"live_online_step_{step_index}_pre_action",
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
                live_arcade=live_arcade,
                mirror_arcade=mirror_arcade,
                scorecard_id=scorecard_id,
                step_index=step_index,
                prior_update_refs=prior_update_refs,
            )
            decision_metrics = producer.write_model_decision_artifacts(
                args=decision_args,
                out_dir=decision_dir,
                games=games,
                selected_game=selected_game,
                env=mirror_env,
                reset_obs=live_obs,
                candidate_packets=candidate_packets,
                condition=decision_condition,
                prior_post_action_mlp_updates=prior_update_refs,
            )
            decision_path = decision_dir / "model_decision.json"
            model_decision = load_model_decision(decision_path)
            try:
                selected_action = require_standard_model_decision(
                    model_decision,
                    available_action_values=action_values(getattr(live_env, "action_space", [])),
                    require_internal_solve=True,
                )
            except ModelDecisionError as exc:
                stop_reason = "internal_solve_gate_blocked_before_online_action"
                write_json(
                    decision_dir / "online_actuator_gate_block.json",
                    {
                        "schema": "arc_agi3.online_actuator_gate_block.v001",
                        "created_at_utc": now_iso(),
                        "step_index": step_index,
                        "reason": str(exc),
                        "model_decision_artifact": _repo_rel(decision_path),
                        "online_actions_executed": len(trace_rows),
                        "scorecard_id": scorecard_id,
                    },
                )
                break

            action = action_by_value(live_env.action_space, int(selected_action["action_value"]))
            action_data = selected_action.get("action_data")
            before_summary = summarize_frame_stack(getattr(live_obs, "frame", None))
            observation_match = model_step.require_observation_artifact_match(
                model_decision=model_decision,
                obs=live_obs,
                env=live_env,
                frame_summary=before_summary,
            )
            reasoning = compact_live_reasoning(
                args=args,
                step_index=step_index,
                scorecard_id=scorecard_id,
                model_decision=model_decision,
            )
            step_kwargs: dict[str, Any] = {"reasoning": reasoning}
            if action_data is not None:
                step_kwargs["data"] = action_data
            next_live_obs = live_env.step(action, **step_kwargs)
            if next_live_obs is None:
                stop_reason = "online_env_step_returned_none"
                break

            mirror_action = action_by_value(mirror_env.action_space, int(selected_action["action_value"]))
            mirror_kwargs: dict[str, Any] = {}
            if action_data is not None:
                mirror_kwargs["data"] = action_data
            next_mirror_obs = mirror_env.step(mirror_action, **mirror_kwargs)
            if next_mirror_obs is None:
                stop_reason = "mirror_env_step_returned_none_after_online_action"
                break

            next_summary = summarize_frame_stack(getattr(next_live_obs, "frame", None))
            post_update_path = actuator_dir / "post_action_mlp_update.json"
            post_update = model_step.build_post_action_mlp_update_artifact(
                args=SimpleNamespace(
                    run_label=f"{step_label}_online_actuator",
                    post_action_mlp_update_mode=args.post_action_mlp_update_mode,
                ),
                obs=live_obs,
                next_obs=next_live_obs,
                action=action,
                action_data=action_data,
                model_decision=model_decision,
                before_summary=before_summary,
                next_summary=next_summary,
            )
            post_update["online_submission"] = True
            post_update["scorecard_submission"] = True
            post_update["scorecard_id"] = scorecard_id
            write_json(post_update_path, post_update)
            post_update_ref = {
                "artifact": _repo_rel(post_update_path),
                "sha256": _sha256(post_update_path),
                "source_step_index": step_index,
                "update_mode": post_update["update_mode"],
                "mlp_weights_updated": post_update["mlp_weights_updated"],
                "training_data_promoted": post_update["training_data_promoted"],
            }
            step_trace = model_step.trace_row(
                args=SimpleNamespace(run_label=f"{step_label}_online_actuator"),
                env=live_env,
                game_name=selected_game["name"],
                obs=live_obs,
                next_obs=next_live_obs,
                action=action,
                action_data=action_data,
                model_decision=model_decision,
                before_summary=before_summary,
                next_summary=next_summary,
                observation_match=observation_match,
                post_action_mlp_update_ref={"artifact": post_update_ref["artifact"], "sha256": post_update_ref["sha256"]},
                post_action_mlp_update=post_update,
            )
            step_trace["online_submission"] = True
            step_trace["scorecard_submission"] = True
            step_trace["scorecard_id"] = scorecard_id
            write_actuator_artifacts(
                actuator_dir=actuator_dir,
                condition=actuator_condition_payload(
                    args,
                    out_dir=actuator_dir,
                    arc_repo=arc_repo,
                    environments_dir=environments_dir,
                    source_condition=source_condition,
                    decision_path=decision_path,
                    selected_game=selected_game,
                    live_arcade=live_arcade,
                    mirror_arcade=mirror_arcade,
                    scorecard_id=scorecard_id,
                    step_index=step_index,
                ),
                model_decision=model_decision,
                trace_row=step_trace,
                post_update=post_update,
                candidate_packets=candidate_packets,
            )

            loop_row = loop_trace_row(
                args=args,
                step_index=step_index,
                scorecard_id=scorecard_id,
                decision_dir=decision_dir,
                actuator_dir=actuator_dir,
                decision_metrics=decision_metrics,
                step_trace=step_trace,
                post_update_ref=post_update_ref,
                obs=live_obs,
                next_obs=next_live_obs,
                mirror_obs=mirror_obs,
                next_mirror_obs=next_mirror_obs,
            )
            trace_rows.append(loop_row)
            frame_rows.append(
                frame_row(
                    step_index=step_index,
                    phase="post_action",
                    obs=next_live_obs,
                    mirror_obs=next_mirror_obs,
                    action=action,
                    action_data=action_data,
                    env=live_env,
                    selected_game=selected_game,
                )
            )
            prior_update_refs.append(post_update_ref)
            write_watch_snapshot(out_dir, args=args, row=loop_row, final=False)
            if args.watch:
                print(json.dumps(watch_payload(args=args, row=loop_row, final=False), sort_keys=True), flush=True)

            live_obs = next_live_obs
            mirror_obs = next_mirror_obs
            if not mirror_matches(live_obs, mirror_obs):
                stop_reason = "mirror_desync_after_online_action"
                break
            if offline_solved(live_obs):
                stop_reason = "online_solved_after_step"
                break
            if terminal_state(live_obs):
                stop_reason = f"terminal_state_after_step:{state_name(getattr(live_obs, 'state', None))}"
                break
    finally:
        if args.close_scorecard:
            final_scorecard = close_scorecard(live_arcade, scorecard_id)
            write_json(out_dir / "scorecard_final.json", scorecard_payload(final_scorecard, scorecard_id))

    metrics = summarize_live_run(
        condition=condition,
        games=games,
        trace_rows=trace_rows,
        frame_rows=frame_rows,
        candidate_packets=all_candidate_packets,
        final_obs=live_obs,
        stop_reason=stop_reason,
        scorecard_id=scorecard_id,
        final_scorecard=final_scorecard,
    )
    _write_jsonl(out_dir / "live_trace.jsonl", trace_rows)
    _write_jsonl(out_dir / "live_frames.jsonl", frame_rows)
    _write_jsonl(out_dir / "candidate_action_packets.jsonl", all_candidate_packets)
    _write_jsonl(out_dir / "post_action_mlp_update_candidates.jsonl", prior_update_refs)
    write_json(out_dir / "metrics.json", metrics)
    replay = compile_live_replay_artifact(
        out_dir=out_dir,
        condition=condition,
        metrics=metrics,
        trace_rows=trace_rows,
        frame_rows=frame_rows,
        scorecard=scorecard_payload(final_scorecard, scorecard_id),
    )
    write_json(out_dir / "compiled_replay.json", replay)
    (out_dir / "compiled_replay.html").write_text(replay_html(replay), encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    write_watch_snapshot(out_dir, args=args, row=trace_rows[-1] if trace_rows else {}, final=True, metrics=metrics)
    return metrics


def create_scorecard(live_arcade: Any, *, args: argparse.Namespace) -> str:
    tags = [tag for tag in args.scorecard_tag if tag]
    if not tags:
        tags = [configured_model_name(args), args.run_label, args.operation_mode.lower(), args.game]
    opaque = {
        "schema": "arc_agi3.live_online_scout_scorecard_opaque.v001",
        "model_name": configured_model_name(args),
        "run_label": args.run_label,
        "git_commit": _git(ROOT, ["rev-parse", "HEAD"]),
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "dream_kernel_review_required": True,
        "nemo_final_confirmation_required": True,
    }
    return str(live_arcade.create_scorecard(source_url=args.scorecard_source_url, tags=tags, opaque=opaque))


def close_scorecard(live_arcade: Any, scorecard_id: str) -> Any | None:
    try:
        return live_arcade.close_scorecard(scorecard_id=scorecard_id)
    except TypeError:
        return live_arcade.close_scorecard(scorecard_id)
    except Exception as error:  # noqa: BLE001 - scorecard close must be recorded but not masked
        return {"close_error": str(error), "scorecard_id": scorecard_id}


def scorecard_payload(scorecard: Any | None, scorecard_id: str) -> dict[str, Any]:
    if scorecard is None:
        return {"scorecard_id": scorecard_id, "available": False}
    if isinstance(scorecard, dict):
        payload = dict(scorecard)
        payload.setdefault("scorecard_id", scorecard_id)
        payload.setdefault("available", False)
        redact_scorecard_payload(payload)
        return payload
    if hasattr(scorecard, "model_dump"):
        payload = scorecard.model_dump(mode="json")
    elif hasattr(scorecard, "dict"):
        payload = scorecard.dict()
    else:
        payload = {"repr": repr(scorecard)}
    payload["scorecard_id"] = scorecard_id
    payload["available"] = True
    redact_scorecard_payload(payload)
    return payload


def redact_scorecard_payload(payload: dict[str, Any]) -> None:
    if "api_key" in payload:
        payload["api_key"] = "REDACTED"


def mirror_matches(live_obs: Any, mirror_obs: Any) -> bool:
    live = summarize_frame_stack(getattr(live_obs, "frame", None))
    mirror = summarize_frame_stack(getattr(mirror_obs, "frame", None))
    return live["latest_frame_sha256"] == mirror["latest_frame_sha256"]


def compact_live_reasoning(
    *,
    args: argparse.Namespace,
    step_index: int,
    scorecard_id: str,
    model_decision: dict[str, Any],
) -> dict[str, Any]:
    reasoning = actuator_reasoning_from_model_decision(model_decision)
    rollout = model_decision.get("internal_forward_rollout", {})
    if not isinstance(rollout, dict):
        rollout = {}
    final_confirmation = {}
    nemo = model_decision.get("nemo3", {})
    if isinstance(nemo, dict) and isinstance(nemo.get("final_confirmation"), dict):
        final_confirmation = nemo["final_confirmation"]
    payload = {
        "schema": "arc_agi3.compact_live_action_reasoning.v001",
        "model_name": configured_model_name(args),
        "run_label": args.run_label,
        "step_index": step_index,
        "scorecard_id": scorecard_id,
        "policy": "standard_world_model_internal_decision_with_external_confirmation",
        "decision_id": model_decision.get("decision_id"),
        "state_id": model_decision.get("state_id"),
        "selected_action": model_decision.get("selected_action"),
        "internal_forward_rollout": reasoning.get("internal_forward_rollout"),
        "internal_forward_rollout_sha256": reasoning.get("internal_forward_rollout_sha256"),
        "solves_before_first_step": rollout.get("solves_before_first_step"),
        "kernel_artifact": rollout.get("kernel_artifact"),
        "kernel_sha256": rollout.get("kernel_sha256"),
        "kernel_simulation_review_artifact": rollout.get("kernel_simulation_review_artifact"),
        "kernel_simulation_review_sha256": rollout.get("kernel_simulation_review_sha256"),
        "nemo3_final_confirmation": final_confirmation.get("artifact"),
        "nemo3_final_confirmation_sha256": final_confirmation.get("sha256"),
        "nemo3_confirms_selected_action": final_confirmation.get("confirms_selected_action"),
        "nemo3_supplied_action": final_confirmation.get("nemo_supplied_action"),
        "online_submission": True,
        "arc_solve_claim": False,
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    if len(encoded.encode("utf-8")) > 16_000:
        payload["selected_action"] = {
            "action_name": (model_decision.get("selected_action") or {}).get("action_name"),
            "action_value": (model_decision.get("selected_action") or {}).get("action_value"),
        }
    return payload


def write_actuator_artifacts(
    *,
    actuator_dir: Path,
    condition: dict[str, Any],
    model_decision: dict[str, Any],
    trace_row: dict[str, Any],
    post_update: dict[str, Any],
    candidate_packets: list[dict[str, Any]],
) -> None:
    write_json(actuator_dir / "condition.json", condition)
    write_json(actuator_dir / "model_decision.json", model_decision)
    write_json(actuator_dir / "post_action_mlp_update.json", post_update)
    _write_jsonl(actuator_dir / "model_step_trace.jsonl", [trace_row])
    _write_jsonl(actuator_dir / "candidate_action_packets.jsonl", candidate_packets)


def loop_trace_row(
    *,
    args: argparse.Namespace,
    step_index: int,
    scorecard_id: str,
    decision_dir: Path,
    actuator_dir: Path,
    decision_metrics: dict[str, Any],
    step_trace: dict[str, Any],
    post_update_ref: dict[str, Any],
    obs: Any,
    next_obs: Any,
    mirror_obs: Any,
    next_mirror_obs: Any,
) -> dict[str, Any]:
    rollout = load_json(decision_dir / "internal_forward_rollout.json")
    return {
        "schema": TRACE_SCHEMA,
        "run_label": args.run_label,
        "step_index": step_index,
        "scorecard_id": scorecard_id,
        "decision_artifact": decision_metrics["model_decision_artifact"],
        "decision_dir": _repo_rel(decision_dir),
        "actuator_dir": _repo_rel(actuator_dir),
        "decision_id": decision_metrics["decision_id"],
        "valid_standard_model_decision": decision_metrics["valid_standard_model_decision"],
        "valid_standard_model_flow_step": True,
        "selected_action": decision_metrics["selected_action"],
        "chosen_action": step_trace["chosen_action"],
        "selected_action_source": decision_metrics["selected_action_source"],
        "nemo3_external_model_invoked": decision_metrics["nemo3_external_model_invoked"],
        "nemo3_final_confirmation": step_trace.get("nemo3_final_confirmation"),
        "nemo3_final_confirmation_sha256": step_trace.get("nemo3_final_confirmation_sha256"),
        "internal_forward_rollout": step_trace.get("internal_forward_rollout"),
        "internal_forward_rollout_sha256": step_trace.get("internal_forward_rollout_sha256"),
        "internal_forward_rollout_solves_before_first_step": step_trace.get(
            "internal_forward_rollout_solves_before_first_step"
        ),
        "kernel_simulation_review_artifact": rollout.get("kernel_simulation_review_artifact"),
        "kernel_simulation_review_sha256": rollout.get("kernel_simulation_review_sha256"),
        "kernel_simulation_review_round_count": rollout.get("kernel_simulation_review_round_count"),
        "kernel_simulation_review_frame_count": rollout.get("kernel_simulation_review_frame_count"),
        "post_action_mlp_update_artifact": post_update_ref["artifact"],
        "post_action_mlp_update_sha256": post_update_ref["sha256"],
        "mlp_weights_updated": post_update_ref["mlp_weights_updated"],
        "training_data_promoted": post_update_ref["training_data_promoted"],
        "levels_completed_start": int(getattr(obs, "levels_completed", 0)),
        "levels_completed_final": int(getattr(next_obs, "levels_completed", 0)),
        "level_delta": int(getattr(next_obs, "levels_completed", 0)) - int(getattr(obs, "levels_completed", 0)),
        "win_levels_start": int(getattr(obs, "win_levels", 0)),
        "win_levels_final": int(getattr(next_obs, "win_levels", 0)),
        "state_start": state_name(getattr(obs, "state", None)),
        "state_final": state_name(getattr(next_obs, "state", None)),
        "frame_sha256": step_trace.get("frame_sha256"),
        "next_frame_sha256": step_trace.get("next_frame_sha256"),
        "frame_changed": step_trace.get("frame_changed"),
        "mirror_frame_sha256": summarize_frame_stack(getattr(mirror_obs, "frame", None))["latest_frame_sha256"],
        "next_mirror_frame_sha256": summarize_frame_stack(getattr(next_mirror_obs, "frame", None))[
            "latest_frame_sha256"
        ],
        "mirror_synced_before_step": mirror_matches(obs, mirror_obs),
        "mirror_synced_after_step": mirror_matches(next_obs, next_mirror_obs),
        "online_solved_after_step": offline_solved(next_obs),
        "terminal_after_step": terminal_state(next_obs),
        "online_submission": True,
        "scorecard_submission": True,
        "arc_solve_claim": False,
    }


def frame_row(
    *,
    step_index: int,
    phase: str,
    obs: Any,
    mirror_obs: Any,
    action: Any | None,
    action_data: Any,
    env: Any,
    selected_game: dict[str, Any],
) -> dict[str, Any]:
    frame_summary = summarize_frame_stack(getattr(obs, "frame", None))
    mirror_summary = summarize_frame_stack(getattr(mirror_obs, "frame", None))
    return {
        "schema": FRAME_SCHEMA,
        "created_at_utc": now_iso(),
        "step_index": step_index,
        "phase": phase,
        "game_name": selected_game["name"],
        "game_id": str(getattr(obs, "game_id", getattr(env.info, "game_id", ""))),
        "guid": str(getattr(obs, "guid", "")),
        "state": state_name(getattr(obs, "state", None)),
        "levels_completed": int(getattr(obs, "levels_completed", 0)),
        "win_levels": int(getattr(obs, "win_levels", 0)),
        "available_action_values": action_values(getattr(env, "action_space", [])),
        "executed_action": None if action is None else f"{action_name(action)}:{action_value(action)}",
        "executed_action_data": action_data,
        "frame": frame_summary,
        "mirror_frame": mirror_summary,
        "mirror_synced": frame_summary["latest_frame_sha256"] == mirror_summary["latest_frame_sha256"],
        "latest_frame_grid": latest_frame_grid(obs),
        "online_submission": True,
        "scorecard_submission": True,
    }


def latest_frame_grid(obs: Any) -> list[list[int]] | None:
    frame_stack = getattr(obs, "frame", None)
    if not frame_stack:
        return None
    latest = frame_stack[-1]
    if hasattr(latest, "tolist"):
        return [[int(value) for value in row] for row in latest.tolist()]
    if isinstance(latest, list):
        return latest
    return None


def compile_live_replay_artifact(
    *,
    out_dir: Path,
    condition: dict[str, Any],
    metrics: dict[str, Any],
    trace_rows: list[dict[str, Any]],
    frame_rows: list[dict[str, Any]],
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    steps = []
    for row in trace_rows:
        review_path = resolve_artifact_path(row.get("kernel_simulation_review_artifact"))
        review = load_json(review_path) if review_path is not None and review_path.is_file() else {}
        steps.append(
            {
                "step_index": row["step_index"],
                "selected_action": row["selected_action"],
                "state_start": row["state_start"],
                "state_final": row["state_final"],
                "levels_completed_start": row["levels_completed_start"],
                "levels_completed_final": row["levels_completed_final"],
                "frame_sha256": row["frame_sha256"],
                "next_frame_sha256": row["next_frame_sha256"],
                "decision_artifact": row["decision_artifact"],
                "kernel_simulation_review_artifact": row.get("kernel_simulation_review_artifact"),
                "kernel_simulation_review_sha256": row.get("kernel_simulation_review_sha256"),
                "predicted_round_count": review.get("round_count"),
                "predicted_frame_count": review.get("frame_count"),
                "predicted_solved": review.get("solved"),
                "predicted_final_state": review.get("final_state"),
                "predicted_final_levels_completed": review.get("final_levels_completed"),
                "predicted_win_levels": review.get("win_levels"),
                "predicted_rounds": review.get("rounds", []),
                "predicted_completion_frames": review.get("completion_frames", []),
                "predicted_next_frame": (review.get("frames") or [{}])[0],
                "mirror_synced_before_step": row["mirror_synced_before_step"],
                "mirror_synced_after_step": row["mirror_synced_after_step"],
            }
        )
    return {
        "schema": REPLAY_SCHEMA,
        "created_at_utc": now_iso(),
        "model_name": condition["model_name"],
        "run_label": condition["run_label"],
        "out_dir": _repo_rel(out_dir),
        "operation_mode": condition["operation_mode"],
        "selected_game": condition["selected_game"],
        "scorecard": scorecard,
        "metrics": {
            "stop_reason": metrics["stop_reason"],
            "online_solve_detected": metrics["online_solve_detected"],
            "official_arc_solve_claim": metrics["official_arc_solve_claim"],
            "online_actions_executed": metrics["online_actions_executed"],
            "levels_completed_final": metrics["levels_completed_final"],
            "win_levels_final": metrics["win_levels_final"],
        },
        "frames": frame_rows,
        "steps": steps,
        "artifact_index": {
            "live_trace": _repo_rel(out_dir / "live_trace.jsonl"),
            "live_frames": _repo_rel(out_dir / "live_frames.jsonl"),
            "metrics": _repo_rel(out_dir / "metrics.json"),
            "scorecard_final": _repo_rel(out_dir / "scorecard_final.json"),
        },
    }


def replay_html(replay: dict[str, Any]) -> str:
    rows = []
    for step in replay.get("steps", []):
        rows.append(
            "<tr>"
            f"<td>{step['step_index']}</td>"
            f"<td>{html_escape(str(step['selected_action']))}</td>"
            f"<td>{html_escape(str(step['state_start']))} -> {html_escape(str(step['state_final']))}</td>"
            f"<td>{step['levels_completed_start']} -> {step['levels_completed_final']}</td>"
            f"<td>{step.get('predicted_round_count')}</td>"
            f"<td>{step.get('predicted_frame_count')}</td>"
            f"<td>{html_escape(str(step.get('predicted_solved')))}</td>"
            f"<td>{html_escape(str(step.get('mirror_synced_after_step')))}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>ARC-AGI-3 Live Replay</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:24px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;text-align:left}"
        "code{background:#eee;padding:2px 4px}</style></head><body>"
        f"<h1>{html_escape(str(replay.get('model_name')))} / {html_escape(str(replay.get('run_label')))}</h1>"
        f"<p>mode <code>{html_escape(str(replay.get('operation_mode')))}</code> "
        f"game <code>{html_escape(str((replay.get('selected_game') or {}).get('game_id')))}</code></p>"
        "<table><thead><tr><th>Step</th><th>Action</th><th>State</th><th>Levels</th>"
        "<th>Predicted Rounds</th><th>Predicted Frames</th><th>Predicted Solve</th><th>Mirror Synced</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>\n"
    )


def write_watch_snapshot(
    out_dir: Path,
    *,
    args: argparse.Namespace,
    row: dict[str, Any],
    final: bool,
    metrics: dict[str, Any] | None = None,
) -> None:
    payload = watch_payload(args=args, row=row, final=final, metrics=metrics)
    write_json(out_dir / "watch" / "latest.json", payload)
    if row:
        write_json(out_dir / "watch" / f"step_{int(row.get('step_index', -1)):03d}.json", payload)


def watch_payload(
    *,
    args: argparse.Namespace,
    row: dict[str, Any],
    final: bool,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": WATCH_SCHEMA,
        "created_at_utc": now_iso(),
        "model_name": configured_model_name(args),
        "run_label": args.run_label,
        "final": final,
        "step_index": row.get("step_index"),
        "selected_action": row.get("selected_action"),
        "state": None if not row else f"{row.get('state_start')} -> {row.get('state_final')}",
        "levels": None if not row else f"{row.get('levels_completed_start')} -> {row.get('levels_completed_final')}",
        "nemo3_external_model_invoked": row.get("nemo3_external_model_invoked"),
        "kernel_simulation_review_artifact": row.get("kernel_simulation_review_artifact"),
        "mirror_synced_after_step": row.get("mirror_synced_after_step"),
        "metrics": metrics,
    }


def condition_payload(
    args: argparse.Namespace,
    *,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    selected_game: dict[str, Any],
    live_arcade: Any,
    mirror_arcade: Any,
    scorecard_id: str,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "model_name": configured_model_name(args),
        "model_identity": {
            "name": configured_model_name(args),
            "family": "nano_world_model",
            "actuation_policy": "3d_world_model_internal_lock_then_nemo_confirmation_then_single_arc_action",
            "nemo_role": "confirmation_not_action_source",
            "dream_kernel_role": "mandatory_3d_simulation_review_before_online_action",
            "mlp_role": "chronometric_game_knowledge_and_post_action_candidate_update_context",
        },
        "run_label": args.run_label,
        "run_kind": "arc_agi3_live_online_scout",
        "run_label_semantics": "new_experiment_guarded_online_world_model_scout",
        "created_at_utc": now_iso(),
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
        "mirror_operation_mode": "OFFLINE",
        "toolkit": "arc_agi.Arcade",
        "toolkit_versions": {"arc_agi": package_version("arc_agi"), "arcengine": package_version("arcengine")},
        "scorecard_id": scorecard_id,
        "scorecard_submission": True,
        "online_submission": True,
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "nemo_mode": args.nemo_mode,
        "nemo_external_model_required": args.nemo_mode == producer.LIVE_NEMO_MODE,
        "nemo_relay_url": args.nemo_relay_url if args.nemo_mode == producer.LIVE_NEMO_MODE else None,
        "nemo_model": args.nemo_model,
        "arc_api_key_source": getattr(args, "arc_api_key_source", "unknown"),
        "arc_env_file": str(args.arc_env_file) if args.arc_env_file else None,
        "arc_env_file_loaded": bool(getattr(args, "arc_api_key_loaded_from_env_file", False)),
        "max_real_steps": args.max_real_steps,
        "post_action_mlp_update_mode": args.post_action_mlp_update_mode,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": args.seed,
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": f"max_real_steps={args.max_real_steps}",
        "loader_mode": "arc_agi_online_or_competition_environment_with_offline_source_mirror",
        "loader_settings": {
            "operation_mode": args.operation_mode,
            "mirror_operation_mode": "OFFLINE",
            "game": args.game,
            "max_candidate_actions": args.max_candidate_actions,
            "max_real_steps": args.max_real_steps,
            "branch_ambiguity_gap_threshold": args.branch_ambiguity_gap_threshold,
            "internal_rollout_max_steps": args.internal_rollout_max_steps,
            "internal_rollout_kernel_timeout": args.internal_rollout_kernel_timeout,
            "save_recording": args.save_recording,
            "render_mode": args.render_mode,
            "confirm_online_actions": args.confirm_online_actions,
            "require_explicit_arc_api_key": args.require_explicit_arc_api_key,
        },
        "metric_to_compare": "online_scorecard_solve_and_standard_world_model_gate_validity",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "mandatory_dream_kernel_ls20_simulation_review_before_online_action",
        "arc_data_used": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "live_arcade_class": type(live_arcade).__name__,
        "mirror_arcade_class": type(mirror_arcade).__name__,
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
    live_arcade: Any,
    mirror_arcade: Any,
    scorecard_id: str,
    step_index: int,
    prior_update_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema": producer.SCHEMA,
        "model_name": configured_model_name(args),
        "run_label": decision_args.run_label,
        "run_kind": "arc_agi3_live_online_scout_decision_step",
        "parent_run_label": args.run_label,
        "step_index": step_index,
        "created_at_utc": now_iso(),
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
        "mirror_operation_mode": "OFFLINE",
        "toolkit": "arc_agi.Arcade",
        "toolkit_versions": {"arc_agi": package_version("arc_agi"), "arcengine": package_version("arcengine")},
        "scorecard_id": scorecard_id,
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "nemo_mode": args.nemo_mode,
        "nemo_external_model_required": args.nemo_mode == producer.LIVE_NEMO_MODE,
        "nemo_relay_url": args.nemo_relay_url if args.nemo_mode == producer.LIVE_NEMO_MODE else None,
        "nemo_model": args.nemo_model,
        "prior_post_action_update_context_count": len(prior_update_refs),
        "prior_post_action_update_candidates": prior_update_refs,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": args.seed,
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": f"parent_max_real_steps={args.max_real_steps}",
        "loader_mode": "online_observation_with_offline_source_mirror_decision_step",
        "metric_to_compare": "valid_model_decision_artifact_before_online_action",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "mandatory_dream_kernel_ls20_simulation_review_before_online_action",
        "arc_data_used": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": True,
        "scorecard_submission": True,
        "live_arcade_class": type(live_arcade).__name__,
        "mirror_arcade_class": type(mirror_arcade).__name__,
    }


def actuator_condition_payload(
    args: argparse.Namespace,
    *,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    decision_path: Path,
    selected_game: dict[str, Any],
    live_arcade: Any,
    mirror_arcade: Any,
    scorecard_id: str,
    step_index: int,
) -> dict[str, Any]:
    return {
        "schema": model_step.SCHEMA,
        "model_name": configured_model_name(args),
        "run_label": f"{args.run_label}_step_{step_index:03d}_online_actuator",
        "run_kind": "arc_agi3_live_online_scout_actuator_step",
        "parent_run_label": args.run_label,
        "step_index": step_index,
        "created_at_utc": now_iso(),
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
        "mirror_operation_mode": "OFFLINE",
        "scorecard_id": scorecard_id,
        "toolkit": "arc_agi.Arcade",
        "toolkit_versions": {"arc_agi": package_version("arc_agi"), "arcengine": package_version("arcengine")},
        "model_decision_artifact": _repo_rel(decision_path),
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "actuator_step_count": 1,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": args.seed,
        "gpu_count": 0,
        "world_size": 1,
        "loader_mode": "arc_agi_online_environment_wrapper_as_actuator_with_offline_mirror",
        "post_action_mlp_update_mode": args.post_action_mlp_update_mode,
        "metric_to_compare": "online_action_standard_model_flow_validity_and_one_step_trace",
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": True,
        "scorecard_submission": True,
        "live_arcade_class": type(live_arcade).__name__,
        "mirror_arcade_class": type(mirror_arcade).__name__,
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
        allow_source_env_solver=True,
    )


def summarize_live_run(
    *,
    condition: dict[str, Any],
    games: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    frame_rows: list[dict[str, Any]],
    candidate_packets: list[dict[str, Any]],
    final_obs: Any,
    stop_reason: str,
    scorecard_id: str,
    final_scorecard: Any | None,
) -> dict[str, Any]:
    final_levels = int(getattr(final_obs, "levels_completed", 0))
    final_win_levels = int(getattr(final_obs, "win_levels", 0))
    online_solved = offline_solved(final_obs)
    valid_steps = all(
        row["valid_standard_model_decision"] is True
        and row["valid_standard_model_flow_step"] is True
        and row["internal_forward_rollout_solves_before_first_step"] is True
        and row["mirror_synced_before_step"] is True
        and row["mirror_synced_after_step"] is True
        and row["training_data_promoted"] is False
        for row in trace_rows
    )
    nemo_valid = all(row["nemo3_external_model_invoked"] is True for row in trace_rows) if trace_rows else True
    return {
        "schema": SCHEMA,
        "condition": condition,
        "available_game_count": len(games),
        "selected_game": condition["selected_game"],
        "scorecard_id": scorecard_id,
        "scorecard_final_available": final_scorecard is not None,
        "valid_live_online_scout": bool(valid_steps and nemo_valid and condition["online_submission"]),
        "stop_reason": stop_reason,
        "online_solve_detected": online_solved,
        "official_arc_solve_claim": bool(condition["operation_mode"] == "COMPETITION" and online_solved),
        "online_actions_executed": len(trace_rows),
        "model_decisions": len(trace_rows),
        "candidate_action_packets": len(candidate_packets),
        "frame_rows": len(frame_rows),
        "final_state": state_name(getattr(final_obs, "state", None)),
        "levels_completed_final": final_levels,
        "win_levels_final": final_win_levels,
        "levels_completed_delta": 0 if not trace_rows else final_levels - int(trace_rows[0]["levels_completed_start"]),
        "selected_actions": [row["selected_action"] for row in trace_rows],
        "nemo3_external_model_invocations": sum(1 for row in trace_rows if row["nemo3_external_model_invoked"] is True),
        "mirror_sync_valid": all(row["mirror_synced_after_step"] is True for row in trace_rows),
        "mlp_weights_updated": False,
        "training_data_promoted": False,
        "online_submission": True,
        "scorecard_submission": True,
        "arc_solve_claim": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC-AGI-3 Live Online Scout Results",
        "",
        "Status: guarded online/competition ARC run through the standard world-model decision loop.",
        "",
        "## Condition",
        "",
        f"- model name: `{condition['model_name']}`",
        f"- run label: `{condition['run_label']}`",
        f"- operation mode: `{condition['operation_mode']}`",
        f"- mirror mode: `{condition['mirror_operation_mode']}`",
        f"- selected game: `{condition['selected_game']['game_id']}`",
        f"- scorecard id: `{condition['scorecard_id']}`",
        f"- max real steps: `{condition['max_real_steps']}`",
        f"- Nemo mode: `{condition['nemo_mode']}`",
        f"- ARC API key source: `{condition['arc_api_key_source']}`",
        f"- online submission: `{condition['online_submission']}`",
        "",
        "## Metrics",
        "",
        f"- valid live online scout: `{metrics['valid_live_online_scout']}`",
        f"- online solve detected: `{metrics['online_solve_detected']}`",
        f"- official ARC solve claim: `{metrics['official_arc_solve_claim']}`",
        f"- stop reason: `{metrics['stop_reason']}`",
        f"- online actions executed: `{metrics['online_actions_executed']}`",
        f"- levels completed final: `{metrics['levels_completed_final']}`",
        f"- win levels final: `{metrics['win_levels_final']}`",
        f"- mirror sync valid: `{metrics['mirror_sync_valid']}`",
        f"- replay: `compiled_replay.html` / `compiled_replay.json`",
        "",
    ]
    return "\n".join(lines)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return payload if isinstance(payload, dict) else {}


def resolve_artifact_path(artifact: Any) -> Path | None:
    if not isinstance(artifact, str) or not artifact:
        return None
    path = Path(artifact)
    return path if path.is_absolute() else ROOT / path


def configured_model_name(args: argparse.Namespace) -> str:
    return str(getattr(args, "model_name", DEFAULT_MODEL_NAME) or DEFAULT_MODEL_NAME)


def load_env_file(path: Path | None) -> set[str]:
    if path is None:
        return set()
    if not path.exists():
        return set()
    if not path.is_file():
        raise FileNotFoundError(f"ARC env path is not a file: {path}")
    loaded: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value
        loaded.add(key)
    return loaded


def arc_api_key_source(args: argparse.Namespace, *, loaded_env_keys: set[str]) -> str:
    if args.arc_api_key:
        return "argument"
    if "ARC_API_KEY" in loaded_env_keys:
        return "arc_env_file"
    if os.environ.get("ARC_API_KEY"):
        return "environment"
    return "missing_or_anonymous"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def html_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--recordings-dir", type=Path, default=ROOT / "recordings")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_agi3_live_online_scout_v061_ls20_guarded")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--operation-mode", choices=("ONLINE", "COMPETITION"), default="ONLINE")
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument("--max-real-steps", type=int, default=320)
    parser.add_argument("--branch-ambiguity-gap-threshold", type=float, default=0.0)
    parser.add_argument("--internal-rollout-max-steps", type=int, default=32)
    parser.add_argument("--internal-rollout-kernel-timeout", type=int, default=30)
    parser.add_argument("--arc-grid-agent-label", type=int, default=None)
    parser.add_argument("--arc-grid-goal-label", type=int, default=None)
    parser.add_argument("--arc-grid-wall-labels", default="")
    parser.add_argument("--arc-grid-hazard-labels", default="")
    parser.add_argument("--nemo-mode", choices=(producer.LOCAL_NEMO_MODE, producer.LIVE_NEMO_MODE), default=producer.LIVE_NEMO_MODE)
    parser.add_argument("--nemo-relay-url", default=os.environ.get("NEMO_RELAY_URL", "http://127.0.0.1:8000/v1/responses"))
    parser.add_argument("--nemo-model", default=os.environ.get("NEMO_RELAY_MODEL", "nemotron_3_nano_omni"))
    parser.add_argument("--nemo-timeout", type=int, default=180)
    parser.add_argument("--post-action-mlp-update-mode", choices=("candidate-only",), default="candidate-only")
    parser.add_argument("--historical-comparator", default="v059_full_local_live_nemo_311_and_v060_simulation_review_reset")
    parser.add_argument("--historical-comparator-artifact", type=Path, default=ROOT / "goal_test_results.md")
    parser.add_argument("--arc-api-key", default="")
    parser.add_argument("--arc-env-file", type=Path, default=DEFAULT_ARC_ENV_FILE)
    parser.add_argument("--scorecard-id", default="")
    parser.add_argument("--scorecard-source-url", default="https://github.com/newjordan/nano-world-model")
    parser.add_argument("--scorecard-tag", action="append", default=[])
    parser.add_argument("--save-recording", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--close-scorecard", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--render-mode", default=None)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--confirm-online-actions", action="store_true")
    parser.add_argument("--allow-anonymous-api-key", dest="require_explicit_arc_api_key", action="store_false")
    parser.set_defaults(require_explicit_arc_api_key=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "model_name": metrics["condition"]["model_name"],
                "valid_live_online_scout": metrics["valid_live_online_scout"],
                "online_solve_detected": metrics["online_solve_detected"],
                "official_arc_solve_claim": metrics["official_arc_solve_claim"],
                "stop_reason": metrics["stop_reason"],
                "online_actions_executed": metrics["online_actions_executed"],
                "levels_completed_final": metrics["levels_completed_final"],
                "win_levels_final": metrics["win_levels_final"],
                "scorecard_id": metrics["scorecard_id"],
                "out_dir": _repo_rel(args.out_dir.resolve()),
                "compiled_replay": _repo_rel(args.out_dir.resolve() / "compiled_replay.html"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
