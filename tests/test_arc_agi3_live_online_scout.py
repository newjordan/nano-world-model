import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_agi3_live_online_scout.py"
    spec = importlib.util.spec_from_file_location("run_arc_agi3_live_online_scout", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_env_file_sets_arc_api_key_without_overwriting(monkeypatch, tmp_path):
    module = _load_module()
    env_file = tmp_path / ".env.arc"
    env_file.write_text("ARC_API_KEY=file-key\nIGNORED_LINE\n", encoding="utf-8")
    monkeypatch.delenv("ARC_API_KEY", raising=False)

    loaded = module.load_env_file(env_file)

    assert loaded == {"ARC_API_KEY"}
    assert module.arc_api_key_source(SimpleNamespace(arc_api_key=""), loaded_env_keys=loaded) == "arc_env_file"
    assert "ARC_API_KEY" in loaded

    monkeypatch.setenv("ARC_API_KEY", "preexisting-key")
    env_file.write_text("ARC_API_KEY=new-file-key\n", encoding="utf-8")
    loaded = module.load_env_file(env_file)

    assert loaded == set()
    assert module.arc_api_key_source(SimpleNamespace(arc_api_key=""), loaded_env_keys=loaded) == "environment"


def test_compact_live_reasoning_keeps_world_model_and_nemo_confirmation_refs():
    module = _load_module()
    args = SimpleNamespace(run_label="live-test")
    decision = {
        "schema": "arc_agi3.model_decision.v001",
        "decision_id": "decision-001",
        "state_id": "state-001",
        "selected_action": {"action_name": "ACTION3", "action_value": 3, "source": "internal_thinking_lock"},
        "internal_forward_rollout": {
            "artifact": "artifact://rollout",
            "sha256": "a" * 64,
            "solves_before_first_step": True,
            "kernel_artifact": "artifact://kernel",
            "kernel_sha256": "b" * 64,
            "kernel_simulation_review_artifact": "artifact://review",
            "kernel_simulation_review_sha256": "c" * 64,
        },
        "nemo3": {
            "invoked": True,
            "final_confirmation": {
                "artifact": "artifact://nemo-final",
                "sha256": "d" * 64,
                "confirms_selected_action": True,
                "nemo_supplied_action": False,
            },
        },
    }

    reasoning = module.compact_live_reasoning(
        args=args,
        step_index=7,
        scorecard_id="scorecard-001",
        model_decision=decision,
    )

    assert reasoning["schema"] == "arc_agi3.compact_live_action_reasoning.v001"
    assert reasoning["online_submission"] is True
    assert reasoning["decision_id"] == "decision-001"
    assert reasoning["kernel_simulation_review_artifact"] == "artifact://review"
    assert reasoning["nemo3_final_confirmation"] == "artifact://nemo-final"
    assert reasoning["nemo3_confirms_selected_action"] is True
    assert reasoning["nemo3_supplied_action"] is False


def test_scorecard_payload_redacts_api_key():
    module = _load_module()

    payload = module.scorecard_payload(
        {"score": 1.0, "api_key": "secret-key", "card_id": "scorecard-001"},
        "scorecard-001",
    )

    assert payload["api_key"] == "REDACTED"
    assert payload["scorecard_id"] == "scorecard-001"


def test_compiled_replay_includes_3d_simulation_round_review(tmp_path):
    module = _load_module()
    review_path = tmp_path / "dream_kernel_ls20_simulation_review.json"
    review_path.write_text(
        """
{
  "round_count": 2,
  "frame_count": 5,
  "solved": true,
  "final_state": "WIN",
  "final_levels_completed": 7,
  "win_levels": 7,
  "rounds": [
    {"round_index": 0, "frame_count": 3, "win_after_round": false},
    {"round_index": 1, "frame_count": 2, "win_after_round": true}
  ],
  "completion_frames": [{"round_index": 1, "global_step_after": 5}],
  "frames": [{"review_step_index": 0, "action_value": 3}]
}
""",
        encoding="utf-8",
    )
    condition = {
        "model_name": "Dreamweaver",
        "run_label": "live-test",
        "operation_mode": "ONLINE",
        "selected_game": {"game_id": "ls20-9607627b", "name": "ls20"},
    }
    metrics = {
        "stop_reason": "online_solved_after_step",
        "online_solve_detected": True,
        "official_arc_solve_claim": False,
        "online_actions_executed": 1,
        "levels_completed_final": 7,
        "win_levels_final": 7,
    }
    row = {
        "step_index": 0,
        "selected_action": "ACTION3:3",
        "state_start": "NOT_FINISHED",
        "state_final": "WIN",
        "levels_completed_start": 6,
        "levels_completed_final": 7,
        "frame_sha256": "before",
        "next_frame_sha256": "after",
        "decision_artifact": "artifact://decision",
        "kernel_simulation_review_artifact": str(review_path),
        "kernel_simulation_review_sha256": "e" * 64,
        "mirror_synced_before_step": True,
        "mirror_synced_after_step": True,
    }

    replay = module.compile_live_replay_artifact(
        out_dir=tmp_path,
        condition=condition,
        metrics=metrics,
        trace_rows=[row],
        frame_rows=[],
        scorecard={"scorecard_id": "scorecard-001"},
    )
    html = module.replay_html(replay)

    step = replay["steps"][0]
    assert step["predicted_round_count"] == 2
    assert step["predicted_frame_count"] == 5
    assert step["predicted_solved"] is True
    assert len(step["predicted_rounds"]) == 2
    assert step["predicted_completion_frames"][0]["global_step_after"] == 5
    assert "Predicted Rounds" in html


def test_compiled_replay_tolerates_missing_review_artifact(tmp_path):
    module = _load_module()
    condition = {
        "model_name": "Dreamweaver",
        "run_label": "live-test",
        "operation_mode": "ONLINE",
        "selected_game": {"game_id": "ls20-9607627b", "name": "ls20"},
    }
    metrics = {
        "stop_reason": "gate_block",
        "online_solve_detected": False,
        "official_arc_solve_claim": False,
        "online_actions_executed": 1,
        "levels_completed_final": 0,
        "win_levels_final": 7,
    }
    row = {
        "step_index": 0,
        "selected_action": "ACTION3:3",
        "state_start": "NOT_FINISHED",
        "state_final": "NOT_FINISHED",
        "levels_completed_start": 0,
        "levels_completed_final": 0,
        "frame_sha256": "before",
        "next_frame_sha256": "after",
        "decision_artifact": "artifact://decision",
        "kernel_simulation_review_artifact": "",
        "kernel_simulation_review_sha256": None,
        "mirror_synced_before_step": True,
        "mirror_synced_after_step": True,
    }

    replay = module.compile_live_replay_artifact(
        out_dir=tmp_path,
        condition=condition,
        metrics=metrics,
        trace_rows=[row],
        frame_rows=[],
        scorecard={"scorecard_id": "scorecard-001"},
    )

    assert replay["steps"][0]["predicted_round_count"] is None
