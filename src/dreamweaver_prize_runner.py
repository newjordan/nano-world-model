"""No-internet Dreamweaver ARC-AGI-3 prize-runner core.

This is the legal mechanics layer for a future Kaggle package. It owns scorecard
and environment iteration rules; it does not use the ONLINE scout mirror and it
does not permit source-environment solvers.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol

from arc_agi3_model_flow import (
    MODEL_DECISION_SCHEMA,
    STANDARD_MODEL_FLOW,
    actuator_reasoning_from_model_decision,
    require_standard_model_decision,
)


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_arc_agi3_model_decision_producer as producer  # noqa: E402
from scripts.run_arc_agi3_io_smoke import (  # noqa: E402
    DEFAULT_ARC_REPO,
    DEFAULT_ENVIRONMENTS_DIR,
    DEFAULT_SOURCE_CONDITION,
    _repo_rel,
    _sha256,
    action_by_value,
    action_name,
    action_value,
    action_values,
    candidate_action_packets,
    normalize_games,
    prepare_out_dir,
    state_name,
    summarize_frame_stack,
)
from scripts.run_arc_agi3_model_solve_scout import offline_solved, terminal_state  # noqa: E402


SCHEMA = "dreamweaver.arc_agi3_prize_runner.v001"
TRACE_SCHEMA = "dreamweaver.arc_agi3_prize_runner_trace_row.v001"
DEFAULT_MODEL_NAME = "Dreamweaver"


@dataclass(frozen=True)
class PrizeRunnerConfig:
    out_dir: Path
    run_label: str = "dreamweaver_arc_agi3_kaggle_prize_candidate"
    model_name: str = DEFAULT_MODEL_NAME
    operation_mode: str = "COMPETITION"
    source_url: str = "https://github.com/newjordan/nano-world-model"
    max_actions_per_environment: int = 80
    max_candidate_actions: int = 8
    seed: int = 0
    require_internal_solve: bool = False
    branch_ambiguity_gap_threshold: float = 0.0
    internal_rollout_max_steps: int = 32
    internal_rollout_kernel_timeout: int = 30
    arc_grid_agent_label: int | None = None
    arc_grid_goal_label: int | None = None
    arc_grid_wall_labels: str = ""
    arc_grid_hazard_labels: str = ""
    source_condition_artifact: Path = DEFAULT_SOURCE_CONDITION
    arc_repo: Path = DEFAULT_ARC_REPO
    environments_dir: Path = DEFAULT_ENVIRONMENTS_DIR


class DecisionSource(Protocol):
    def build_model_decision(
        self,
        *,
        env: Any,
        obs: Any,
        selected_game: dict[str, Any],
        games: list[dict[str, Any]],
        candidate_packets: list[dict[str, Any]],
        step_dir: Path,
        config: PrizeRunnerConfig,
        prior_post_action_mlp_updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return a standard ModelDecision artifact for the current observation."""


