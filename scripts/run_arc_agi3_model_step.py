#!/usr/bin/env python3
"""Execute one ARC-AGI-3 actuator step from a standard ModelDecision artifact.

This is the merged boundary: the ARC wrapper is only the actuator, and it is
downstream of the Nemo3/world-model decision. The runner does not choose a
policy from ``env.action_space``. It validates a ModelDecision artifact produced
by the standard flow, executes exactly one selected action, and records the
provenance.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_agi3_model_flow import (  # noqa: E402
    CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
    CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
    CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA,
    CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
    INTERNAL_FORWARD_ROLLOUT_SCHEMA,
    INTERNAL_THINKING_LOCK_SCHEMA,
    MLP_CONSULTATION_SCHEMA,
    MODEL_DECISION_SCHEMA,
    NEMO3_FINAL_CONFIRMATION_SCHEMA,
    NEMO3_INTERIM_CONFIRMATION_SCHEMA,
    SELECTED_ACTION_SOURCE,
    STANDARD_MODEL_FLOW,
    actuator_reasoning_from_model_decision,
    load_model_decision,
    require_standard_model_decision,
)
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
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_agi3_model_step_v043_standard_flow"
SCHEMA = "arc_agi3.model_step.v001"
TRACE_SCHEMA = "arc_agi3.model_step_trace_row.v001"
POST_ACTION_MLP_UPDATE_SCHEMA = "arc_agi3.post_action_mlp_update_candidate.v001"


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    prepare_out_dir(out_dir)
    arc_repo = args.arc_repo.resolve()
    environments_dir = args.environments_dir.resolve()
    source_condition = args.source_condition_artifact.resolve()
    decision_path = args.model_decision_artifact.resolve()
    if not source_condition.exists():
        raise FileNotFoundError(source_condition)
    if not environments_dir.exists():
        raise FileNotFoundError(environments_dir)
    if not decision_path.exists():
        raise FileNotFoundError(decision_path)

    Arcade, OperationMode = load_arcade()
    operation_mode = getattr(OperationMode, args.operation_mode)
    arcade = Arcade(operation_mode=operation_mode, environments_dir=str(environments_dir))
    games = normalize_games(arcade.get_environments())
    selected_game = select_game(games, args.game)
    env = arcade.make(selected_game["name"])
    obs = env.reset()
    if obs is None:
        raise RuntimeError(f"{selected_game['name']} reset returned None")

    candidate_packets = candidate_action_packets(
        env=env,
        game_name=selected_game["name"],
        observation_guid=str(getattr(obs, "guid", "")),
        phase="model_step_pre_action",
        max_actions=args.max_candidate_actions,
    )
    available_values = action_values(getattr(env, "action_space", []))
    model_decision = load_model_decision(decision_path)
    selected_action = require_standard_model_decision(
        model_decision,
        available_action_values=available_values,
        require_internal_solve=not args.allow_unsolved_internal_rollout_for_contract_test,
    )
    action = action_by_value(env.action_space, int(selected_action["action_value"]))
    action_data = selected_action.get("action_data")
    before_summary = summarize_frame_stack(getattr(obs, "frame", None))
    observation_match = require_observation_artifact_match(
        model_decision=model_decision,
        obs=obs,
        env=env,
        frame_summary=before_summary,
    )
    reasoning = actuator_reasoning_from_model_decision(model_decision)
    reasoning["run_label"] = args.run_label

    step_kwargs: dict[str, Any] = {"reasoning": reasoning}
    if action_data is not None:
        step_kwargs["data"] = action_data
    next_obs = env.step(action, **step_kwargs)
    if next_obs is None:
        raise RuntimeError(f"env.step returned None after {action_name(action)}")

    next_summary = summarize_frame_stack(getattr(next_obs, "frame", None))
    post_action_mlp_update_path = out_dir / "post_action_mlp_update.json"
    post_action_mlp_update = build_post_action_mlp_update_artifact(
        args=args,
        obs=obs,
        next_obs=next_obs,
        action=action,
        action_data=action_data,
        model_decision=model_decision,
        before_summary=before_summary,
        next_summary=next_summary,
    )
    post_action_mlp_update_path.write_text(
        json.dumps(post_action_mlp_update, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    post_action_mlp_update_ref = {
        "artifact": _repo_rel(post_action_mlp_update_path),
        "sha256": _sha256(post_action_mlp_update_path),
    }
    trace_rows = [
        trace_row(
            args=args,
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
            post_action_mlp_update_ref=post_action_mlp_update_ref,
            post_action_mlp_update=post_action_mlp_update,
        )
    ]
    condition = condition_payload(
        args,
        out_dir=out_dir,
        arc_repo=arc_repo,
        environments_dir=environments_dir,
        source_condition=source_condition,
        decision_path=decision_path,
        selected_game=selected_game,
        arcade=arcade,
    )
    metrics = summarize_model_step(
        condition=condition,
        games=games,
        trace_rows=trace_rows,
        candidate_packets=candidate_packets,
        model_decision=model_decision,
    )
    (out_dir / "model_decision.json").write_text(
        json.dumps(model_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_jsonl(out_dir / "model_step_trace.jsonl", trace_rows)
    _write_jsonl(out_dir / "candidate_action_packets.jsonl", candidate_packets)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def trace_row(
    *,
    args: argparse.Namespace,
    env: Any,
    game_name: str,
    obs: Any,
    next_obs: Any,
    action: Any,
    action_data: Any,
    model_decision: dict[str, Any],
    before_summary: dict[str, Any],
    next_summary: dict[str, Any],
    observation_match: dict[str, Any],
    post_action_mlp_update_ref: dict[str, str],
    post_action_mlp_update: dict[str, Any],
) -> dict[str, Any]:
    levels_completed = int(getattr(obs, "levels_completed", 0))
    next_levels_completed = int(getattr(next_obs, "levels_completed", 0))
    nemo3 = model_decision.get("nemo3", {}) if isinstance(model_decision.get("nemo3"), dict) else {}
    final_confirmation = (
        nemo3.get("final_confirmation", {}) if isinstance(nemo3.get("final_confirmation"), dict) else {}
    )
    game_knowledge = (
        model_decision.get("chronometric_game_knowledge", {})
        if isinstance(model_decision.get("chronometric_game_knowledge"), dict)
        else {}
    )
    internal_forward_rollout = (
        model_decision.get("internal_forward_rollout", {})
        if isinstance(model_decision.get("internal_forward_rollout"), dict)
        else {}
    )
    interim_confirmations = nemo3.get("interim_confirmations", [])
    if not isinstance(interim_confirmations, list):
        interim_confirmations = []
    selected_action = (
        model_decision.get("selected_action", {}) if isinstance(model_decision.get("selected_action"), dict) else {}
    )
    return {
        "schema": TRACE_SCHEMA,
        "run_label": args.run_label,
        "game_name": game_name,
        "game_id": str(getattr(obs, "game_id", getattr(env.info, "game_id", ""))),
        "state_id": model_decision["state_id"],
        "decision_id": model_decision["decision_id"],
        "source_model_decision_id": model_decision["decision_id"],
        "observation_artifact": observation_match["artifact"],
        "observation_artifact_sha256": observation_match["sha256"],
        "observation_content_match": observation_match["content_match"],
        "observation_guid_match": observation_match["guid_match"],
        "model_observation_guid": observation_match["expected_guid"],
        "current_observation_guid": observation_match["current_guid"],
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
        "chosen_action": f"{action_name(action)}:{action_value(action)}",
        "chosen_action_name": action_name(action),
        "chosen_action_value": action_value(action),
        "action_data": action_data,
        "frame_shape": before_summary["latest_frame_shape"],
        "frame_sha256": before_summary["latest_frame_sha256"],
        "next_frame_shape": next_summary["latest_frame_shape"],
        "next_frame_sha256": next_summary["latest_frame_sha256"],
        "frame_changed": before_summary["latest_frame_sha256"] != next_summary["latest_frame_sha256"],
        "model_decision_schema": model_decision.get("schema"),
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "selected_action_source": selected_action.get("source"),
        "chronometric_game_knowledge": game_knowledge.get("artifact"),
        "chronometric_game_knowledge_sha256": game_knowledge.get("sha256"),
        "chronometric_game_knowledge_score_surface": game_knowledge.get("score_surface"),
        "chronometric_game_knowledge_action_embedding_linked": game_knowledge.get("action_embedding_context_linked"),
        "chronometric_game_knowledge_branch_library_linked": game_knowledge.get("branch_library_linked"),
        "nemo3_invoked": nemo3.get("invoked") is True,
        "nemo3_role": nemo3.get("role"),
        "nemo3_decision_delegated_to_nemo": nemo3.get("decision_delegated_to_nemo"),
        "nemo3_final_confirmation": final_confirmation.get("artifact"),
        "nemo3_final_confirmation_sha256": final_confirmation.get("sha256"),
        "nemo3_interim_confirmation_count": len(interim_confirmations),
        "mlp_consultation": _dict(model_decision.get("mlp_consultation")).get("artifact"),
        "mlp_consultation_sha256": _dict(model_decision.get("mlp_consultation")).get("sha256"),
        "internal_forward_rollout": internal_forward_rollout.get("artifact"),
        "internal_forward_rollout_sha256": internal_forward_rollout.get("sha256"),
        "internal_forward_rollout_kernel_supported": internal_forward_rollout.get("kernel_supported"),
        "internal_forward_rollout_solves_before_first_step": internal_forward_rollout.get(
            "solves_before_first_step"
        ),
        "post_action_mlp_update_artifact": post_action_mlp_update_ref["artifact"],
        "post_action_mlp_update_sha256": post_action_mlp_update_ref["sha256"],
        "post_action_mlp_update_candidate_written": True,
        "post_action_mlp_update_mode": post_action_mlp_update["update_mode"],
        "mlp_weights_updated": post_action_mlp_update["mlp_weights_updated"],
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def build_post_action_mlp_update_artifact(
    *,
    args: argparse.Namespace,
    obs: Any,
    next_obs: Any,
    action: Any,
    action_data: Any,
    model_decision: dict[str, Any],
    before_summary: dict[str, Any],
    next_summary: dict[str, Any],
) -> dict[str, Any]:
    selected_action = _dict(model_decision.get("selected_action"))
    mlp_consultation = _dict(model_decision.get("mlp_consultation"))
    game_knowledge = _dict(model_decision.get("chronometric_game_knowledge"))
    levels_completed = int(getattr(obs, "levels_completed", 0))
    next_levels_completed = int(getattr(next_obs, "levels_completed", 0))
    level_delta = next_levels_completed - levels_completed
    frame_changed = before_summary["latest_frame_sha256"] != next_summary["latest_frame_sha256"]
    return {
        "schema": POST_ACTION_MLP_UPDATE_SCHEMA,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_label": args.run_label,
        "decision_id": model_decision.get("decision_id"),
        "source_model_decision_id": model_decision.get("decision_id"),
        "state_id": model_decision.get("state_id"),
        "update_mode": args.post_action_mlp_update_mode,
        "update_candidate_written": True,
        "mlp_weights_updated": False,
        "training_data_promoted": False,
        "heldout_labels_used": False,
        "online_update_requires_promotion_condition": True,
        "promotion_condition_satisfied": False,
        "target_surface": CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
        "score_surface": CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
        "mlp_consultation_artifact": mlp_consultation.get("artifact"),
        "mlp_consultation_sha256": mlp_consultation.get("sha256"),
        "chronometric_game_knowledge_artifact": game_knowledge.get("artifact"),
        "chronometric_game_knowledge_sha256": game_knowledge.get("sha256"),
        "selected_action": {
            "action_name": selected_action.get("action_name", action_name(action)),
            "action_value": int(selected_action.get("action_value", action_value(action))),
            "action_data": action_data,
            "source": selected_action.get("source"),
        },
        "pre_action_observation": {
            "guid": str(getattr(obs, "guid", "")),
            "state": state_name(getattr(obs, "state", None)),
            "levels_completed": levels_completed,
            "win_levels": int(getattr(obs, "win_levels", 0)),
            "frame": before_summary,
        },
        "post_action_observation": {
            "guid": str(getattr(next_obs, "guid", "")),
            "state": state_name(getattr(next_obs, "state", None)),
            "levels_completed": next_levels_completed,
            "win_levels": int(getattr(next_obs, "win_levels", 0)),
            "frame": next_summary,
        },
        "post_action_calibration_label": {
            "source": "post_action_observation_only",
            "frame_changed": frame_changed,
            "level_delta": level_delta,
            "next_state": state_name(getattr(next_obs, "state", None)),
            "direct_outcome_fields_are_post_action_only": True,
        },
        "candidate_update": {
            "kind": "chronometric_calibration_mlp_transition_candidate",
            "apply_to_weights_now": False,
            "append_to_branch_library_candidate_buffer": True,
            "requires_review_or_promotion": True,
            "features": {
                "action_value": int(selected_action.get("action_value", action_value(action))),
                "before_frame_sha256": before_summary["latest_frame_sha256"],
                "after_frame_sha256": next_summary["latest_frame_sha256"],
                "frame_changed": frame_changed,
            },
            "targets": {
                "level_delta": level_delta,
                "frame_changed": frame_changed,
            },
        },
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def require_observation_artifact_match(
    *,
    model_decision: dict[str, Any],
    obs: Any,
    env: Any,
    frame_summary: dict[str, Any],
) -> dict[str, Any]:
    flow = model_decision.get("standard_model_flow", {})
    if not isinstance(flow, dict):
        raise RuntimeError("ModelDecision standard_model_flow is missing")
    artifact_ref = flow.get("observation_artifact")
    artifact_path = resolve_model_artifact(artifact_ref)
    expected = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(expected, dict):
        raise RuntimeError(f"observation_artifact is not a JSON object: {artifact_ref}")

    current = {
        "game_id": str(getattr(obs, "game_id", getattr(env.info, "game_id", ""))),
        "state": state_name(getattr(obs, "state", None)),
        "levels_completed": int(getattr(obs, "levels_completed", 0)),
        "win_levels": int(getattr(obs, "win_levels", 0)),
        "full_reset": bool(getattr(obs, "full_reset", False)),
        "available_action_values": action_values(getattr(env, "action_space", [])),
        "frame_stack_len": frame_summary["frame_stack_len"],
        "latest_frame_shape": frame_summary["latest_frame_shape"],
        "latest_frame_min": frame_summary["latest_frame_min"],
        "latest_frame_max": frame_summary["latest_frame_max"],
        "latest_frame_sha256": frame_summary["latest_frame_sha256"],
    }
    expected_frame = expected.get("frame") if isinstance(expected.get("frame"), dict) else {}
    expected_values = {
        "game_id": str(expected.get("game_id", "")),
        "state": str(expected.get("state", "")),
        "levels_completed": int(expected.get("levels_completed", 0)),
        "win_levels": int(expected.get("win_levels", 0)),
        "full_reset": bool(expected.get("full_reset", False)),
        "available_action_values": [int(value) for value in expected.get("available_action_values", [])],
        "frame_stack_len": expected_frame.get("frame_stack_len"),
        "latest_frame_shape": expected_frame.get("latest_frame_shape"),
        "latest_frame_min": expected_frame.get("latest_frame_min"),
        "latest_frame_max": expected_frame.get("latest_frame_max"),
        "latest_frame_sha256": expected_frame.get("latest_frame_sha256"),
    }
    mismatches = [key for key, current_value in current.items() if current_value != expected_values.get(key)]
    if mismatches:
        details = ", ".join(
            f"{key}: current={current[key]!r} expected={expected_values.get(key)!r}"
            for key in mismatches
        )
        raise RuntimeError(
            "current observation does not match ModelDecision observation_artifact "
            f"{artifact_ref}: {details}"
        )

    current_guid = str(getattr(obs, "guid", ""))
    expected_guid = str(expected.get("guid", ""))
    return {
        "artifact": _repo_rel(artifact_path),
        "sha256": _sha256(artifact_path),
        "content_match": True,
        "guid_match": current_guid == expected_guid,
        "current_guid": current_guid,
        "expected_guid": expected_guid,
        "matched_fields": sorted(current),
    }


def resolve_model_artifact(artifact_ref: Any) -> Path:
    if not isinstance(artifact_ref, str) or not artifact_ref.strip():
        raise RuntimeError("ModelDecision observation_artifact is required")
    if artifact_ref.startswith("artifact://"):
        raise RuntimeError(f"ModelDecision observation_artifact is not a file path: {artifact_ref}")
    path = Path(artifact_ref)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise FileNotFoundError(path)
    return path.resolve()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def condition_payload(
    args: argparse.Namespace,
    *,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    decision_path: Path,
    selected_game: dict[str, Any],
    arcade: Any,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "run_label": args.run_label,
        "run_kind": "arc_agi3_standard_model_flow_actuator_step",
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
        "allow_unsolved_internal_rollout_for_contract_test": args.allow_unsolved_internal_rollout_for_contract_test,
        "metric_to_compare": "arc_agi3_standard_model_flow_validity_and_one_step_trace",
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def summarize_model_step(
    *,
    condition: dict[str, Any],
    games: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    candidate_packets: list[dict[str, Any]],
    model_decision: dict[str, Any],
) -> dict[str, Any]:
    row = trace_rows[0]
    return {
        "schema": SCHEMA,
        "condition": condition,
        "available_game_count": len(games),
        "selected_game": condition["selected_game"],
        "model_decision_schema": model_decision.get("schema"),
        "decision_id": model_decision.get("decision_id"),
        "source_model_decision_id": row.get("source_model_decision_id"),
        "state_id": model_decision.get("state_id"),
        "candidate_action_packets": len(candidate_packets),
        "actuator_steps_executed": len(trace_rows),
        "chosen_action": row["chosen_action"],
        "chosen_action_name": row["chosen_action_name"],
        "chosen_action_value": row["chosen_action_value"],
        "frame_changed": row["frame_changed"],
        "levels_completed_start": row["levels_completed"],
        "levels_completed_final": row["next_levels_completed"],
        "levels_completed_delta": row["level_delta"],
        "final_state": row["next_state"],
        "nemo3_invoked": row["nemo3_invoked"],
        "nemo3_final_confirmation": row.get("nemo3_final_confirmation"),
        "nemo3_interim_confirmation_count": row.get("nemo3_interim_confirmation_count", 0),
        "chronometric_game_knowledge": row.get("chronometric_game_knowledge"),
        "chronometric_game_knowledge_score_surface": row.get("chronometric_game_knowledge_score_surface"),
        "observation_artifact": row.get("observation_artifact"),
        "observation_artifact_sha256": row.get("observation_artifact_sha256"),
        "observation_content_match": row.get("observation_content_match"),
        "observation_guid_match": row.get("observation_guid_match"),
        "mlp_consultation": row.get("mlp_consultation"),
        "mlp_consultation_sha256": row.get("mlp_consultation_sha256"),
        "internal_forward_rollout": row.get("internal_forward_rollout"),
        "internal_forward_rollout_sha256": row.get("internal_forward_rollout_sha256"),
        "internal_forward_rollout_kernel_supported": row.get("internal_forward_rollout_kernel_supported"),
        "internal_forward_rollout_solves_before_first_step": row.get(
            "internal_forward_rollout_solves_before_first_step"
        ),
        "post_action_mlp_update_artifact": row.get("post_action_mlp_update_artifact"),
        "post_action_mlp_update_sha256": row.get("post_action_mlp_update_sha256"),
        "post_action_mlp_update_candidate_written": row.get("post_action_mlp_update_candidate_written"),
        "post_action_mlp_update_mode": row.get("post_action_mlp_update_mode"),
        "mlp_weights_updated": row.get("mlp_weights_updated"),
        "valid_standard_model_flow_step": bool(
            len(trace_rows) == 1
            and model_decision.get("schema") == MODEL_DECISION_SCHEMA
            and row["chosen_action_value"] in row["available_action_values"]
            and row.get("observation_content_match") is True
            and row.get("selected_action_source") == SELECTED_ACTION_SOURCE
            and row.get("chronometric_game_knowledge")
            and row.get("chronometric_game_knowledge_score_surface") == CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE
            and row.get("chronometric_game_knowledge_action_embedding_linked") is True
            and row.get("chronometric_game_knowledge_branch_library_linked") is True
            and row.get("mlp_consultation")
            and row.get("internal_forward_rollout")
            and (
                condition.get("allow_unsolved_internal_rollout_for_contract_test") is True
                or row.get("internal_forward_rollout_solves_before_first_step") is True
            )
            and row.get("post_action_mlp_update_candidate_written") is True
            and row.get("mlp_weights_updated") is False
            and row["nemo3_invoked"]
            and row.get("nemo3_role") == "confirmation_not_action_source"
            and row.get("nemo3_decision_delegated_to_nemo") is False
            and row.get("nemo3_final_confirmation")
            and not row["online_submission"]
            and not row["arc_solve_claim"]
        ),
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC-AGI-3 Standard Model Step Results",
        "",
        "Status: one actuator step driven by a validated Nemo3/world-model ModelDecision artifact.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- selected game: `{condition['selected_game']['game_id']}`",
        f"- model decision: `{condition['model_decision_artifact']}`",
        f"- standard model flow: `{condition['standard_model_flow']}`",
        f"- online submission: `{condition['online_submission']}`",
        f"- ARC solve claim: `{condition['arc_solve_claim']}`",
        "",
        "## Metrics",
        "",
        f"- valid standard model-flow step: `{metrics['valid_standard_model_flow_step']}`",
        f"- decision id: `{metrics['decision_id']}`",
        f"- observation content match: `{metrics['observation_content_match']}`",
        f"- observation GUID match: `{metrics['observation_guid_match']}`",
        f"- MLP consultation: `{metrics['mlp_consultation']}`",
        f"- internal forward rollout: `{metrics['internal_forward_rollout']}`",
        f"- solved before first step: `{metrics['internal_forward_rollout_solves_before_first_step']}`",
        f"- post-action MLP update: `{metrics['post_action_mlp_update_artifact']}`",
        f"- MLP weights updated: `{metrics['mlp_weights_updated']}`",
        f"- Nemo3 invoked: `{metrics['nemo3_invoked']}`",
        f"- action: `{metrics['chosen_action_name']}:{metrics['chosen_action_value']}`",
        f"- candidate action packets: `{metrics['candidate_action_packets']}`",
        f"- actuator steps executed: `{metrics['actuator_steps_executed']}`",
        f"- levels completed: `{metrics['levels_completed_start']} -> {metrics['levels_completed_final']}`",
        f"- final state: `{metrics['final_state']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--model-decision-artifact", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_agi3_model_step_v043_standard_flow")
    parser.add_argument("--operation-mode", choices=("OFFLINE",), default="OFFLINE")
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument("--post-action-mlp-update-mode", choices=("candidate-only",), default="candidate-only")
    parser.add_argument("--allow-unsolved-internal-rollout-for-contract-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "valid_standard_model_flow_step": metrics["valid_standard_model_flow_step"],
                "decision_id": metrics["decision_id"],
                "chosen_action": f"{metrics['chosen_action_name']}:{metrics['chosen_action_value']}",
                "levels_completed_delta": metrics["levels_completed_delta"],
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
