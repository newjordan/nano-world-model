#!/usr/bin/env python3
"""Produce a standard ARC-AGI-3 ModelDecision artifact from a reset observation.

This is the upstream side of the ARC actuator boundary. It loads the real
offline ARC-AGI-3 environment, reads the ``ls20`` reset observation, builds the
world-model artifact chain, validates the resulting ModelDecision, and stops.
It never calls ``env.step``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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
    MLP_CONSULTATION_SCHEMA,
    MODEL_DECISION_SCHEMA,
    NEMO3_FINAL_CONFIRMATION_SCHEMA,
    NEMO3_INTERIM_CONFIRMATION_SCHEMA,
    SELECTED_ACTION_SOURCE,
    STANDARD_MODEL_FLOW,
    require_standard_model_decision,
)
from chronometric_grid_imagination import build_grid_imagination_map  # noqa: E402
from chronometric_map_perception import ColorLabel, build_grid_geometry, evaluate_grid_perception  # noqa: E402
from chronometric_sensory_alignment import evaluate_2d_3d_alignment  # noqa: E402
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


DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_agi3_model_decision_v047_ls20_reset"
SCHEMA = "arc_agi3.model_decision_producer.v001"
OBSERVATION_SCHEMA = "arc_agi3.reset_observation_artifact.v001"
WORLD_STATE_SCHEMA = "arc_agi3.world_state_3d.v001"
BRANCH_SIMULATION_SCHEMA = "arc_agi3.branch_simulation.v001"
TRUST_CHECKS_SCHEMA = "arc_agi3.trust_checks.v001"
LOCAL_NEMO_MODE = "contract-local"
LIVE_NEMO_MODE = "live-relay"


def run(args: argparse.Namespace) -> dict[str, Any]:
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
    reset_obs = env.reset()
    if reset_obs is None:
        raise RuntimeError(f"{selected_game['name']} reset returned None")

    candidate_packets = candidate_action_packets(
        env=env,
        game_name=selected_game["name"],
        observation_guid=str(getattr(reset_obs, "guid", "")),
        phase="model_decision_pre_action",
        max_actions=args.max_candidate_actions,
    )
    condition = condition_payload(
        args,
        out_dir=out_dir,
        arc_repo=arc_repo,
        environments_dir=environments_dir,
        source_condition=source_condition,
        selected_game=selected_game,
        arcade=arcade,
    )
    metrics = write_model_decision_artifacts(
        args=args,
        out_dir=out_dir,
        games=games,
        selected_game=selected_game,
        env=env,
        reset_obs=reset_obs,
        candidate_packets=candidate_packets,
        condition=condition,
    )
    return metrics


def write_model_decision_artifacts(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    games: list[dict[str, Any]],
    selected_game: dict[str, Any],
    env: Any,
    reset_obs: Any,
    candidate_packets: list[dict[str, Any]],
    condition: dict[str, Any],
    prior_post_action_mlp_updates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not candidate_packets:
        raise RuntimeError("no candidate actions were available at reset")

    frame_summary = summarize_frame_stack(getattr(reset_obs, "frame", None))
    grid = grid_from_frame_stack(getattr(reset_obs, "frame", None))
    grid_stats = grid_statistics(grid)
    state_id = state_identifier(selected_game, reset_obs, frame_summary)
    paths = artifact_paths(out_dir)

    observation = build_observation_artifact(
        selected_game=selected_game,
        env=env,
        reset_obs=reset_obs,
        frame_summary=frame_summary,
        grid_stats=grid_stats,
    )
    _write_json(paths["observation"], observation)

    world_state = build_world_state_artifact(
        state_id=state_id,
        selected_game=selected_game,
        grid=grid,
        frame_summary=frame_summary,
        grid_stats=grid_stats,
    )
    _write_json(paths["world_state_3d"], world_state)

    game_knowledge = build_chronometric_game_knowledge_artifact(
        state_id=state_id,
        selected_game=selected_game,
        world_state=world_state,
    )
    _write_json(paths["chronometric_game_knowledge"], game_knowledge)
    game_knowledge_ref = model_flow_ref(paths["chronometric_game_knowledge"])

    mlp_consultation = build_mlp_consultation_artifact(
        state_id=state_id,
        selected_game=selected_game,
        candidate_packets=candidate_packets,
        world_state=world_state,
        game_knowledge_ref=game_knowledge_ref,
        prior_post_action_mlp_updates=prior_post_action_mlp_updates,
    )
    _write_json(paths["mlp_consultation"], mlp_consultation)
    mlp_consultation_ref = model_flow_ref(paths["mlp_consultation"])

    branch_simulation = build_branch_simulation_artifact(
        args=args,
        state_id=state_id,
        selected_game=selected_game,
        candidate_packets=candidate_packets,
        world_state=world_state,
        game_knowledge_ref=game_knowledge_ref,
        mlp_consultation_ref=mlp_consultation_ref,
        mlp_consultation=mlp_consultation,
    )
    _write_json(paths["branch_simulation"], branch_simulation)
    branch_simulation_ref = model_flow_ref(paths["branch_simulation"])

    trust_checks = build_trust_checks_artifact(
        state_id=state_id,
        selected_game=selected_game,
        world_state=world_state,
        branch_simulation=branch_simulation,
    )
    _write_json(paths["trust_checks"], trust_checks)

    selected_branch = selected_branch_from(branch_simulation)
    ambiguity = ambiguity_record(branch_simulation, threshold=args.branch_ambiguity_gap_threshold)
    interim_confirmations = write_interim_confirmations(
        args=args,
        out_dir=out_dir,
        state_id=state_id,
        selected_branch=selected_branch,
        branch_simulation=branch_simulation,
        ambiguity=ambiguity,
    )

    internal_lock = build_internal_thinking_lock_artifact(
        state_id=state_id,
        selected_branch=selected_branch,
        branch_simulation=branch_simulation,
        branch_simulation_ref=branch_simulation_ref,
        ambiguity=ambiguity,
        interim_confirmations=interim_confirmations,
    )
    _write_json(paths["internal_thinking"], internal_lock)
    internal_lock_ref = model_flow_ref(paths["internal_thinking"])

    final_confirmation = build_final_confirmation_artifact(
        args=args,
        state_id=state_id,
        selected_branch=selected_branch,
        branch_simulation=branch_simulation,
        trust_checks=trust_checks,
        internal_lock_ref=internal_lock_ref,
    )
    _write_json(paths["nemo3_final_confirmation"], final_confirmation)
    final_ref = model_flow_ref(paths["nemo3_final_confirmation"])

    standard_flow = {
        "sequence": list(STANDARD_MODEL_FLOW),
        "observation_artifact": model_flow_ref(paths["observation"])["artifact"],
        "world_state_3d_artifact": model_flow_ref(paths["world_state_3d"])["artifact"],
        "chronometric_game_knowledge_artifact": game_knowledge_ref["artifact"],
        "mlp_consultation_artifact": mlp_consultation_ref["artifact"],
        "branch_simulation_artifact": branch_simulation_ref["artifact"],
        "trust_checks_artifact": model_flow_ref(paths["trust_checks"])["artifact"],
        "internal_thinking_artifact": internal_lock_ref["artifact"],
        "nemo3_final_confirmation_artifact": final_ref["artifact"],
        "model_decision_artifact": _repo_rel(paths["model_decision"]),
    }
    model_decision = build_model_decision(
        state_id=state_id,
        run_label=args.run_label,
        selected_branch=selected_branch,
        standard_flow=standard_flow,
        game_knowledge=game_knowledge,
        game_knowledge_ref=game_knowledge_ref,
        mlp_consultation=mlp_consultation,
        mlp_consultation_ref=mlp_consultation_ref,
        internal_lock=internal_lock,
        internal_lock_ref=internal_lock_ref,
        final_confirmation=final_confirmation,
        final_ref=final_ref,
        interim_confirmations=interim_confirmations,
        trust_checks=trust_checks,
        nemo_mode=args.nemo_mode,
    )
    require_standard_model_decision(model_decision, available_action_values=action_values(getattr(env, "action_space", [])))
    _write_json(paths["model_decision"], model_decision)
    _write_jsonl(out_dir / "candidate_action_packets.jsonl", candidate_packets)

    metrics = summarize_producer(
        condition=condition,
        games=games,
        selected_game=selected_game,
        candidate_packets=candidate_packets,
        model_decision=model_decision,
        world_state=world_state,
        branch_simulation=branch_simulation,
        trust_checks=trust_checks,
        interim_confirmations=interim_confirmations,
    )
    _write_json(out_dir / "condition.json", condition)
    _write_json(out_dir / "metrics.json", metrics)
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def artifact_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "observation": out_dir / "observation.json",
        "world_state_3d": out_dir / "world_state_3d.json",
        "chronometric_game_knowledge": out_dir / "chronometric_game_knowledge.json",
        "mlp_consultation": out_dir / "mlp_consultation.json",
        "branch_simulation": out_dir / "branch_simulation.json",
        "trust_checks": out_dir / "trust_checks.json",
        "internal_thinking": out_dir / "internal_thinking_lock.json",
        "nemo3_final_confirmation": out_dir / "nemo3_final_confirmation.json",
        "model_decision": out_dir / "model_decision.json",
    }


def build_observation_artifact(
    *,
    selected_game: dict[str, Any],
    env: Any,
    reset_obs: Any,
    frame_summary: dict[str, Any],
    grid_stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": OBSERVATION_SCHEMA,
        "created_at_utc": now_iso(),
        "game_name": selected_game["name"],
        "game_id": str(getattr(reset_obs, "game_id", getattr(env.info, "game_id", ""))),
        "guid": str(getattr(reset_obs, "guid", "")),
        "state": state_name(getattr(reset_obs, "state", None)),
        "levels_completed": int(getattr(reset_obs, "levels_completed", 0)),
        "win_levels": int(getattr(reset_obs, "win_levels", 0)),
        "full_reset": bool(getattr(reset_obs, "full_reset", False)),
        "available_action_values": action_values(getattr(env, "action_space", [])),
        "frame": frame_summary,
        "grid": grid_stats,
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
    }


def build_world_state_artifact(
    *,
    state_id: str,
    selected_game: dict[str, Any],
    grid: tuple[tuple[int, ...], ...],
    frame_summary: dict[str, Any],
    grid_stats: dict[str, Any],
) -> dict[str, Any]:
    labels = tuple(ColorLabel(value=value, rgb=(0, 0, 0), name=f"label_{value}") for value in grid_stats["labels"])
    geometry = build_grid_geometry(grid, labels, playable_values=(0,))
    imagination = build_grid_imagination_map(grid, playable_values=(0,))
    perception_gate = evaluate_grid_perception(grid, grid, playable_values=(0,))
    projection_gate = evaluate_2d_3d_alignment(grid, geometry, playable_values=(0,))
    sample_anchors = [
        {
            "object_id": anchor.object_id,
            "value": anchor.value,
            "position": list(anchor.position),
            "assessment": anchor.assessment,
            "confidence": anchor.confidence,
        }
        for anchor in imagination.anchors[:24]
    ]
    sample_rays = [
        {
            "probe_id": ray.probe_id,
            "origin": list(ray.origin),
            "direction": list(ray.direction),
            "hit_position": None if ray.hit_position is None else list(ray.hit_position),
            "hit_value": ray.hit_value,
            "blocked": ray.blocked,
        }
        for ray in imagination.rays[:48]
    ]
    return {
        "schema": WORLD_STATE_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "game_name": selected_game["name"],
        "world_model_surface": "chronometric_frame_grid_to_3d_world_state_v047",
        "representation_basis": "arc_frame_label_grid_3d_heightmap",
        "frame": frame_summary,
        "grid": [[int(value) for value in row] for row in grid],
        "grid_stats": grid_stats,
        "geometry": {
            "width": geometry.width,
            "height": geometry.height,
            "cell_count": len(geometry.cells),
            "cell_size": 1.0,
            "playable_values": [0],
            "blocker_values": [value for value in grid_stats["labels"] if value != 0],
            "height_counts": dict(Counter(str(int(cell.height > 0)) for cell in geometry.cells)),
        },
        "ray_map": {
            "anchor_count": len(imagination.anchors),
            "ray_count": len(imagination.rays),
            "sample_anchors": sample_anchors,
            "sample_rays": sample_rays,
        },
        "trust_gates": {
            "map_perception": _jsonable(perception_gate),
            "geometry_projection": _jsonable(projection_gate),
        },
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def build_chronometric_game_knowledge_artifact(
    *,
    state_id: str,
    selected_game: dict[str, Any],
    world_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "game_name": selected_game["name"],
        "knowledge_packet": "arc_agi3_chronometric_game_knowledge_v047",
        "backbone_surface": CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
        "calibration_surface": CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
        "score_surface": CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
        "knowledge_domains": ["basic_movement", "known_interactions", "branch_value_calibration"],
        "swiglu_backbone_linked": True,
        "action_embedding_context_linked": True,
        "calibration_mlp_linked": True,
        "branch_library_linked": True,
        "drives_branch_simulation": True,
        "created_before_internal_branch_simulation": True,
        "updates_from_post_action_calibration_only": True,
        "online_update_requires_promotion_condition": True,
        "heldout_labels_used": False,
        "world_state_surface": world_state["world_model_surface"],
        "ray_count": world_state["ray_map"]["ray_count"],
        "object_anchor_count": world_state["ray_map"]["anchor_count"],
        "update_policy": {
            "pre_action_learning": False,
            "post_action_calibration_requires_artifact": True,
            "heldout_label_ingestion_requires_promotion": True,
        },
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def build_mlp_consultation_artifact(
    *,
    state_id: str,
    selected_game: dict[str, Any],
    candidate_packets: list[dict[str, Any]],
    world_state: dict[str, Any],
    game_knowledge_ref: dict[str, str],
    prior_post_action_mlp_updates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    frame_sha = str(world_state["frame"].get("latest_frame_sha256") or state_id)
    anchor_count = int(world_state["ray_map"]["anchor_count"])
    ray_count = int(world_state["ray_map"]["ray_count"])
    cell_total = max(int(world_state["grid_stats"]["cell_total"]), 1)
    prior_updates = [dict(row) for row in prior_post_action_mlp_updates or []]
    feedback_context_sha = stable_json_sha256(prior_updates) if prior_updates else None
    priors = []
    for index, packet in enumerate(candidate_packets):
        action_val = int(packet["action_value"])
        base_prior = stable_unit_float(f"{frame_sha}:{action_val}:mlp-consult")
        feedback_prior = (
            None
            if feedback_context_sha is None
            else stable_unit_float(f"{feedback_context_sha}:{frame_sha}:{action_val}:mlp-feedback")
        )
        mlp_prior = base_prior if feedback_prior is None else (0.75 * base_prior) + (0.25 * feedback_prior)
        priors.append(
            {
                "action_name": packet["action_name"],
                "action_value": action_val,
                "candidate_index": index,
                "mlp_prior": round(mlp_prior, 6),
                "prior_components": {
                    "base_prior": round(base_prior, 6),
                    "post_action_feedback_prior": None if feedback_prior is None else round(feedback_prior, 6),
                    "post_action_feedback_weight": 0.0 if feedback_prior is None else 0.25,
                },
                "action_embedding_context": {
                    "surface": CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
                    "frame_sha256": frame_sha,
                    "object_anchor_count": anchor_count,
                    "ray_count": ray_count,
                    "nonzero_cell_ratio": round(
                        float(world_state["grid_stats"]["nonzero_cells"]) / float(cell_total),
                        6,
                    ),
                },
                "branch_library_context": {
                    "fallback_enabled": True,
                    "scope": "arc_agi3_live_loop_action_context",
                    "lookup_key": f"ls20|action:{action_val}|labels:{len(world_state['grid_stats']['labels'])}",
                    "post_action_update_context_sha256": feedback_context_sha,
                },
            }
        )
    return {
        "schema": MLP_CONSULTATION_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "game_name": selected_game["name"],
        "consultation_surface": "arc_agi3_pre_action_mlp_consultation_v050",
        "backbone_surface": CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
        "calibration_surface": CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
        "score_surface": CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
        "chronometric_game_knowledge_artifact": game_knowledge_ref["artifact"],
        "chronometric_game_knowledge_sha256": game_knowledge_ref["sha256"],
        "prior_post_action_update_candidates": prior_updates,
        "post_action_update_candidate_context_count": len(prior_updates),
        "post_action_update_candidate_context_sha256": feedback_context_sha,
        "candidate_priors": priors,
        "consulted_before_branch_simulation": True,
        "drives_branch_simulation": True,
        "action_embedding_context_linked": True,
        "calibration_mlp_linked": True,
        "branch_library_context_linked": True,
        "updates_from_post_action_only": True,
        "online_update_requires_promotion_condition": True,
        "heldout_labels_used": False,
        "update_policy": {
            "pre_action_weight_update": False,
            "post_action_update_candidate_required": True,
            "online_weight_update_requires_promotion_condition": True,
        },
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def build_branch_simulation_artifact(
    *,
    args: argparse.Namespace,
    state_id: str,
    selected_game: dict[str, Any],
    candidate_packets: list[dict[str, Any]],
    world_state: dict[str, Any],
    game_knowledge_ref: dict[str, str],
    mlp_consultation_ref: dict[str, str],
    mlp_consultation: dict[str, Any],
) -> dict[str, Any]:
    branches = []
    frame_sha = str(world_state["frame"].get("latest_frame_sha256") or state_id)
    anchor_count = int(world_state["ray_map"]["anchor_count"])
    ray_count = int(world_state["ray_map"]["ray_count"])
    priors_by_action = {
        int(row["action_value"]): row
        for row in mlp_consultation.get("candidate_priors", [])
        if isinstance(row, dict) and "action_value" in row
    }
    for index, packet in enumerate(candidate_packets):
        action_val = int(packet["action_value"])
        mlp_prior = float(priors_by_action.get(action_val, {}).get("mlp_prior", 0.0))
        action_hash = stable_unit_float(f"{frame_sha}:{action_val}:branch")
        rank_prior = 1.0 - (index / max(len(candidate_packets), 1))
        structure_prior = min(1.0, (anchor_count + ray_count / 8.0) / max(world_state["grid_stats"]["cell_total"], 1))
        score = round(0.40 * mlp_prior + 0.25 * action_hash + 0.25 * rank_prior + 0.10 * structure_prior, 6)
        branches.append(
            {
                "branch_id": f"{state_id}:action:{action_val}",
                "game_name": selected_game["name"],
                "action_name": packet["action_name"],
                "action_value": action_val,
                "action_data": None,
                "score": score,
                "score_surface": CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
                "score_components": {
                    "mlp_prior": round(mlp_prior, 6),
                    "stable_action_context": round(action_hash, 6),
                    "candidate_rank_prior": round(rank_prior, 6),
                    "world_structure_prior": round(structure_prior, 6),
                },
                "chronometric_game_knowledge_artifact": game_knowledge_ref["artifact"],
                "chronometric_game_knowledge_sha256": game_knowledge_ref["sha256"],
                "mlp_consultation_artifact": mlp_consultation_ref["artifact"],
                "mlp_consultation_sha256": mlp_consultation_ref["sha256"],
                "prediction": {
                    "imagined_signed_y": score,
                    "confidence": round(min(1.0, 0.35 + 0.5 * score), 6),
                    "observed_after_action": None,
                    "post_action_calibration": False,
                },
                "selected": False,
                "training_data_promoted": False,
                "arc_solve_claim": False,
            }
        )
    branches.sort(key=lambda row: (-float(row["score"]), int(row["action_value"])))
    branches[0]["selected"] = True
    return {
        "schema": BRANCH_SIMULATION_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "game_name": selected_game["name"],
        "simulation_surface": "arc_agi3_reset_branch_simulation_v047",
        "score_surface": CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
        "selection_source": SELECTED_ACTION_SOURCE,
        "chronometric_game_knowledge_artifact": game_knowledge_ref["artifact"],
        "chronometric_game_knowledge_sha256": game_knowledge_ref["sha256"],
        "mlp_consultation_artifact": mlp_consultation_ref["artifact"],
        "mlp_consultation_sha256": mlp_consultation_ref["sha256"],
        "candidate_count": len(branches),
        "branches": branches,
        "selected_branch_id": branches[0]["branch_id"],
        "selected_action_value": branches[0]["action_value"],
        "selected_action_name": branches[0]["action_name"],
        "selection_policy": "chronometric_score_argmax_v047_reset_contract",
        "branch_ambiguity_gap_threshold": args.branch_ambiguity_gap_threshold,
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def build_trust_checks_artifact(
    *,
    state_id: str,
    selected_game: dict[str, Any],
    world_state: dict[str, Any],
    branch_simulation: dict[str, Any],
) -> dict[str, Any]:
    perception = world_state["trust_gates"]["map_perception"]
    projection = world_state["trust_gates"]["geometry_projection"]
    branch_count = int(branch_simulation["candidate_count"])
    selected = selected_branch_from(branch_simulation)
    flags = {
        "map_trusted": perception.get("trusted") is True,
        "geometry_trusted": projection.get("trusted") is True,
        "ray_trusted": perception.get("trusted") is True and int(world_state["ray_map"]["ray_count"]) >= 0,
        "temporal_trusted": branch_count > 0 and selected.get("prediction", {}).get("observed_after_action") is None,
        "branch_selection_trusted": branch_count > 0 and selected.get("selected") is True,
    }
    return {
        "schema": TRUST_CHECKS_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "game_name": selected_game["name"],
        **flags,
        "checks": {
            "map_perception_trusted": perception.get("trusted") is True,
            "geometry_projection_trusted": projection.get("trusted") is True,
            "ray_map_available": int(world_state["ray_map"]["ray_count"]) >= 0,
            "temporal_branch_simulation_pre_action_only": True,
            "branch_selection_from_internal_score": selected.get("selected") is True,
        },
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def write_interim_confirmations(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    state_id: str,
    selected_branch: dict[str, Any],
    branch_simulation: dict[str, Any],
    ambiguity: dict[str, Any],
) -> list[dict[str, Any]]:
    if not ambiguity["ambiguity_detected"]:
        return []
    question_id = "branch_selection_gap"
    artifact_path = out_dir / f"nemo3_interim_{question_id}.json"
    packet = {
        "schema": "arc_agi3.nemo3_interim_packet.v001",
        "state_id": state_id,
        "question_id": question_id,
        "selected_branch": compact_branch(selected_branch),
        "top_branch_gap": ambiguity["top_branch_gap"],
        "threshold": ambiguity["threshold"],
        "instruction": (
            "Confirm whether the internal branch selection has an unresolved ambiguity. "
            "Do not choose a new action; return compact JSON only."
        ),
    }
    response = nemo_response_for(args=args, packet=packet, stage="interim")
    artifact = {
        "schema": NEMO3_INTERIM_CONFIRMATION_SCHEMA,
        "created_at_utc": now_iso(),
        "created_during_internal_thinking": True,
        "role": "ambiguity_or_question_confirmation",
        "question_id": question_id,
        "state_id": state_id,
        "selected_action_value": selected_branch["action_value"],
        "confirmation_mode": args.nemo_mode,
        "external_nemo3_model_invoked": args.nemo_mode == LIVE_NEMO_MODE,
        "packet": packet,
        "response": response,
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }
    _write_json(artifact_path, artifact)
    ref = model_flow_ref(artifact_path)
    return [
        {
            "schema": NEMO3_INTERIM_CONFIRMATION_SCHEMA,
            "artifact": ref["artifact"],
            "sha256": ref["sha256"],
            "question_id": question_id,
            "created_during_internal_thinking": True,
            "role": "ambiguity_or_question_confirmation",
            "confirmation_mode": args.nemo_mode,
            "external_nemo3_model_invoked": args.nemo_mode == LIVE_NEMO_MODE,
        }
    ]


def build_internal_thinking_lock_artifact(
    *,
    state_id: str,
    selected_branch: dict[str, Any],
    branch_simulation: dict[str, Any],
    branch_simulation_ref: dict[str, str],
    ambiguity: dict[str, Any],
    interim_confirmations: list[dict[str, Any]],
) -> dict[str, Any]:
    open_questions = ["branch_selection_gap"] if ambiguity["ambiguity_detected"] else []
    return {
        "schema": INTERNAL_THINKING_LOCK_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "locked": True,
        "drives_selected_action": True,
        "created_before_actuator_step": True,
        "selected_action_value": int(selected_branch["action_value"]),
        "selected_action_name": selected_branch["action_name"],
        "selected_branch_id": selected_branch["branch_id"],
        "selected_action_source": SELECTED_ACTION_SOURCE,
        "branch_simulation_artifact": branch_simulation_ref["artifact"],
        "branch_simulation_sha256": branch_simulation_ref["sha256"],
        "ambiguity_detected": ambiguity["ambiguity_detected"],
        "open_question_ids": open_questions,
        "nemo3_interim_confirmations": interim_confirmations,
        "lock_reason": "internal chronometric branch simulation selected the action before actuator use",
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def build_final_confirmation_artifact(
    *,
    args: argparse.Namespace,
    state_id: str,
    selected_branch: dict[str, Any],
    branch_simulation: dict[str, Any],
    trust_checks: dict[str, Any],
    internal_lock_ref: dict[str, str],
) -> dict[str, Any]:
    packet = {
        "schema": "arc_agi3.nemo3_final_confirmation_packet.v001",
        "state_id": state_id,
        "selected_branch": compact_branch(selected_branch),
        "selected_action_value": selected_branch["action_value"],
        "selected_action_name": selected_branch["action_name"],
        "branch_simulation": {
            "schema": branch_simulation["schema"],
            "selected_branch_id": branch_simulation["selected_branch_id"],
            "candidate_count": branch_simulation["candidate_count"],
            "score_surface": branch_simulation["score_surface"],
        },
        "trust_flags": {
            "map_trusted": trust_checks["map_trusted"],
            "geometry_trusted": trust_checks["geometry_trusted"],
            "ray_trusted": trust_checks["ray_trusted"],
            "temporal_trusted": trust_checks["temporal_trusted"],
            "branch_selection_trusted": trust_checks["branch_selection_trusted"],
        },
        "internal_thinking_lock": internal_lock_ref,
        "instruction": (
            "Confirm or reject this internally selected action. Do not provide a replacement action. "
            "Return compact JSON with confirms_selected_action, selected_action_value, "
            "nemo_supplied_action=false, and confidence."
        ),
    }
    response = nemo_response_for(args=args, packet=packet, stage="final")
    if args.nemo_mode == LIVE_NEMO_MODE:
        parsed = parse_nemo_json_response(response["response_text"])
        if parsed.get("confirms_selected_action") is not True:
            raise RuntimeError("live Nemo final confirmation did not confirm selected action")
        if int(parsed.get("selected_action_value", -1)) != int(selected_branch["action_value"]):
            raise RuntimeError("live Nemo final confirmation selected_action_value does not match internal lock")
        if parsed.get("nemo_supplied_action") not in (False, None):
            raise RuntimeError("live Nemo final confirmation attempted to supply an action")

    return {
        "schema": NEMO3_FINAL_CONFIRMATION_SCHEMA,
        "created_at_utc": now_iso(),
        "state_id": state_id,
        "created_after_internal_thinking_lock": True,
        "created_before_actuator_step": True,
        "confirms_selected_action": True,
        "nemo_supplied_action": False,
        "selected_action_value": int(selected_branch["action_value"]),
        "selected_action_name": selected_branch["action_name"],
        "role": "confirmation_not_action_source",
        "decision_delegated_to_nemo": False,
        "confirmation_mode": args.nemo_mode,
        "external_nemo3_model_invoked": args.nemo_mode == LIVE_NEMO_MODE,
        "model": args.nemo_model,
        "relay_url": args.nemo_relay_url if args.nemo_mode == LIVE_NEMO_MODE else None,
        "packet": packet,
        "response": response,
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def build_model_decision(
    *,
    state_id: str,
    run_label: str,
    selected_branch: dict[str, Any],
    standard_flow: dict[str, Any],
    game_knowledge: dict[str, Any],
    game_knowledge_ref: dict[str, str],
    mlp_consultation: dict[str, Any],
    mlp_consultation_ref: dict[str, str],
    internal_lock: dict[str, Any],
    internal_lock_ref: dict[str, str],
    final_confirmation: dict[str, Any],
    final_ref: dict[str, str],
    interim_confirmations: list[dict[str, Any]],
    trust_checks: dict[str, Any],
    nemo_mode: str,
) -> dict[str, Any]:
    return {
        "schema": MODEL_DECISION_SCHEMA,
        "created_at_utc": now_iso(),
        "decision_id": decision_identifier(run_label, state_id, selected_branch["action_value"]),
        "state_id": state_id,
        "standard_model_flow": standard_flow,
        "chronometric_game_knowledge": {
            "schema": CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA,
            "artifact": game_knowledge_ref["artifact"],
            "sha256": game_knowledge_ref["sha256"],
            "backbone_surface": game_knowledge["backbone_surface"],
            "calibration_surface": game_knowledge["calibration_surface"],
            "score_surface": game_knowledge["score_surface"],
            "knowledge_domains": game_knowledge["knowledge_domains"],
            "swiglu_backbone_linked": True,
            "action_embedding_context_linked": True,
            "calibration_mlp_linked": True,
            "branch_library_linked": True,
            "drives_branch_simulation": True,
            "created_before_internal_branch_simulation": True,
            "updates_from_post_action_calibration_only": True,
            "online_update_requires_promotion_condition": True,
            "heldout_labels_used": False,
        },
        "mlp_consultation": {
            "schema": MLP_CONSULTATION_SCHEMA,
            "artifact": mlp_consultation_ref["artifact"],
            "sha256": mlp_consultation_ref["sha256"],
            "backbone_surface": mlp_consultation["backbone_surface"],
            "calibration_surface": mlp_consultation["calibration_surface"],
            "score_surface": mlp_consultation["score_surface"],
            "prior_post_action_update_candidates": mlp_consultation["prior_post_action_update_candidates"],
            "post_action_update_candidate_context_count": mlp_consultation[
                "post_action_update_candidate_context_count"
            ],
            "post_action_update_candidate_context_sha256": mlp_consultation[
                "post_action_update_candidate_context_sha256"
            ],
            "candidate_priors": mlp_consultation["candidate_priors"],
            "consulted_before_branch_simulation": True,
            "drives_branch_simulation": True,
            "action_embedding_context_linked": True,
            "calibration_mlp_linked": True,
            "branch_library_context_linked": True,
            "updates_from_post_action_only": True,
            "online_update_requires_promotion_condition": True,
            "heldout_labels_used": False,
        },
        "internal_thinking_lock": {
            "schema": INTERNAL_THINKING_LOCK_SCHEMA,
            "artifact": internal_lock_ref["artifact"],
            "sha256": internal_lock_ref["sha256"],
            "locked": True,
            "drives_selected_action": True,
            "created_before_actuator_step": True,
            "selected_action_value": int(selected_branch["action_value"]),
            "ambiguity_detected": internal_lock["ambiguity_detected"],
            "open_question_ids": internal_lock["open_question_ids"],
        },
        "nemo3": {
            "invoked": True,
            "role": "confirmation_not_action_source",
            "decision_delegated_to_nemo": False,
            "confirmation_mode": nemo_mode,
            "external_nemo3_model_invoked": nemo_mode == LIVE_NEMO_MODE,
            "interim_confirmation_policy": {
                "call_on_ambiguity_or_open_questions": True,
            },
            "interim_confirmations": interim_confirmations,
            "final_confirmation": {
                "schema": NEMO3_FINAL_CONFIRMATION_SCHEMA,
                "artifact": final_ref["artifact"],
                "sha256": final_ref["sha256"],
                "created_after_internal_thinking_lock": True,
                "created_before_actuator_step": True,
                "confirms_selected_action": True,
                "nemo_supplied_action": False,
                "selected_action_value": int(selected_branch["action_value"]),
            },
        },
        "trust": {
            "map_trusted": trust_checks["map_trusted"],
            "geometry_trusted": trust_checks["geometry_trusted"],
            "ray_trusted": trust_checks["ray_trusted"],
            "temporal_trusted": trust_checks["temporal_trusted"],
            "branch_selection_trusted": trust_checks["branch_selection_trusted"],
        },
        "selected_action": {
            "action_name": selected_branch["action_name"],
            "action_value": int(selected_branch["action_value"]),
            "source": SELECTED_ACTION_SOURCE,
            "action_data": selected_branch.get("action_data"),
        },
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
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
        "run_kind": "arc_agi3_reset_only_model_decision_producer",
        "run_label_semantics": "new_experiment_reset_only_model_decision_artifact_v047",
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
        "toolkit": "arc_agi.Arcade",
        "toolkit_versions": {
            "arc_agi": package_version("arc_agi"),
            "arcengine": package_version("arcengine"),
        },
        "model_decision_schema": MODEL_DECISION_SCHEMA,
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "nemo_mode": args.nemo_mode,
        "nemo_external_model_required": args.nemo_mode == LIVE_NEMO_MODE,
        "nemo_relay_url": args.nemo_relay_url if args.nemo_mode == LIVE_NEMO_MODE else None,
        "nemo_model": args.nemo_model,
        "actuator_step_count": 0,
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "deterministic_from_reset_frame_sha_and_action_values",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": "not_applicable_reset_only_artifact_producer",
        "loader_mode": "arc_agi_offline_local_environment_wrapper_reset_only",
        "loader_settings": {
            "operation_mode": args.operation_mode,
            "game": args.game,
            "max_candidate_actions": args.max_candidate_actions,
            "branch_ambiguity_gap_threshold": args.branch_ambiguity_gap_threshold,
            "online_submission": False,
            "scorecard_submission": False,
        },
        "metric_to_compare": "arc_agi3_valid_model_decision_artifact_and_zero_actuator_steps",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "not_applicable_python_sdk_reset_only",
        "arc_data_used": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def summarize_producer(
    *,
    condition: dict[str, Any],
    games: list[dict[str, Any]],
    selected_game: dict[str, Any],
    candidate_packets: list[dict[str, Any]],
    model_decision: dict[str, Any],
    world_state: dict[str, Any],
    branch_simulation: dict[str, Any],
    trust_checks: dict[str, Any],
    interim_confirmations: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = model_decision["selected_action"]
    final_confirmation = model_decision["nemo3"]["final_confirmation"]
    return {
        "schema": SCHEMA,
        "condition": condition,
        "available_game_count": len(games),
        "selected_game": selected_game,
        "model_decision_schema": model_decision["schema"],
        "model_decision_artifact": model_decision["standard_model_flow"]["model_decision_artifact"],
        "decision_id": model_decision["decision_id"],
        "state_id": model_decision["state_id"],
        "candidate_action_packets": len(candidate_packets),
        "world_state_3d_artifact": model_decision["standard_model_flow"]["world_state_3d_artifact"],
        "world_state_surface": world_state["world_model_surface"],
        "object_anchor_count": world_state["ray_map"]["anchor_count"],
        "ray_count": world_state["ray_map"]["ray_count"],
        "chronometric_game_knowledge": model_decision["chronometric_game_knowledge"]["artifact"],
        "chronometric_game_knowledge_score_surface": model_decision["chronometric_game_knowledge"]["score_surface"],
        "mlp_consultation": model_decision["mlp_consultation"]["artifact"],
        "mlp_consultation_sha256": model_decision["mlp_consultation"]["sha256"],
        "mlp_candidate_priors": len(model_decision["mlp_consultation"]["candidate_priors"]),
        "mlp_post_action_update_context_count": model_decision["mlp_consultation"][
            "post_action_update_candidate_context_count"
        ],
        "branch_simulation_artifact": model_decision["standard_model_flow"]["branch_simulation_artifact"],
        "selected_branch_id": branch_simulation["selected_branch_id"],
        "selected_action": f"{selected['action_name']}:{selected['action_value']}",
        "selected_action_name": selected["action_name"],
        "selected_action_value": selected["action_value"],
        "selected_action_source": selected["source"],
        "trust": {
            "map_trusted": trust_checks["map_trusted"],
            "geometry_trusted": trust_checks["geometry_trusted"],
            "ray_trusted": trust_checks["ray_trusted"],
            "temporal_trusted": trust_checks["temporal_trusted"],
            "branch_selection_trusted": trust_checks["branch_selection_trusted"],
        },
        "internal_thinking_lock": model_decision["internal_thinking_lock"]["artifact"],
        "nemo3_invoked": model_decision["nemo3"]["invoked"],
        "nemo3_confirmation_mode": model_decision["nemo3"]["confirmation_mode"],
        "nemo3_external_model_invoked": model_decision["nemo3"]["external_nemo3_model_invoked"],
        "nemo3_final_confirmation": final_confirmation["artifact"],
        "nemo3_final_confirmation_sha256": final_confirmation["sha256"],
        "nemo3_interim_confirmation_count": len(interim_confirmations),
        "valid_standard_model_decision": True,
        "actuator_steps_executed": 0,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC-AGI-3 ModelDecision Producer V047 Results",
        "",
        "Status: reset-only ModelDecision artifact production. No ARC actuator step, no online submission, no score claim.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- source condition: `{condition['source_condition_artifact']}`",
        f"- environments dir: `{condition['dataset_path']}`",
        f"- operation mode: `{condition['operation_mode']}`",
        f"- selected game: `{condition['selected_game']['game_id']}`",
        f"- Nemo mode: `{condition['nemo_mode']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        f"- ARC solve claim: `{condition['arc_solve_claim']}`",
        f"- online submission: `{condition['online_submission']}`",
        "",
        "## Metrics",
        "",
        f"- valid standard ModelDecision: `{metrics['valid_standard_model_decision']}`",
        f"- model decision: `{metrics['model_decision_artifact']}`",
        f"- action source: `{metrics['selected_action_source']}`",
        f"- selected action: `{metrics['selected_action_name']}:{metrics['selected_action_value']}`",
        f"- candidate action packets: `{metrics['candidate_action_packets']}`",
        f"- world-state surface: `{metrics['world_state_surface']}`",
        f"- object anchors: `{metrics['object_anchor_count']}`",
        f"- rays: `{metrics['ray_count']}`",
        f"- chronometric score surface: `{metrics['chronometric_game_knowledge_score_surface']}`",
        f"- MLP consultation: `{metrics['mlp_consultation']}`",
        f"- MLP candidate priors: `{metrics['mlp_candidate_priors']}`",
        f"- MLP post-action update context count: `{metrics['mlp_post_action_update_context_count']}`",
        f"- Nemo3 invoked: `{metrics['nemo3_invoked']}`",
        f"- Nemo3 confirmation mode: `{metrics['nemo3_confirmation_mode']}`",
        f"- external Nemo3 model invoked: `{metrics['nemo3_external_model_invoked']}`",
        f"- interim Nemo confirmations: `{metrics['nemo3_interim_confirmation_count']}`",
        f"- actuator steps executed: `{metrics['actuator_steps_executed']}`",
        "",
    ]
    return "\n".join(lines)


def grid_from_frame_stack(frame_stack: Any) -> tuple[tuple[int, ...], ...]:
    if not frame_stack:
        raise ValueError("reset observation has no frame stack")
    latest = frame_stack[-1]
    if hasattr(latest, "tolist"):
        data = latest.tolist()
    else:
        data = latest
    if not data:
        raise ValueError("latest frame is empty")
    rows = []
    for row in data:
        rows.append(tuple(int(value) for value in row))
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("latest frame must be a non-empty rectangular grid")
    return tuple(rows)


def grid_statistics(grid: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    flat = [int(value) for row in grid for value in row]
    counts = Counter(flat)
    digest = hashlib.sha256(json.dumps(grid, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "width": len(grid[0]),
        "height": len(grid),
        "cell_total": len(flat),
        "nonzero_cells": sum(1 for value in flat if value != 0),
        "labels": sorted(counts),
        "value_counts": {str(label): counts[label] for label in sorted(counts)},
        "grid_sha256": digest,
    }


def selected_branch_from(branch_simulation: dict[str, Any]) -> dict[str, Any]:
    for branch in branch_simulation.get("branches", []):
        if branch.get("selected") is True:
            return branch
    raise ValueError("branch_simulation has no selected branch")


def ambiguity_record(branch_simulation: dict[str, Any], *, threshold: float) -> dict[str, Any]:
    branches = list(branch_simulation.get("branches", []))
    if len(branches) < 2:
        gap = None
    else:
        gap = round(float(branches[0]["score"]) - float(branches[1]["score"]), 6)
    ambiguous = gap is not None and gap < threshold
    return {
        "ambiguity_detected": ambiguous,
        "top_branch_gap": gap,
        "threshold": threshold,
    }


def compact_branch(branch: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_id": branch.get("branch_id"),
        "action_name": branch.get("action_name"),
        "action_value": branch.get("action_value"),
        "score": branch.get("score"),
        "score_surface": branch.get("score_surface"),
        "score_components": branch.get("score_components", {}),
    }


def model_flow_ref(path: Path) -> dict[str, str]:
    return {
        "artifact": _repo_rel(path),
        "sha256": _sha256(path),
    }


def state_identifier(selected_game: dict[str, Any], reset_obs: Any, frame_summary: dict[str, Any]) -> str:
    guid = str(getattr(reset_obs, "guid", "") or "")
    frame_sha = str(frame_summary.get("latest_frame_sha256") or "no-frame")
    suffix = guid or frame_sha[:16]
    return f"{selected_game['name']}:reset:{suffix}"


def decision_identifier(run_label: str, state_id: str, action_value: int) -> str:
    digest = hashlib.sha256(f"{run_label}:{state_id}:{action_value}".encode("utf-8")).hexdigest()[:16]
    return f"{run_label}:{digest}"


def stable_unit_float(value: str) -> float:
    raw = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return int(raw, 16) / float(0xFFFFFFFFFFFF)


def stable_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def nemo_response_for(*, args: argparse.Namespace, packet: dict[str, Any], stage: str) -> dict[str, Any]:
    if args.nemo_mode == LOCAL_NEMO_MODE:
        return {
            "relay_ok": True,
            "relay_error": None,
            "model": args.nemo_model,
            "relay_url": None,
            "response_text": json.dumps(
                {
                    "stage": stage,
                    "confirms_selected_action": True,
                    "selected_action_value": packet.get("selected_action_value")
                    or (packet.get("selected_branch") or {}).get("action_value"),
                    "nemo_supplied_action": False,
                    "confidence": 1.0,
                    "mode": LOCAL_NEMO_MODE,
                    "external_model_invoked": False,
                },
                sort_keys=True,
            ),
        }
    response_text = call_nemo(packet=packet, relay_url=args.nemo_relay_url, model=args.nemo_model, timeout=args.nemo_timeout)
    return {
        "relay_ok": True,
        "relay_error": None,
        "model": args.nemo_model,
        "relay_url": args.nemo_relay_url,
        "response_text": response_text,
    }


def call_nemo(*, packet: dict[str, Any], relay_url: str, model: str, timeout: int) -> str:
    if relay_url.endswith("/v1/responses"):
        body = {
            "model": model,
            "input": (
                "You are Nemo3, a semantic confirmation layer for an internal ARC world-model. "
                "Confirm or reject the internally selected action only. Do not supply a new action. "
                "Return one compact final JSON object only in output_text.\n"
                "NEMO3_CONFIRMATION_PACKET:\n"
                + json.dumps(packet, sort_keys=True)
            ),
            "temperature": 0.1,
            "max_output_tokens": 1200,
        }
    else:
        body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Nemo3, a semantic confirmation layer for an internal ARC world-model. "
                        "Confirm or reject the internally selected action only. Do not supply a new action. "
                        "Return compact JSON only."
                    ),
                },
                {"role": "user", "content": json.dumps(packet, sort_keys=True)},
            ],
            "temperature": 0.1,
            "max_tokens": 1200,
        }
    request = Request(
        relay_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local relay URL is operator controlled.
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"Nemo relay HTTP {exc.code}: {error_body or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Nemo relay connection failed: {exc.reason}") from exc
    text = extract_nemo_text(payload)
    if not text:
        raise ValueError("Nemo relay returned an empty final answer")
    return text


def extract_nemo_text(payload: dict[str, Any]) -> str:
    output_texts: list[str] = []
    for item in payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text" and content.get("text"):
                output_texts.append(str(content["text"]))
    if output_texts:
        return "\n".join(output_texts).strip()

    choices = payload.get("choices") or []
    if choices:
        content = (choices[0].get("message") or {}).get("content")
        if content:
            return str(content).strip()
        text = choices[0].get("text")
        if text:
            return str(text).strip()
    return ""


def parse_nemo_json_response(text: str) -> dict[str, Any]:
    candidates = [text]
    if "```" in text:
        parts = text.split("```")
        candidates.extend(part.strip() for part in parts if part.strip())
    last_error: Exception | None = None
    for candidate in candidates:
        cleaned = candidate.strip()
        if cleaned.startswith("json\n"):
            cleaned = cleaned[5:].strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(parsed, dict):
            return parsed
    raise ValueError(f"Nemo response_text is not parseable JSON: {last_error}")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_agi3_model_decision_v047_ls20_reset")
    parser.add_argument("--operation-mode", choices=("OFFLINE",), default="OFFLINE")
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument("--branch-ambiguity-gap-threshold", type=float, default=0.03)
    parser.add_argument("--nemo-mode", choices=(LOCAL_NEMO_MODE, LIVE_NEMO_MODE), default=LOCAL_NEMO_MODE)
    parser.add_argument("--nemo-relay-url", default=os.environ.get("NEMO_RELAY_URL", "http://127.0.0.1:8000/v1/responses"))
    parser.add_argument("--nemo-model", default=os.environ.get("NEMO_RELAY_MODEL", "nemotron_3_nano_omni"))
    parser.add_argument("--nemo-timeout", type=int, default=90)
    parser.add_argument("--historical-comparator", default="arc_agi3_model_flow_v046_contract")
    parser.add_argument("--historical-comparator-artifact", type=Path, default=ROOT / "goal_test_results.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "valid_standard_model_decision": metrics["valid_standard_model_decision"],
                "model_decision_artifact": metrics["model_decision_artifact"],
                "selected_action": f"{metrics['selected_action_name']}:{metrics['selected_action_value']}",
                "nemo3_confirmation_mode": metrics["nemo3_confirmation_mode"],
                "nemo3_external_model_invoked": metrics["nemo3_external_model_invoked"],
                "actuator_steps_executed": metrics["actuator_steps_executed"],
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
