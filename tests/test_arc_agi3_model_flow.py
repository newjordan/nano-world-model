import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

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
    ModelDecisionError,
    actuator_reasoning_from_model_decision,
    require_standard_model_decision,
)


def _valid_decision(action_value=1):
    return {
        "schema": MODEL_DECISION_SCHEMA,
        "decision_id": "decision-001",
        "state_id": "ls20-reset",
        "standard_model_flow": {
            "sequence": list(STANDARD_MODEL_FLOW),
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
            "schema": CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA,
            "artifact": "artifact://game-knowledge",
            "sha256": "d" * 64,
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
        },
        "mlp_consultation": {
            "schema": MLP_CONSULTATION_SCHEMA,
            "artifact": "artifact://mlp-consultation",
            "sha256": "e" * 64,
            "backbone_surface": CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE,
            "calibration_surface": CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION,
            "score_surface": CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE,
            "candidate_priors": [{"action_value": action_value, "mlp_prior": 0.8}],
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
            "artifact": "artifact://internal-thinking",
            "sha256": "a" * 64,
            "locked": True,
            "drives_selected_action": True,
            "created_before_actuator_step": True,
            "selected_action_value": action_value,
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
                "schema": NEMO3_FINAL_CONFIRMATION_SCHEMA,
                "artifact": "artifact://nemo3-final",
                "sha256": "b" * 64,
                "created_after_internal_thinking_lock": True,
                "created_before_actuator_step": True,
                "confirms_selected_action": True,
                "nemo_supplied_action": False,
                "selected_action_value": action_value,
            },
        },
        "trust": {
            "map_trusted": True,
            "geometry_trusted": True,
            "ray_trusted": True,
            "temporal_trusted": True,
            "branch_selection_trusted": True,
        },
        "selected_action": {
            "action_name": f"ACTION{action_value}",
            "action_value": action_value,
            "source": SELECTED_ACTION_SOURCE,
            "action_data": None,
        },
    }


def test_standard_model_decision_accepts_complete_world_model_flow():
    selected = require_standard_model_decision(_valid_decision(), available_action_values=[1, 2, 3, 4])

    assert selected["action_value"] == 1
    assert selected["action_name"] == "ACTION1"


def test_standard_model_decision_rejects_missing_nemo3_and_world_artifacts():
    decision = _valid_decision()
    decision["nemo3"] = {"invoked": False}
    decision["standard_model_flow"]["world_state_3d_artifact"] = ""

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    message = str(error.value)
    assert "nemo3.invoked must be true" in message
    assert "standard_model_flow.world_state_3d_artifact is required" in message


def test_standard_model_decision_rejects_unlinked_chronometric_game_knowledge():
    decision = _valid_decision()
    decision["chronometric_game_knowledge"]["artifact"] = ""
    decision["chronometric_game_knowledge"]["action_embedding_context_linked"] = False
    decision["chronometric_game_knowledge"]["branch_library_linked"] = False
    decision["chronometric_game_knowledge"]["heldout_labels_used"] = True
    decision["chronometric_game_knowledge"]["knowledge_domains"] = ["basic_movement"]

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    message = str(error.value)
    assert "chronometric_game_knowledge.artifact is required" in message
    assert "chronometric_game_knowledge.action_embedding_context_linked must be true" in message
    assert "chronometric_game_knowledge.branch_library_linked must be true" in message
    assert "chronometric_game_knowledge.heldout_labels_used must be false" in message
    assert "chronometric_game_knowledge.knowledge_domains must include known_interactions" in message
    assert "chronometric_game_knowledge.knowledge_domains must include branch_value_calibration" in message


def test_standard_model_decision_rejects_missing_mlp_consultation():
    decision = _valid_decision()
    decision["standard_model_flow"]["mlp_consultation_artifact"] = ""
    decision["mlp_consultation"]["artifact"] = ""
    decision["mlp_consultation"]["consulted_before_branch_simulation"] = False
    decision["mlp_consultation"]["candidate_priors"] = []
    decision["mlp_consultation"]["heldout_labels_used"] = True

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    message = str(error.value)
    assert "standard_model_flow.mlp_consultation_artifact is required" in message
    assert "mlp_consultation.artifact is required" in message
    assert "mlp_consultation.consulted_before_branch_simulation must be true" in message
    assert "mlp_consultation.candidate_priors must be non-empty" in message
    assert "mlp_consultation.heldout_labels_used must be false" in message


