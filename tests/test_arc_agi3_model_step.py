import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_agi3_model_step.py"
    spec = importlib.util.spec_from_file_location("run_arc_agi3_model_step", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeInfo:
    game_id = "ls20-9607627b"


class FakeEnv:
    info = FakeInfo()
    action_space = []


class FakeObs:
    def __init__(self, *, levels_completed=0, state="NOT_FINISHED"):
        self.game_id = "ls20-9607627b"
        self.guid = "obs-guid"
        self.state = state
        self.levels_completed = levels_completed
        self.win_levels = 7
        self.full_reset = True


class FakeAction:
    name = "ACTION1"
    value = 1


def _decision(module):
    return {
        "schema": module.MODEL_DECISION_SCHEMA,
        "decision_id": "decision-001",
        "state_id": "ls20-reset",
        "standard_model_flow": {
            "sequence": list(module.STANDARD_MODEL_FLOW),
            "observation_artifact": "artifact://obs",
            "world_state_3d_artifact": "artifact://world3d",
            "chronometric_game_knowledge_artifact": "artifact://game-knowledge",
            "mlp_consultation_artifact": "artifact://mlp-consultation",
            "branch_simulation_artifact": "artifact://branches",
            "trust_checks_artifact": "artifact://trust",
            "internal_thinking_artifact": "artifact://internal-thinking",
            "nemo3_final_confirmation_artifact": "artifact://nemo3-final",
            "model_decision_artifact": "artifact://decision",
        },
        "chronometric_game_knowledge": {
            "schema": module.CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA,
            "artifact": "artifact://game-knowledge",
            "sha256": "d" * 64,
            "backbone_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
            "calibration_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
            "score_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
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
        },
        "mlp_consultation": {
            "schema": module.MLP_CONSULTATION_SCHEMA,
            "artifact": "artifact://mlp-consultation",
            "sha256": "e" * 64,
            "backbone_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
            "calibration_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
            "score_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
            "candidate_priors": [{"action_value": 1, "mlp_prior": 0.8}],
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
            "schema": module.INTERNAL_THINKING_LOCK_SCHEMA,
            "artifact": "artifact://internal-thinking",
            "sha256": "a" * 64,
            "locked": True,
            "drives_selected_action": True,
            "created_before_actuator_step": True,
            "selected_action_value": 1,
        },
        "nemo3": {
            "invoked": True,
            "role": "confirmation_not_action_source",
            "decision_delegated_to_nemo": False,
            "interim_confirmation_policy": {
                "call_on_ambiguity_or_open_questions": True,
            },
            "interim_confirmations": [],
            "final_confirmation": {
                "schema": module.NEMO3_FINAL_CONFIRMATION_SCHEMA,
                "artifact": "artifact://nemo3-final",
                "sha256": "b" * 64,
                "created_after_internal_thinking_lock": True,
                "created_before_actuator_step": True,
                "confirms_selected_action": True,
                "nemo_supplied_action": False,
                "selected_action_value": 1,
            },
        },
        "selected_action": {
            "action_name": "ACTION1",
            "action_value": 1,
            "source": module.SELECTED_ACTION_SOURCE,
            "action_data": None,
        },
    }


def test_model_step_trace_row_records_model_decision_not_policy_loop():
    module = _load_module()
    args = SimpleNamespace(run_label="test-model-step")
    before = {"latest_frame_shape": [64, 64], "latest_frame_sha256": "a"}
    after = {"latest_frame_shape": [64, 64], "latest_frame_sha256": "b"}
    env = FakeEnv()
    env.action_space = [FakeAction()]
    observation_match = {
        "artifact": "artifact://obs",
        "sha256": "e" * 64,
        "content_match": True,
        "guid_match": False,
        "expected_guid": "model-guid",
        "current_guid": "obs-guid",
    }
    update_ref = {"artifact": "artifact://post-action-mlp", "sha256": "f" * 64}
    update = {"update_mode": "candidate-only", "mlp_weights_updated": False}

    row = module.trace_row(
        args=args,
        env=env,
        game_name="ls20",
        obs=FakeObs(),
        next_obs=FakeObs(levels_completed=1),
        action=FakeAction(),
        action_data=None,
        model_decision=_decision(module),
        before_summary=before,
        next_summary=after,
        observation_match=observation_match,
        post_action_mlp_update_ref=update_ref,
        post_action_mlp_update=update,
    )

    assert row["schema"] == module.TRACE_SCHEMA
    assert row["decision_id"] == "decision-001"
    assert row["source_model_decision_id"] == "decision-001"
    assert row["standard_model_flow"] == list(module.STANDARD_MODEL_FLOW)
    assert row["observation_artifact"] == "artifact://obs"
    assert row["observation_content_match"] is True
    assert row["observation_guid_match"] is False
    assert row["nemo3_invoked"] is True
    assert row["nemo3_role"] == "confirmation_not_action_source"
    assert row["nemo3_decision_delegated_to_nemo"] is False
    assert row["nemo3_final_confirmation"] == "artifact://nemo3-final"
    assert row["nemo3_final_confirmation_sha256"] == "b" * 64
    assert row["selected_action_source"] == module.SELECTED_ACTION_SOURCE
    assert row["chronometric_game_knowledge"] == "artifact://game-knowledge"
    assert row["chronometric_game_knowledge_sha256"] == "d" * 64
    assert row["chronometric_game_knowledge_score_surface"] == module.CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE
    assert row["chronometric_game_knowledge_action_embedding_linked"] is True
    assert row["chronometric_game_knowledge_branch_library_linked"] is True
    assert row["mlp_consultation"] == "artifact://mlp-consultation"
    assert row["post_action_mlp_update_artifact"] == "artifact://post-action-mlp"
    assert row["post_action_mlp_update_candidate_written"] is True
    assert row["mlp_weights_updated"] is False
    assert row["chosen_action"] == "ACTION1:1"
    assert row["chosen_action_value"] == 1
    assert row["level_delta"] == 1
    assert row["online_submission"] is False


def test_model_step_summary_requires_one_model_decision_actuator_step():
    module = _load_module()
    condition = {"selected_game": {"game_id": "ls20-9607627b", "name": "ls20"}}
    row = {
        "chosen_action_name": "ACTION1",
        "chosen_action": "ACTION1:1",
        "chosen_action_value": 1,
        "source_model_decision_id": "decision-001",
        "available_action_values": [1, 2, 3, 4],
        "observation_artifact": "artifact://obs",
        "observation_artifact_sha256": "e" * 64,
        "observation_content_match": True,
        "observation_guid_match": False,
        "frame_changed": True,
        "levels_completed": 0,
        "next_levels_completed": 1,
        "level_delta": 1,
        "next_state": "NOT_FINISHED",
        "selected_action_source": module.SELECTED_ACTION_SOURCE,
        "nemo3_invoked": True,
        "nemo3_role": "confirmation_not_action_source",
        "nemo3_decision_delegated_to_nemo": False,
        "nemo3_final_confirmation": "artifact://nemo3-final",
        "nemo3_interim_confirmation_count": 0,
        "chronometric_game_knowledge": "artifact://game-knowledge",
        "chronometric_game_knowledge_score_surface": module.CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
        "chronometric_game_knowledge_action_embedding_linked": True,
        "chronometric_game_knowledge_branch_library_linked": True,
        "mlp_consultation": "artifact://mlp-consultation",
        "mlp_consultation_sha256": "e" * 64,
        "post_action_mlp_update_artifact": "artifact://post-action-mlp",
        "post_action_mlp_update_sha256": "f" * 64,
        "post_action_mlp_update_candidate_written": True,
        "post_action_mlp_update_mode": "candidate-only",
        "mlp_weights_updated": False,
        "online_submission": False,
        "arc_solve_claim": False,
    }

    metrics = module.summarize_model_step(
        condition=condition,
        games=[condition["selected_game"]],
        trace_rows=[row],
        candidate_packets=[{"action_value": 1}],
        model_decision=_decision(module),
    )

    assert metrics["valid_standard_model_flow_step"] is True
    assert metrics["source_model_decision_id"] == "decision-001"
    assert metrics["chosen_action"] == "ACTION1:1"
    assert metrics["actuator_steps_executed"] == 1
    assert metrics["observation_content_match"] is True
    assert metrics["observation_guid_match"] is False
    assert metrics["nemo3_final_confirmation"] == "artifact://nemo3-final"
    assert metrics["nemo3_interim_confirmation_count"] == 0
    assert metrics["chronometric_game_knowledge"] == "artifact://game-knowledge"
    assert metrics["chronometric_game_knowledge_score_surface"] == module.CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE
    assert metrics["mlp_consultation"] == "artifact://mlp-consultation"
    assert metrics["post_action_mlp_update_artifact"] == "artifact://post-action-mlp"
    assert metrics["post_action_mlp_update_candidate_written"] is True
    assert metrics["mlp_weights_updated"] is False
    assert metrics["levels_completed_delta"] == 1


def test_observation_artifact_match_requires_current_frame_content(tmp_path):
    module = _load_module()
    env = FakeEnv()
    env.action_space = [FakeAction()]
    obs = FakeObs()
    frame_summary = {
        "frame_stack_len": 1,
        "latest_frame_shape": [64, 64],
        "latest_frame_min": 0,
        "latest_frame_max": 15,
        "latest_frame_sha256": "frame-sha",
    }
    artifact = tmp_path / "observation.json"
    artifact.write_text(
        """{
  "game_id": "ls20-9607627b",
  "guid": "model-guid",
  "state": "NOT_FINISHED",
  "levels_completed": 0,
  "win_levels": 7,
  "full_reset": true,
  "available_action_values": [1],
  "frame": {
    "frame_stack_len": 1,
    "latest_frame_shape": [64, 64],
    "latest_frame_min": 0,
    "latest_frame_max": 15,
    "latest_frame_sha256": "frame-sha"
  }
}
""",
        encoding="utf-8",
    )
    decision = _decision(module)
    decision["standard_model_flow"]["observation_artifact"] = str(artifact)

    match = module.require_observation_artifact_match(
        model_decision=decision,
        obs=obs,
        env=env,
        frame_summary=frame_summary,
    )

    assert match["content_match"] is True
    assert match["guid_match"] is False
    assert match["expected_guid"] == "model-guid"
    assert match["current_guid"] == "obs-guid"


def test_observation_artifact_match_rejects_frame_mismatch(tmp_path):
    module = _load_module()
    env = FakeEnv()
    env.action_space = [FakeAction()]
    obs = FakeObs()
    frame_summary = {
        "frame_stack_len": 1,
        "latest_frame_shape": [64, 64],
        "latest_frame_min": 0,
        "latest_frame_max": 15,
        "latest_frame_sha256": "current-frame-sha",
    }
    artifact = tmp_path / "observation.json"
    artifact.write_text(
        """{
  "game_id": "ls20-9607627b",
  "guid": "obs-guid",
  "state": "NOT_FINISHED",
  "levels_completed": 0,
  "win_levels": 7,
  "full_reset": true,
  "available_action_values": [1],
  "frame": {
    "frame_stack_len": 1,
    "latest_frame_shape": [64, 64],
    "latest_frame_min": 0,
    "latest_frame_max": 15,
    "latest_frame_sha256": "model-frame-sha"
  }
}
""",
        encoding="utf-8",
    )
    decision = _decision(module)
    decision["standard_model_flow"]["observation_artifact"] = str(artifact)

    try:
        module.require_observation_artifact_match(
            model_decision=decision,
            obs=obs,
            env=env,
            frame_summary=frame_summary,
        )
    except RuntimeError as error:
        assert "latest_frame_sha256" in str(error)
    else:
        raise AssertionError("expected frame mismatch to fail closed")
