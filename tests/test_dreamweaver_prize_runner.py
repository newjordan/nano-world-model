import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

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
    SELECTED_ACTION_SOURCE,
    STANDARD_MODEL_FLOW,
)
from dreamweaver_prize_runner import PrizeRunnerConfig, run_prize_candidate  # noqa: E402


class FakeGame:
    def __init__(self, game_id):
        self.game_id = game_id
        self.title = game_id.upper()


class FakeAction:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def is_complex(self):
        return self.value >= 5


class FakeInfo:
    def __init__(self, game_id):
        self.game_id = game_id


class FakeFrame:
    shape = (2, 2)

    def __init__(self, value=0):
        self.value = value

    def tolist(self):
        return [[self.value, 0], [0, self.value]]

    def tobytes(self):
        return bytes([self.value, 0, 0, self.value])

    def min(self):
        return 0

    def max(self):
        return self.value


class FakeObs:
    def __init__(self, game_id, step=0, state="NOT_FINISHED", levels_completed=0, win_levels=2):
        self.game_id = game_id
        self.guid = f"{game_id}-guid"
        self.state = state
        self.levels_completed = levels_completed
        self.win_levels = win_levels
        self.full_reset = step == 0
        self.frame = [FakeFrame(step)]


class FakeEnv:
    def __init__(self, game_id, actions=None):
        self.info = FakeInfo(game_id)
        self.action_space = actions or [FakeAction("ACTION1", 1), FakeAction("ACTION2", 2)]
        self.steps = 0
        self.step_reasoning = []

    def reset(self):
        return FakeObs(self.info.game_id, step=0)

    def step(self, action, **kwargs):
        self.steps += 1
        self.step_reasoning.append(kwargs.get("reasoning", {}))
        return FakeObs(
            self.info.game_id,
            step=self.steps,
            state="WIN",
            levels_completed=2,
            win_levels=2,
        )


class FakeArcade:
    def __init__(self, games, actions=None):
        self.games = [FakeGame(game) for game in games]
        self.actions = actions
        self.scorecards_created = 0
        self.scorecards_closed = 0
        self.make_calls = []
        self.get_scorecard_calls = 0
        self.envs = {}

    def get_environments(self):
        return self.games

    def create_scorecard(self, **_kwargs):
        self.scorecards_created += 1
        return "scorecard-001"

    def make(self, game_id, **_kwargs):
        self.make_calls.append(game_id)
        env = FakeEnv(game_id, actions=self.actions)
        self.envs[game_id] = env
        return env

    def get_scorecard(self, *_args, **_kwargs):
        self.get_scorecard_calls += 1
        raise AssertionError("runner must not read inflight scorecard")

    def close_scorecard(self, **_kwargs):
        self.scorecards_closed += 1
        return {"score": 1.0, "api_key": "should-redact"}


class FakeDecisionSource:
    def __init__(self, action_value=1):
        self.action_value = action_value

    def build_model_decision(
        self,
        *,
        env,
        obs,
        selected_game,
        games,
        candidate_packets,
        step_dir,
        config,
        prior_post_action_mlp_updates,
    ):
        decision = _valid_decision(action_value=self.action_value)
        (step_dir / "model_decision.json").write_text(json.dumps(decision), encoding="utf-8")
        return decision


def test_prize_runner_uses_one_scorecard_all_envs_one_make_no_inflight_scorecard_reads(tmp_path):
    arcade = FakeArcade(["aa11-test", "bb22-test"])
    metrics = run_prize_candidate(
        arcade=arcade,
        config=PrizeRunnerConfig(out_dir=tmp_path / "run", max_actions_per_environment=2),
        decision_source=FakeDecisionSource(),
    )

    assert arcade.scorecards_created == 1
    assert arcade.scorecards_closed == 1
    assert arcade.get_scorecard_calls == 0
    assert arcade.make_calls == ["aa11", "bb22"]
    assert metrics["all_environment_runner"] is True
    assert metrics["one_make_per_environment"] is True
    assert metrics["single_scorecard"] is True
    assert metrics["external_api_used"] is False
    assert metrics["source_env_solver_used"] is False
    assert metrics["offline_mirror_used"] is False
    assert metrics["nemo3_external_model_invocations"] == 0
    assert (tmp_path / "run" / "condition.json").exists()
    assert (tmp_path / "run" / "trace.jsonl").exists()

    scorecard = json.loads((tmp_path / "run" / "scorecard_final.json").read_text(encoding="utf-8"))
    assert scorecard["api_key"] == "REDACTED"


