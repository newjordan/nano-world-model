"""Standard ARC-AGI-3 model-flow boundary.

The ARC environment wrapper is an actuator. It does not own policy. A real
non-I/O ARC step must be driven by a ModelDecision emitted by the Nemo3/world
model flow:

observation -> 3D/world state -> chronometric game knowledge -> MLP
consultation -> internal forward rollout -> internal branch simulation ->
trust checks -> ModelDecision artifact -> actuator step
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence


MODEL_DECISION_SCHEMA = "arc_agi3.model_decision.v001"
INTERNAL_THINKING_LOCK_SCHEMA = "arc_agi3.internal_thinking_lock.v001"
NEMO3_FINAL_CONFIRMATION_SCHEMA = "arc_agi3.nemo3_final_confirmation.v001"
NEMO3_INTERIM_CONFIRMATION_SCHEMA = "arc_agi3.nemo3_interim_confirmation.v001"
CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA = "chronometric.game_knowledge_link.v001"
MLP_CONSULTATION_SCHEMA = "arc_agi3.mlp_consultation.v001"
INTERNAL_FORWARD_ROLLOUT_SCHEMA = "arc_agi3.internal_forward_rollout.v001"
CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE = "nanowm_action_conditioned_transformer"
CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION = "ChronometricCalibrationMLP+branch_library_fallback"
CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE = "NanoWM.score_chronometric_branch"
SELECTED_ACTION_SOURCE = "world_model_internal_thinking"
STANDARD_MODEL_FLOW = (
    "observation",
    "world_state_3d",
    "chronometric_game_knowledge",
    "mlp_consultation",
    "internal_forward_rollout",
    "internal_branch_simulation",
    "trust_checks",
    "internal_thinking_lock",
    "nemo3_final_confirmation",
    "model_decision",
    "actuator_step",
)
REQUIRED_MODEL_FLOW_ARTIFACTS = (
    "observation_artifact",
    "world_state_3d_artifact",
    "chronometric_game_knowledge_artifact",
    "mlp_consultation_artifact",
    "internal_forward_rollout_artifact",
    "branch_simulation_artifact",
    "trust_checks_artifact",
    "internal_thinking_artifact",
    "nemo3_final_confirmation_artifact",
    "model_decision_artifact",
)
REQUIRED_TRUST_FLAGS = (
    "map_trusted",
    "geometry_trusted",
    "ray_trusted",
    "temporal_trusted",
    "branch_selection_trusted",
)


class ModelDecisionError(ValueError):
    """Raised when an ARC action is not backed by the standard model flow."""


def load_model_decision(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_standard_model_decision(
    decision: dict[str, Any],
    *,
    available_action_values: Sequence[int],
    require_internal_solve: bool = False,
) -> dict[str, Any]:
    """Validate and return the selected actuator action.

    This is deliberately fail-closed. Missing Nemo3/world-model evidence is not
    a warning or optional preflight; it means there is no action.
    """
    failures = model_decision_failures(
        decision,
        available_action_values=available_action_values,
        require_internal_solve=require_internal_solve,
    )
    if failures:
        raise ModelDecisionError("; ".join(failures))
    return dict(decision["selected_action"])


def model_decision_failures(
    decision: dict[str, Any],
    *,
    available_action_values: Sequence[int],
    require_internal_solve: bool = False,
) -> list[str]:
    failures: list[str] = []
    if decision.get("schema") != MODEL_DECISION_SCHEMA:
        failures.append(f"schema must be {MODEL_DECISION_SCHEMA}")

    flow = _dict(decision.get("standard_model_flow"))
    if tuple(flow.get("sequence") or ()) != STANDARD_MODEL_FLOW:
        failures.append("standard_model_flow.sequence must match the canonical model flow")
    for key in REQUIRED_MODEL_FLOW_ARTIFACTS:
        if not _non_empty_string(flow.get(key)):
            failures.append(f"standard_model_flow.{key} is required")

    nemo3 = _dict(decision.get("nemo3"))
    game_knowledge = _dict(decision.get("chronometric_game_knowledge"))
    mlp_consultation = _dict(decision.get("mlp_consultation"))
    forward_rollout = _dict(decision.get("internal_forward_rollout"))
    trust = _dict(decision.get("trust"))
    for key in REQUIRED_TRUST_FLAGS:
        if trust.get(key) is not True:
            failures.append(f"trust.{key} must be true")

    selected = _dict(decision.get("selected_action"))
    internal_lock = _dict(decision.get("internal_thinking_lock"))
    action_value = selected.get("action_value")
    if selected.get("source") != SELECTED_ACTION_SOURCE:
        failures.append(f"selected_action.source must be {SELECTED_ACTION_SOURCE}")
    if not isinstance(action_value, int) or isinstance(action_value, bool):
        failures.append("selected_action.action_value must be an integer")
    elif action_value not in {int(value) for value in available_action_values}:
        failures.append(f"selected_action.action_value {action_value} is not available")
    if not _non_empty_string(selected.get("action_name")):
        failures.append("selected_action.action_name is required")

    failures.extend(_chronometric_game_knowledge_failures(game_knowledge, flow=flow))
    failures.extend(_mlp_consultation_failures(mlp_consultation, flow=flow))
    failures.extend(
        _internal_forward_rollout_failures(
            forward_rollout,
            flow=flow,
            selected_action_value=action_value,
            require_internal_solve=require_internal_solve,
        )
    )
    failures.extend(_internal_thinking_lock_failures(internal_lock, flow=flow, selected_action_value=action_value))
    failures.extend(_nemo3_confirmation_failures(nemo3, flow=flow, lock=internal_lock, selected_action_value=action_value))

    if not _non_empty_string(decision.get("state_id")):
        failures.append("state_id is required")
    if not _non_empty_string(decision.get("decision_id")):
        failures.append("decision_id is required")
    return failures


def actuator_reasoning_from_model_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy": "standard_nemo3_world_model_flow",
        "decision_id": decision.get("decision_id"),
        "state_id": decision.get("state_id"),
        "schema": decision.get("schema"),
        "standard_model_flow": list(STANDARD_MODEL_FLOW),
        "nemo3_invoked": _dict(decision.get("nemo3")).get("invoked") is True,
        "nemo3_final_confirmation": _dict(_dict(decision.get("nemo3")).get("final_confirmation")).get("artifact"),
        "nemo3_final_confirmation_sha256": _dict(_dict(decision.get("nemo3")).get("final_confirmation")).get("sha256"),
        "nemo3_interim_confirmation_count": len(_list(_dict(decision.get("nemo3")).get("interim_confirmations"))),
        "chronometric_game_knowledge": _dict(decision.get("chronometric_game_knowledge")).get("artifact"),
        "chronometric_game_knowledge_sha256": _dict(decision.get("chronometric_game_knowledge")).get("sha256"),
        "chronometric_game_knowledge_score_surface": _dict(decision.get("chronometric_game_knowledge")).get(
            "score_surface"
        ),
        "mlp_consultation": _dict(decision.get("mlp_consultation")).get("artifact"),
        "mlp_consultation_sha256": _dict(decision.get("mlp_consultation")).get("sha256"),
        "mlp_consultation_surface": _dict(decision.get("mlp_consultation")).get("calibration_surface"),
        "mlp_post_action_update_context_count": _dict(decision.get("mlp_consultation")).get(
            "post_action_update_candidate_context_count",
            0,
        ),
        "mlp_post_action_update_context_sha256": _dict(decision.get("mlp_consultation")).get(
            "post_action_update_candidate_context_sha256"
        ),
        "internal_forward_rollout": _dict(decision.get("internal_forward_rollout")).get("artifact"),
        "internal_forward_rollout_sha256": _dict(decision.get("internal_forward_rollout")).get("sha256"),
        "internal_forward_rollout_kernel_supported": _dict(decision.get("internal_forward_rollout")).get(
            "kernel_supported"
        ),
        "internal_forward_rollout_solves_before_first_step": _dict(decision.get("internal_forward_rollout")).get(
            "solves_before_first_step"
        ),
        "internal_forward_rollout_selected_prediction": _dict(decision.get("internal_forward_rollout")).get(
            "selected_candidate_prediction"
        ),
        "internal_thinking_lock": _dict(decision.get("internal_thinking_lock")).get("artifact"),
        "internal_thinking_sha256": _dict(decision.get("internal_thinking_lock")).get("sha256"),
        "model_decision_artifact": _dict(decision.get("standard_model_flow")).get("model_decision_artifact"),
        "submit_online": False,
        "scorecard_submission": False,
        "arc_solve_claim": False,
    }


def _chronometric_game_knowledge_failures(knowledge: dict[str, Any], *, flow: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if knowledge.get("schema") != CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA:
        failures.append(f"chronometric_game_knowledge.schema must be {CHRONOMETRIC_GAME_KNOWLEDGE_SCHEMA}")
    if not _non_empty_string(knowledge.get("artifact")):
        failures.append("chronometric_game_knowledge.artifact is required")
    elif knowledge.get("artifact") != flow.get("chronometric_game_knowledge_artifact"):
        failures.append(
            "chronometric_game_knowledge.artifact must match "
            "standard_model_flow.chronometric_game_knowledge_artifact"
        )
    if not _sha256_string(knowledge.get("sha256")):
        failures.append("chronometric_game_knowledge.sha256 must be a 64-character lowercase hex digest")
    if knowledge.get("backbone_surface") != CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE:
        failures.append(f"chronometric_game_knowledge.backbone_surface must be {CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE}")
    if knowledge.get("calibration_surface") != CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION:
        failures.append(
            f"chronometric_game_knowledge.calibration_surface must be {CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION}"
        )
    if knowledge.get("score_surface") != CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE:
        failures.append(f"chronometric_game_knowledge.score_surface must be {CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE}")
    for key in (
        "swiglu_backbone_linked",
        "action_embedding_context_linked",
        "calibration_mlp_linked",
        "branch_library_linked",
        "drives_branch_simulation",
        "created_before_internal_branch_simulation",
        "updates_from_post_action_calibration_only",
        "online_update_requires_promotion_condition",
    ):
        if knowledge.get(key) is not True:
            failures.append(f"chronometric_game_knowledge.{key} must be true")
    if knowledge.get("heldout_labels_used") is not False:
        failures.append("chronometric_game_knowledge.heldout_labels_used must be false")
    domains = _list(knowledge.get("knowledge_domains"))
    for domain in ("basic_movement", "known_interactions", "branch_value_calibration"):
        if domain not in domains:
            failures.append(f"chronometric_game_knowledge.knowledge_domains must include {domain}")
    return failures


def _mlp_consultation_failures(consultation: dict[str, Any], *, flow: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if consultation.get("schema") != MLP_CONSULTATION_SCHEMA:
        failures.append(f"mlp_consultation.schema must be {MLP_CONSULTATION_SCHEMA}")
    if not _non_empty_string(consultation.get("artifact")):
        failures.append("mlp_consultation.artifact is required")
    elif consultation.get("artifact") != flow.get("mlp_consultation_artifact"):
        failures.append("mlp_consultation.artifact must match standard_model_flow.mlp_consultation_artifact")
    if not _sha256_string(consultation.get("sha256")):
        failures.append("mlp_consultation.sha256 must be a 64-character lowercase hex digest")
    if consultation.get("backbone_surface") != CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE:
        failures.append(f"mlp_consultation.backbone_surface must be {CHRONOMETRIC_GAME_KNOWLEDGE_BACKBONE}")
    if consultation.get("calibration_surface") != CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION:
        failures.append(f"mlp_consultation.calibration_surface must be {CHRONOMETRIC_GAME_KNOWLEDGE_CALIBRATION}")
    if consultation.get("score_surface") != CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE:
        failures.append(f"mlp_consultation.score_surface must be {CHRONOMETRIC_GAME_KNOWLEDGE_SCORE_SURFACE}")
    for key in (
        "consulted_before_branch_simulation",
        "drives_branch_simulation",
        "action_embedding_context_linked",
        "calibration_mlp_linked",
        "branch_library_context_linked",
        "updates_from_post_action_only",
        "online_update_requires_promotion_condition",
    ):
        if consultation.get(key) is not True:
            failures.append(f"mlp_consultation.{key} must be true")
    if consultation.get("heldout_labels_used") is not False:
        failures.append("mlp_consultation.heldout_labels_used must be false")
    if not _list(consultation.get("candidate_priors")):
        failures.append("mlp_consultation.candidate_priors must be non-empty")
    return failures


def _internal_forward_rollout_failures(
    rollout: dict[str, Any],
    *,
    flow: dict[str, Any],
    selected_action_value: Any,
    require_internal_solve: bool,
) -> list[str]:
    failures: list[str] = []
    if rollout.get("schema") != INTERNAL_FORWARD_ROLLOUT_SCHEMA:
        failures.append(f"internal_forward_rollout.schema must be {INTERNAL_FORWARD_ROLLOUT_SCHEMA}")
    if not _non_empty_string(rollout.get("artifact")):
        failures.append("internal_forward_rollout.artifact is required")
    elif rollout.get("artifact") != flow.get("internal_forward_rollout_artifact"):
        failures.append(
            "internal_forward_rollout.artifact must match "
            "standard_model_flow.internal_forward_rollout_artifact"
        )
    if not _sha256_string(rollout.get("sha256")):
        failures.append("internal_forward_rollout.sha256 must be a 64-character lowercase hex digest")
    if rollout.get("created_before_actuator_step") is not True:
        failures.append("internal_forward_rollout.created_before_actuator_step must be true")
    if not _non_empty_string(rollout.get("kernel_surface")):
        failures.append("internal_forward_rollout.kernel_surface is required")
    candidate_count = rollout.get("candidate_count")
    if not isinstance(candidate_count, int) or isinstance(candidate_count, bool) or candidate_count <= 0:
        failures.append("internal_forward_rollout.candidate_count must be a positive integer")
    if not _list(rollout.get("candidate_rollout_refs")):
        failures.append("internal_forward_rollout.candidate_rollout_refs must be non-empty")

    selected_prediction = _dict(rollout.get("selected_candidate_prediction"))
    if not selected_prediction:
        failures.append("internal_forward_rollout.selected_candidate_prediction is required")
    else:
        if selected_prediction.get("action_value") != selected_action_value:
            failures.append(
                "internal_forward_rollout.selected_candidate_prediction.action_value must match "
                "selected_action.action_value"
            )
        for field in (
            "prediction_supported",
            "kernel_supported",
            "predicted_next_state",
            "predicted_level_delta",
            "predicted_solved",
            "predicted_solved_by_plan",
            "predicted_next_frame_sha256",
            "rollout_steps",
        ):
            if field not in selected_prediction:
                failures.append(f"internal_forward_rollout.selected_candidate_prediction.{field} is required")

    planned_values = _list(rollout.get("planned_action_values"))
    if rollout.get("solves_before_first_step") is True:
        if not planned_values:
            failures.append("internal_forward_rollout.planned_action_values must be non-empty when solved")
        elif isinstance(selected_action_value, int) and planned_values[0] != selected_action_value:
            failures.append(
                "internal_forward_rollout.planned_action_values[0] must match selected_action.action_value"
            )

    if require_internal_solve:
        if rollout.get("kernel_supported") is not True:
            failures.append("internal_forward_rollout.kernel_supported must be true before actuator step")
        if rollout.get("solves_before_first_step") is not True:
            failures.append("internal_forward_rollout.solves_before_first_step must be true before actuator step")
        if selected_prediction.get("prediction_supported") is not True:
            failures.append(
                "internal_forward_rollout.selected_candidate_prediction.prediction_supported must be true "
                "before actuator step"
            )
        if selected_prediction.get("predicted_solved_by_plan") is not True:
            failures.append(
                "internal_forward_rollout.selected_candidate_prediction.predicted_solved_by_plan must be true "
                "before actuator step"
            )
    return failures


def _internal_thinking_lock_failures(
    lock: dict[str, Any],
    *,
    flow: dict[str, Any],
    selected_action_value: Any,
) -> list[str]:
    failures: list[str] = []
    if lock.get("schema") != INTERNAL_THINKING_LOCK_SCHEMA:
        failures.append(f"internal_thinking_lock.schema must be {INTERNAL_THINKING_LOCK_SCHEMA}")
    if lock.get("locked") is not True:
        failures.append("internal_thinking_lock.locked must be true")
    if lock.get("drives_selected_action") is not True:
        failures.append("internal_thinking_lock.drives_selected_action must be true")
    if lock.get("created_before_actuator_step") is not True:
        failures.append("internal_thinking_lock.created_before_actuator_step must be true")
    if not _non_empty_string(lock.get("artifact")):
        failures.append("internal_thinking_lock.artifact is required")
    elif lock.get("artifact") != flow.get("internal_thinking_artifact"):
        failures.append("internal_thinking_lock.artifact must match standard_model_flow.internal_thinking_artifact")
    if not _sha256_string(lock.get("sha256")):
        failures.append("internal_thinking_lock.sha256 must be a 64-character lowercase hex digest")
    locked_value = lock.get("selected_action_value")
    if isinstance(selected_action_value, int) and locked_value != selected_action_value:
        failures.append("internal_thinking_lock.selected_action_value must match selected_action.action_value")
    return failures


def _nemo3_confirmation_failures(
    nemo3: dict[str, Any],
    *,
    flow: dict[str, Any],
    lock: dict[str, Any],
    selected_action_value: Any,
) -> list[str]:
    failures: list[str] = []
    if nemo3.get("invoked") is not True:
        failures.append("nemo3.invoked must be true")
    if nemo3.get("role") != "confirmation_not_action_source":
        failures.append("nemo3.role must be confirmation_not_action_source")
    if nemo3.get("decision_delegated_to_nemo") is not False:
        failures.append("nemo3.decision_delegated_to_nemo must be false")

    policy = _dict(nemo3.get("interim_confirmation_policy"))
    if policy.get("call_on_ambiguity_or_open_questions") is not True:
        failures.append("nemo3.interim_confirmation_policy.call_on_ambiguity_or_open_questions must be true")

    final = _dict(nemo3.get("final_confirmation"))
    if final.get("schema") != NEMO3_FINAL_CONFIRMATION_SCHEMA:
        failures.append(f"nemo3.final_confirmation.schema must be {NEMO3_FINAL_CONFIRMATION_SCHEMA}")
    if not _non_empty_string(final.get("artifact")):
        failures.append("nemo3.final_confirmation.artifact is required")
    elif final.get("artifact") != flow.get("nemo3_final_confirmation_artifact"):
        failures.append("nemo3.final_confirmation.artifact must match standard_model_flow.nemo3_final_confirmation_artifact")
    if not _sha256_string(final.get("sha256")):
        failures.append("nemo3.final_confirmation.sha256 must be a 64-character lowercase hex digest")
    if final.get("created_after_internal_thinking_lock") is not True:
        failures.append("nemo3.final_confirmation.created_after_internal_thinking_lock must be true")
    if final.get("created_before_actuator_step") is not True:
        failures.append("nemo3.final_confirmation.created_before_actuator_step must be true")
    if final.get("confirms_selected_action") is not True:
        failures.append("nemo3.final_confirmation.confirms_selected_action must be true")
    if final.get("nemo_supplied_action") is not False:
        failures.append("nemo3.final_confirmation.nemo_supplied_action must be false")
    if isinstance(selected_action_value, int) and final.get("selected_action_value") != selected_action_value:
        failures.append("nemo3.final_confirmation.selected_action_value must match selected_action.action_value")

    interim_confirmations = _list(nemo3.get("interim_confirmations"))
    ambiguity_detected = lock.get("ambiguity_detected") is True or bool(_list(lock.get("open_question_ids")))
    if ambiguity_detected and not interim_confirmations:
        failures.append("nemo3.interim_confirmations are required when internal thinking records ambiguity or open questions")
    for index, confirmation in enumerate(interim_confirmations):
        failures.extend(_interim_confirmation_failures(index, _dict(confirmation)))
    return failures


def _interim_confirmation_failures(index: int, confirmation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    prefix = f"nemo3.interim_confirmations[{index}]"
    if confirmation.get("schema") != NEMO3_INTERIM_CONFIRMATION_SCHEMA:
        failures.append(f"{prefix}.schema must be {NEMO3_INTERIM_CONFIRMATION_SCHEMA}")
    if not _non_empty_string(confirmation.get("artifact")):
        failures.append(f"{prefix}.artifact is required")
    if not _sha256_string(confirmation.get("sha256")):
        failures.append(f"{prefix}.sha256 must be a 64-character lowercase hex digest")
    if not _non_empty_string(confirmation.get("question_id")):
        failures.append(f"{prefix}.question_id is required")
    if confirmation.get("created_during_internal_thinking") is not True:
        failures.append(f"{prefix}.created_during_internal_thinking must be true")
    if confirmation.get("role") != "ambiguity_or_question_confirmation":
        failures.append(f"{prefix}.role must be ambiguity_or_question_confirmation")
    return failures


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha256_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )
