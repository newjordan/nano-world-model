import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_agi3_model_decision_producer.py"
    spec = importlib.util.spec_from_file_location("run_arc_agi3_model_decision_producer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeInfo:
    game_id = "ls20-9607627b"


class FakeAction:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class FakeEnv:
    info = FakeInfo()

    def __init__(self):
        self.action_space = [FakeAction("ACTION1", 1), FakeAction("ACTION2", 2), FakeAction("ACTION3", 3)]
        self.step_called = False

    def step(self, *_args, **_kwargs):
        self.step_called = True
        raise AssertionError("producer must not call env.step")


class FakeFrame:
    shape = (4, 4)

    def __init__(self):
        self._rows = [
            [0, 0, 1, 0],
            [0, 2, 0, 0],
            [0, 0, 0, 3],
            [4, 0, 0, 0],
        ]

    def tolist(self):
        return self._rows

    def tobytes(self):
        return bytes(value for row in self._rows for value in row)

    def min(self):
        return 0

    def max(self):
        return 4


class FakeObs:
    game_id = "ls20-9607627b"
    guid = "obs-guid"
    state = "NOT_FINISHED"
    levels_completed = 0
    win_levels = 7
    full_reset = True

    def __init__(self):
        self.frame = [FakeFrame()]


def _args(module, *, threshold=0.0):
    return SimpleNamespace(
        run_label="test_model_decision_v047",
        branch_ambiguity_gap_threshold=threshold,
        nemo_mode=module.LOCAL_NEMO_MODE,
        nemo_model="test-nemo",
        nemo_relay_url="http://127.0.0.1:8000/v1/responses",
        nemo_timeout=1,
    )


def _condition(module, selected_game):
    return {
        "schema": module.SCHEMA,
        "run_label": "test_model_decision_v047",
        "run_kind": "arc_agi3_reset_only_model_decision_producer",
        "source_condition_artifact": "docs/arc-agi-3-env.md",
        "dataset_path": "environment_files",
        "operation_mode": "OFFLINE",
        "selected_game": selected_game,
        "nemo_mode": module.LOCAL_NEMO_MODE,
        "metric_to_compare": "arc_agi3_valid_model_decision_artifact_and_zero_actuator_steps",
        "arc_solve_claim": False,
        "online_submission": False,
    }


def _produce(module, tmp_path, *, threshold=0.0, prior_update_refs=None):
    env = FakeEnv()
    obs = FakeObs()
    selected_game = {"game_id": "ls20-9607627b", "name": "ls20", "title": "LS20"}
    packets = module.candidate_action_packets(
        env=env,
        game_name="ls20",
        observation_guid=obs.guid,
        phase="model_decision_pre_action",
        max_actions=3,
    )
    metrics = module.write_model_decision_artifacts(
        args=_args(module, threshold=threshold),
        out_dir=tmp_path,
        games=[selected_game],
        selected_game=selected_game,
        env=env,
        reset_obs=obs,
        candidate_packets=packets,
        condition=_condition(module, selected_game),
        prior_post_action_mlp_updates=prior_update_refs,
    )
    return env, metrics, json.loads((tmp_path / "model_decision.json").read_text(encoding="utf-8"))


def test_model_decision_producer_writes_valid_artifact_chain_without_actuator_step(tmp_path):
    module = _load_module()

    env, metrics, decision = _produce(module, tmp_path)

    selected = module.require_standard_model_decision(decision, available_action_values=[1, 2, 3])
    assert selected["source"] == module.SELECTED_ACTION_SOURCE
    assert metrics["valid_standard_model_decision"] is True
    assert metrics["actuator_steps_executed"] == 0
    assert metrics["selected_action"] == f"{selected['action_name']}:{selected['action_value']}"
    assert env.step_called is False
    assert (tmp_path / "observation.json").exists()
    assert (tmp_path / "world_state_3d.json").exists()
    assert (tmp_path / "chronometric_game_knowledge.json").exists()
    assert (tmp_path / "mlp_consultation.json").exists()
    assert (tmp_path / "branch_simulation.json").exists()
    assert (tmp_path / "trust_checks.json").exists()
    assert (tmp_path / "internal_thinking_lock.json").exists()
    assert (tmp_path / "nemo3_final_confirmation.json").exists()


def test_contract_local_nemo_mode_is_explicit_not_external_model(tmp_path):
    module = _load_module()

    _env, metrics, decision = _produce(module, tmp_path)
    final_artifact = json.loads((tmp_path / "nemo3_final_confirmation.json").read_text(encoding="utf-8"))

    assert decision["nemo3"]["invoked"] is True
    assert decision["nemo3"]["confirmation_mode"] == module.LOCAL_NEMO_MODE
    assert decision["nemo3"]["external_nemo3_model_invoked"] is False
    assert final_artifact["external_nemo3_model_invoked"] is False
    assert final_artifact["confirmation_mode"] == module.LOCAL_NEMO_MODE
    assert metrics["nemo3_external_model_invoked"] is False


def test_ambiguous_branch_selection_creates_interim_nemo_confirmation(tmp_path):
    module = _load_module()

    _env, metrics, decision = _produce(module, tmp_path, threshold=2.0)

    assert metrics["nemo3_interim_confirmation_count"] == 1
    assert decision["internal_thinking_lock"]["ambiguity_detected"] is True
    assert decision["internal_thinking_lock"]["open_question_ids"] == ["branch_selection_gap"]
    assert decision["nemo3"]["interim_confirmations"][0]["question_id"] == "branch_selection_gap"
    module.require_standard_model_decision(decision, available_action_values=[1, 2, 3])


def test_mlp_consultation_can_consume_prior_post_action_update_candidate(tmp_path):
    module = _load_module()
    prior_update = {
        "artifact": "experiments/run/step_000/post_action_mlp_update.json",
        "sha256": "f" * 64,
        "source_step_index": 0,
        "update_mode": "candidate-only",
        "mlp_weights_updated": False,
        "training_data_promoted": False,
    }

    _env, metrics, decision = _produce(module, tmp_path, prior_update_refs=[prior_update])
    consultation = decision["mlp_consultation"]

    assert metrics["mlp_post_action_update_context_count"] == 1
    assert consultation["post_action_update_candidate_context_count"] == 1
    assert consultation["prior_post_action_update_candidates"] == [prior_update]
    assert consultation["post_action_update_candidate_context_sha256"]
    assert all("prior_components" in row for row in consultation["candidate_priors"])


def test_parse_nemo_json_response_accepts_plain_or_fenced_json():
    module = _load_module()

    plain = module.parse_nemo_json_response('{"confirms_selected_action": true}')
    fenced = module.parse_nemo_json_response('```json\n{"confirms_selected_action": true}\n```')

    assert plain["confirms_selected_action"] is True
    assert fenced["confirms_selected_action"] is True