def test_prize_runner_reasoning_marks_no_external_api_or_source_solver(tmp_path):
    arcade = FakeArcade(["aa11-test"])
    run_prize_candidate(
        arcade=arcade,
        config=PrizeRunnerConfig(out_dir=tmp_path / "run", max_actions_per_environment=1),
        decision_source=FakeDecisionSource(),
    )

    reasoning = arcade.envs["aa11"].step_reasoning[0]
    assert reasoning["external_api_used"] is False
    assert reasoning["source_env_solver_used"] is False
    assert reasoning["offline_mirror_used"] is False
    assert reasoning["policy"] == "local_3d_world_model_internal_lock_then_local_confirmation"


def test_prize_runner_blocks_complex_action_without_action_data(tmp_path):
    arcade = FakeArcade(["aa11-test"], actions=[FakeAction("ACTION6", 6)])
    metrics = run_prize_candidate(
        arcade=arcade,
        config=PrizeRunnerConfig(out_dir=tmp_path / "run", max_actions_per_environment=1),
        decision_source=FakeDecisionSource(action_value=6),
    )

    assert metrics["actions_executed"] == 0
    assert arcade.envs["aa11"].steps == 0
    trace = (tmp_path / "run" / "trace.jsonl").read_text(encoding="utf-8")
    assert "missing_complex_action_data_before_step" in trace


def _valid_decision(action_value=1):
    return {
        "schema": MODEL_DECISION_SCHEMA,
        "decision_id": "decision-001",
        "state_id": "state-001",
        "standard_model_flow": {
            "sequence": list(STANDARD_MODEL_FLOW),
            "observation_artifact": "artifact://obs",
            "world_state_3d_artifact": "artifact://world3d",
            "chronometric_game_knowledge_artifact": "artifact://game-knowledge",
            "mlp_consultation_artifact": "artifact://mlp-consultation",
            "internal_forward_rollout_artifact": "artifact://forward-rollout",
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
        "internal_forward_rollout": {
            "schema": INTERNAL_FORWARD_ROLLOUT_SCHEMA,
            "artifact": "artifact://forward-rollout",
            "sha256": "f" * 64,
            "created_before_actuator_step": True,
            "kernel_surface": "dream_kernel.arc_grid_scout.v001",
            "kernel_supported": True,
            "solves_before_first_step": False,
            "planned_action_values": [],
            "candidate_count": 1,
            "candidate_rollout_refs": [
                {
                    "action_value": action_value,
                    "prediction_supported": True,
                    "kernel_supported": True,
                    "predicted_next_state": "NOT_FINISHED",
                    "predicted_level_delta": 0,
                    "predicted_solved": False,
                    "predicted_solved_by_plan": False,
                    "predicted_next_frame_sha256": "c" * 64,
                    "rollout_steps": 1,
                }
            ],
            "selected_candidate_prediction": {
                "action_value": action_value,
                "prediction_supported": True,
                "kernel_supported": True,
                "predicted_next_state": "NOT_FINISHED",
                "predicted_level_delta": 0,
                "predicted_solved": False,
                "predicted_solved_by_plan": False,
                "predicted_next_frame_sha256": "c" * 64,
                "rollout_steps": 1,
            },
        },
        "internal_thinking_lock": {
            "schema": INTERNAL_THINKING_LOCK_SCHEMA,
            "artifact": "artifact://internal-thinking",
            "sha256": "a" * 64,
            "locked": True,
            "drives_selected_action": True,
            "created_before_actuator_step": True,
            "selected_action_value": action_value,
            "ambiguity_detected": False,
            "open_question_ids": [],
        },
        "nemo3": {
            "invoked": True,
            "role": "confirmation_not_action_source",
            "decision_delegated_to_nemo": False,
            "confirmation_mode": "contract-local",
            "external_nemo3_model_invoked": False,
            "interim_confirmation_policy": {"call_on_ambiguity_or_open_questions": True},
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