class ProducerDecisionSource:
    """Use the existing Dreamweaver ModelDecision producer in local-only mode."""

    def build_model_decision(
        self,
        *,
        env: Any,
        obs: Any,
        selected_game: dict[str, Any],
        games: list[dict[str, Any]],
        candidate_packets: list[dict[str, Any]],
        step_dir: Path,
        config: PrizeRunnerConfig,
        prior_post_action_mlp_updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        decision_args = SimpleNamespace(
            run_label=f"{config.run_label}_{selected_game['name']}_step_{step_dir.name}_decision",
            branch_ambiguity_gap_threshold=config.branch_ambiguity_gap_threshold,
            nemo_mode=producer.LOCAL_NEMO_MODE,
            nemo_model="dreamweaver-local-confirmation",
            nemo_relay_url="",
            nemo_timeout=0,
            internal_rollout_max_steps=config.internal_rollout_max_steps,
            internal_rollout_kernel_timeout=config.internal_rollout_kernel_timeout,
            arc_grid_agent_label=config.arc_grid_agent_label,
            arc_grid_goal_label=config.arc_grid_goal_label,
            arc_grid_wall_labels=config.arc_grid_wall_labels,
            arc_grid_hazard_labels=config.arc_grid_hazard_labels,
            allow_source_env_solver=False,
        )
        condition = {
            "schema": producer.SCHEMA,
            "run_label": decision_args.run_label,
            "run_kind": "dreamweaver_prize_runner_decision_step",
            "source_condition_artifact": str(config.source_condition_artifact),
            "source_condition_sha256": (
                _sha256(config.source_condition_artifact) if config.source_condition_artifact.exists() else None
            ),
            "dataset_path": str(config.environments_dir),
            "selected_game": selected_game,
            "operation_mode": config.operation_mode,
            "nemo_mode": producer.LOCAL_NEMO_MODE,
            "nemo_external_model_required": False,
            "allow_source_env_solver": False,
            "metric_to_compare": "valid_model_decision_before_prize_runner_action",
            "online_submission": False,
            "scorecard_submission": True,
            "arc_solve_claim": False,
        }
        producer.write_model_decision_artifacts(
            args=decision_args,
            out_dir=step_dir,
            games=games,
            selected_game=selected_game,
            env=env,
            reset_obs=obs,
            candidate_packets=candidate_packets,
            condition=condition,
            prior_post_action_mlp_updates=prior_post_action_mlp_updates,
        )
        return json.loads((step_dir / "model_decision.json").read_text(encoding="utf-8"))


def run_prize_candidate(
    *,
    arcade: Any,
    config: PrizeRunnerConfig,
    decision_source: DecisionSource | None = None,
) -> dict[str, Any]:
    """Run all available environments through the no-internet Dreamweaver loop."""

    if config.max_actions_per_environment < 1:
        raise ValueError("max_actions_per_environment must be at least 1")
    decision_source = decision_source or ProducerDecisionSource()
    out_dir = config.out_dir.resolve()
    prepare_out_dir(out_dir)
    (out_dir / "steps").mkdir(parents=True, exist_ok=True)

    games = normalize_games(arcade.get_environments())
    if not games:
        raise RuntimeError("no ARC-AGI-3 environments are available")

    scorecard_id = create_scorecard_once(arcade, config)
    make_calls: dict[str, int] = {}
    trace_rows: list[dict[str, Any]] = []
    prior_post_action_mlp_updates: list[dict[str, Any]] = []

    for selected_game in games:
        game_name = selected_game["name"]
        make_calls[game_name] = make_calls.get(game_name, 0) + 1
        if make_calls[game_name] > 1:
            raise RuntimeError(f"make called more than once for {game_name}")
        env = arcade.make(
            game_name,
            seed=config.seed,
            scorecard_id=scorecard_id,
            save_recording=False,
            include_frame_data=True,
        )
        if env is None:
            raise RuntimeError(f"Arcade.make({game_name!r}) returned None")
        obs = env.reset()
        if obs is None:
            raise RuntimeError(f"{game_name} reset returned None")

        for step_index in range(config.max_actions_per_environment):
            if offline_solved(obs):
                trace_rows.append(done_row(config, selected_game, scorecard_id, step_index, obs, "solved_before_step"))
                break
            if terminal_state(obs):
                trace_rows.append(done_row(config, selected_game, scorecard_id, step_index, obs, "terminal_before_step"))
                break
            packets = candidate_action_packets(
                env=env,
                game_name=game_name,
                observation_guid=str(getattr(obs, "guid", "")),
                phase=f"prize_candidate_step_{step_index}",
                max_actions=config.max_candidate_actions,
            )
            if not packets:
                trace_rows.append(done_row(config, selected_game, scorecard_id, step_index, obs, "no_available_actions"))
                break

            step_dir = out_dir / "steps" / f"{game_name}_{step_index:03d}"
            step_dir.mkdir(parents=True, exist_ok=False)
            model_decision = decision_source.build_model_decision(
                env=env,
                obs=obs,
                selected_game=selected_game,
                games=games,
                candidate_packets=packets,
                step_dir=step_dir,
                config=config,
                prior_post_action_mlp_updates=prior_post_action_mlp_updates,
            )
            selected_action = require_standard_model_decision(
                model_decision,
                available_action_values=action_values(getattr(env, "action_space", [])),
                require_internal_solve=config.require_internal_solve,
            )
            action = action_by_value(env.action_space, int(selected_action["action_value"]))
            action_data = selected_action.get("action_data")
            if action_requires_data(action) and not isinstance(action_data, dict):
                trace_rows.append(
                    done_row(
                        config,
                        selected_game,
                        scorecard_id,
                        step_index,
                        obs,
                        "missing_complex_action_data_before_step",
                    )
                )
                break
            reasoning = compact_prize_reasoning(
                config=config,
                scorecard_id=scorecard_id,
                selected_game=selected_game,
                step_index=step_index,
                model_decision=model_decision,
            )
            step_kwargs: dict[str, Any] = {"reasoning": reasoning}
            if action_data is not None:
                step_kwargs["data"] = action_data
            next_obs = env.step(action, **step_kwargs)
            if next_obs is None:
                trace_rows.append(done_row(config, selected_game, scorecard_id, step_index, obs, "env_step_returned_none"))
                break
            trace_rows.append(
                trace_row(
                    config=config,
                    scorecard_id=scorecard_id,
                    selected_game=selected_game,
                    step_index=step_index,
                    obs=obs,
                    next_obs=next_obs,
                    action=action,
                    action_data=action_data,
                    model_decision=model_decision,
                    step_dir=step_dir,
                )
            )
            obs = next_obs
        else:
            trace_rows.append(done_row(config, selected_game, scorecard_id, config.max_actions_per_environment, obs, "max_actions_exhausted"))

    scorecard = close_scorecard_once(arcade, scorecard_id)
    metrics = summarize_run(config, games, scorecard_id, trace_rows, make_calls, scorecard)
    write_json(out_dir / "condition.json", condition_payload(config, games, scorecard_id))
    write_json(out_dir / "metrics.json", metrics)
    write_json(out_dir / "scorecard_final.json", scorecard_payload(scorecard, scorecard_id))
    write_jsonl(out_dir / "trace.jsonl", trace_rows)
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def create_scorecard_once(arcade: Any, config: PrizeRunnerConfig) -> str:
    opaque = {
        "schema": "dreamweaver.arc_agi3_prize_runner_scorecard_opaque.v001",
        "model_name": config.model_name,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "internet_required": False,
        "external_confirmation_backend": False,
        "source_env_solver_allowed": False,
    }
    return str(arcade.create_scorecard(source_url=config.source_url, tags=[config.model_name, "kaggle-prize-candidate"], opaque=opaque))


def close_scorecard_once(arcade: Any, scorecard_id: str) -> Any | None:
    try:
        return arcade.close_scorecard(scorecard_id=scorecard_id)
    except TypeError:
        return arcade.close_scorecard(scorecard_id)


def action_requires_data(action: Any) -> bool:
    is_complex = getattr(action, "is_complex", None)
    if callable(is_complex):
        return bool(is_complex())
    return action_value(action) >= 5


def compact_prize_reasoning(
    *,
    config: PrizeRunnerConfig,
    scorecard_id: str,
    selected_game: dict[str, Any],
    step_index: int,
    model_decision: dict[str, Any],
) -> dict[str, Any]:
    reasoning = actuator_reasoning_from_model_decision(model_decision)
    return {
        "schema": "dreamweaver.arc_agi3_prize_action_reasoning.v001",
        "model_name": config.model_name,
        "run_label": config.run_label,
        "scorecard_id": scorecard_id,
        "game_name": selected_game["name"],
        "step_index": step_index,
        "policy": "local_3d_world_model_internal_lock_then_local_confirmation",
        "decision_id": model_decision.get("decision_id"),
        "state_id": model_decision.get("state_id"),
        "selected_action": model_decision.get("selected_action"),
        "internal_forward_rollout": reasoning.get("internal_forward_rollout"),
        "internal_forward_rollout_sha256": reasoning.get("internal_forward_rollout_sha256"),
        "nemo3_final_confirmation": reasoning.get("nemo3_final_confirmation"),
        "nemo3_final_confirmation_sha256": reasoning.get("nemo3_final_confirmation_sha256"),
        "external_api_used": False,
        "source_env_solver_used": False,
        "offline_mirror_used": False,
        "arc_solve_claim": False,
    }


def trace_row(
    *,
    config: PrizeRunnerConfig,
    scorecard_id: str,
    selected_game: dict[str, Any],
    step_index: int,
    obs: Any,
    next_obs: Any,
    action: Any,
    action_data: Any,
    model_decision: dict[str, Any],
    step_dir: Path,
) -> dict[str, Any]:
    return {
        "schema": TRACE_SCHEMA,
        "run_label": config.run_label,
        "scorecard_id": scorecard_id,
        "game_name": selected_game["name"],
        "game_id": selected_game["game_id"],
        "step_index": step_index,
        "phase": "post_action",
        "state_start": state_name(getattr(obs, "state", None)),
        "state_final": state_name(getattr(next_obs, "state", None)),
        "levels_completed_start": int(getattr(obs, "levels_completed", 0)),
        "levels_completed_final": int(getattr(next_obs, "levels_completed", 0)),
        "win_levels": int(getattr(next_obs, "win_levels", 0)),
        "action": f"{action_name(action)}:{action_value(action)}",
        "action_data": action_data,
        "frame_sha256": summarize_frame_stack(getattr(obs, "frame", None))["latest_frame_sha256"],
        "next_frame_sha256": summarize_frame_stack(getattr(next_obs, "frame", None))["latest_frame_sha256"],
        "model_decision_schema": model_decision.get("schema"),
        "model_decision_artifact": _repo_rel(step_dir / "model_decision.json"),
        "selected_action_source": (model_decision.get("selected_action") or {}).get("source"),
        "nemo3_confirmation_mode": (model_decision.get("nemo3") or {}).get("confirmation_mode"),
        "nemo3_external_model_invoked": (model_decision.get("nemo3") or {}).get("external_nemo3_model_invoked"),
        "external_api_used": False,
        "source_env_solver_used": False,
        "offline_mirror_used": False,
        "scorecard_submission": True,
        "arc_solve_claim": False,
    }


def done_row(
    config: PrizeRunnerConfig,
    selected_game: dict[str, Any],
    scorecard_id: str,
    step_index: int,
    obs: Any,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema": TRACE_SCHEMA,
        "run_label": config.run_label,
        "scorecard_id": scorecard_id,
        "game_name": selected_game["name"],
        "game_id": selected_game["game_id"],
        "step_index": step_index,
        "phase": "done",
        "stop_reason": reason,
        "state_final": state_name(getattr(obs, "state", None)),
        "levels_completed_final": int(getattr(obs, "levels_completed", 0)),
        "win_levels": int(getattr(obs, "win_levels", 0)),
        "external_api_used": False,
        "source_env_solver_used": False,
        "offline_mirror_used": False,
        "scorecard_submission": True,
        "arc_solve_claim": False,
    }


def condition_payload(config: PrizeRunnerConfig, games: list[dict[str, Any]], scorecard_id: str) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "created_at_utc": now_iso(),
        "model_name": config.model_name,
        "run_label": config.run_label,
        "script": _repo_rel(script_path),
        "script_sha256": _sha256(script_path),
        "operation_mode": config.operation_mode,
        "internet_allowed": False,
        "confirmation_backend_kind": producer.LOCAL_NEMO_MODE,
        "nemo_external_model_required": False,
        "uses_offline_mirror": False,
        "uses_source_env_solver": False,
        "single_scorecard": True,
        "all_environment_runner": True,
        "one_make_per_environment": True,
        "scorecard_reads_during_run": False,
        "scorecard_id": scorecard_id,
        "available_game_count": len(games),
        "available_games": games,
        "max_actions_per_environment": config.max_actions_per_environment,
        "require_internal_solve": config.require_internal_solve,
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "source_condition_artifact": str(config.source_condition_artifact),
        "source_condition_sha256": _sha256(config.source_condition_artifact) if config.source_condition_artifact.exists() else None,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": config.seed,
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": f"max_actions_per_environment={config.max_actions_per_environment}",
        "loader_mode": "arc_agi_competition_all_environments_one_make_each",
        "quantization_policy": "none",
        "compile_kernel_policy": "dream_kernel_arc_grid_scout_no_source_env_solver",
        "metric_to_compare": "competition_scorecard_all_environment_completion_and_efficiency",
        "historical_comparator": "dreamweaver_online_scorecard_v001_ls20_not_prize_claim",
        "historical_comparator_artifact": "packages/dreamweaver_scorecard_v001_ls20/competition_preflight_manifest.json",
        "secret_sources": [],
        "arc_solve_claim": False,
    }