def test_standard_model_decision_rejects_nemo_as_action_source_or_missing_final_signoff():
    decision = _valid_decision()
    decision["selected_action"]["source"] = "nemo3"
    decision["nemo3"]["role"] = "action_source"
    decision["nemo3"]["decision_delegated_to_nemo"] = True
    decision["nemo3"]["final_confirmation"]["artifact"] = ""
    decision["nemo3"]["final_confirmation"]["confirms_selected_action"] = False
    decision["nemo3"]["final_confirmation"]["nemo_supplied_action"] = True
    decision["nemo3"]["final_confirmation"]["selected_action_value"] = 2

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    message = str(error.value)
    assert f"selected_action.source must be {SELECTED_ACTION_SOURCE}" in message
    assert "nemo3.role must be confirmation_not_action_source" in message
    assert "nemo3.decision_delegated_to_nemo must be false" in message
    assert "nemo3.final_confirmation.artifact is required" in message
    assert "nemo3.final_confirmation.confirms_selected_action must be true" in message
    assert "nemo3.final_confirmation.nemo_supplied_action must be false" in message
    assert "nemo3.final_confirmation.selected_action_value must match" in message


def test_standard_model_decision_requires_interim_nemo_confirmation_when_ambiguous():
    decision = _valid_decision()
    decision["internal_thinking_lock"]["ambiguity_detected"] = True
    decision["internal_thinking_lock"]["open_question_ids"] = ["q-map"]

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    assert "nemo3.interim_confirmations are required" in str(error.value)

    decision["nemo3"]["interim_confirmations"] = [
        {
            "schema": NEMO3_INTERIM_CONFIRMATION_SCHEMA,
            "artifact": "artifact://nemo3-q-map",
            "sha256": "c" * 64,
            "question_id": "q-map",
            "created_during_internal_thinking": True,
            "role": "ambiguity_or_question_confirmation",
        }
    ]

    selected = require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    assert selected["action_value"] == 1


def test_standard_model_decision_rejects_unlocked_internal_thinking():
    decision = _valid_decision()
    decision["internal_thinking_lock"] = {
        "schema": INTERNAL_THINKING_LOCK_SCHEMA,
        "artifact": "artifact://different",
        "sha256": "not-a-hash",
        "locked": False,
        "drives_selected_action": False,
        "created_before_actuator_step": False,
        "selected_action_value": 2,
    }

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    message = str(error.value)
    assert "internal_thinking_lock.locked must be true" in message
    assert "internal_thinking_lock.drives_selected_action must be true" in message
    assert "internal_thinking_lock.created_before_actuator_step must be true" in message
    assert "internal_thinking_lock.artifact must match" in message
    assert "internal_thinking_lock.sha256 must be" in message
    assert "internal_thinking_lock.selected_action_value must match" in message


def test_standard_model_decision_rejects_untrusted_ray_or_unavailable_action():
    decision = _valid_decision(action_value=9)
    decision["trust"]["ray_trusted"] = False

    with pytest.raises(ModelDecisionError) as error:
        require_standard_model_decision(decision, available_action_values=[1, 2, 3, 4])

    message = str(error.value)
    assert "trust.ray_trusted must be true" in message
    assert "selected_action.action_value 9 is not available" in message


def test_actuator_reasoning_keeps_model_provenance_and_non_submission_flags():
    decision = _valid_decision()

    reasoning = actuator_reasoning_from_model_decision(decision)

    assert reasoning["policy"] == "standard_nemo3_world_model_flow"
    assert reasoning["decision_id"] == "decision-001"
    assert reasoning["nemo3_invoked"] is True
    assert reasoning["nemo3_final_confirmation"] == "artifact://nemo3-final"
    assert reasoning["nemo3_final_confirmation_sha256"] == "b" * 64
    assert reasoning["nemo3_interim_confirmation_count"] == 0
    assert reasoning["chronometric_game_knowledge"] == "artifact://game-knowledge"
    assert reasoning["chronometric_game_knowledge_sha256"] == "d" * 64
    assert reasoning["chronometric_game_knowledge_score_surface"] == CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE
    assert reasoning["mlp_consultation"] == "artifact://mlp-consultation"
    assert reasoning["mlp_consultation_sha256"] == "e" * 64
    assert reasoning["mlp_consultation_surface"] == CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION
    assert reasoning["internal_thinking_lock"] == "artifact://internal-thinking"
    assert reasoning["internal_thinking_sha256"] == "a" * 64
    assert reasoning["submit_online"] is False
    assert reasoning["arc_solve_claim"] is False
