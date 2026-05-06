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
    INTERNAL_THINKING_LOCK_SCHEMA,
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
    selected_action = require_standard_model_decision(model_decision, available_action_values=available_values)
    action = action_by_value(env.action_space, int(selected_action["action_value"]))
    action_data = selected_action.get("action_data")
    before_summary = summarize_frame_stack(getattr(obs, "frame", None))
    reasoning = actuator_reasoning_from_model_decision(model_decision)
    reasoning["run_label"] = args.run_label

    step_kwargs: dict[str, Any] = {"reasoning": reasoning}
    if action_data is not None:
        step_kwargs["data"] = action_data
    next_obs = env.step(action, **step_kwargs)
    if next_obs is None:
        raise RuntimeError(f"env.step returned None after {action_name(action)}")

    next_summary = summarize_frame_stack(getattr(next_obs, "frame", None))
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
        "state_id": model_decision.get("state_id"),
        "candidate_action_packets": len(candidate_packets),
        "actuator_steps_executed": len(trace_rows),
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
        "valid_standard_model_flow_step": bool(
            len(trace_rows) == 1
            and model_decision.get("schema") == MODEL_DECISION_SCHEMA
            and row["chosen_action_value"] in row["available_action_values"]
            and row.get("selected_action_source") == SELECTED_ACTION_SOURCE
            and row.get("chronometric_game_knowledge")
            and row.get("chronometric_game_knowledge_score_surface") == CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE
            and row.get("chronometric_game_knowledge_action_embedding_linked") is True
            and row.get("chronometric_game_knowledge_branch_library_linked") is True
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