def summarize_run(
    config: PrizeRunnerConfig,
    games: list[dict[str, Any]],
    scorecard_id: str,
    trace_rows: list[dict[str, Any]],
    make_calls: dict[str, int],
    scorecard: Any | None,
) -> dict[str, Any]:
    action_rows = [row for row in trace_rows if row.get("phase") == "post_action"]
    return {
        "schema": SCHEMA,
        "created_at_utc": now_iso(),
        "model_name": config.model_name,
        "run_label": config.run_label,
        "scorecard_id": scorecard_id,
        "available_game_count": len(games),
        "games_attempted": sorted(make_calls),
        "all_environment_runner": sorted(make_calls) == sorted(game["name"] for game in games),
        "one_make_per_environment": all(count == 1 for count in make_calls.values()),
        "single_scorecard": True,
        "scorecard_reads_during_run": False,
        "online_submission": False,
        "scorecard_submission": True,
        "competition_mode": config.operation_mode == "COMPETITION",
        "internet_allowed": False,
        "external_api_used": False,
        "offline_mirror_used": False,
        "source_env_solver_used": False,
        "nemo3_external_model_invocations": sum(1 for row in action_rows if row.get("nemo3_external_model_invoked") is True),
        "actions_executed": len(action_rows),
        "trace_rows": len(trace_rows),
        "scorecard_final_available": scorecard is not None,
        "arc_solve_claim": False,
        "kaggle_prize_eligible_mechanics": bool(
            sorted(make_calls) == sorted(game["name"] for game in games)
            and all(count == 1 for count in make_calls.values())
        ),
    }


def scorecard_payload(scorecard: Any | None, scorecard_id: str) -> dict[str, Any]:
    if scorecard is None:
        return {"scorecard_id": scorecard_id, "available": False}
    if hasattr(scorecard, "model_dump"):
        payload = scorecard.model_dump(mode="json")
    elif isinstance(scorecard, dict):
        payload = dict(scorecard)
    else:
        payload = {"repr": repr(scorecard)}
    payload["scorecard_id"] = scorecard_id
    if "api_key" in payload:
        payload["api_key"] = "REDACTED"
    return payload


def format_results(metrics: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Dreamweaver ARC-AGI-3 Prize Runner Results",
            "",
            f"- model: `{metrics['model_name']}`",
            f"- scorecard id: `{metrics['scorecard_id']}`",
            f"- available games: `{metrics['available_game_count']}`",
            f"- actions executed: `{metrics['actions_executed']}`",
            f"- all environments attempted: `{metrics['all_environment_runner']}`",
            f"- one make per environment: `{metrics['one_make_per_environment']}`",
            f"- external API used: `{metrics['external_api_used']}`",
            f"- source-env solver used: `{metrics['source_env_solver_used']}`",
            f"- offline mirror used: `{metrics['offline_mirror_used']}`",
            "",
        ]
    )


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
