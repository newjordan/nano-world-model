import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_dream_kernel_branch_choice_smoke.py"
    spec = importlib.util.spec_from_file_location("run_dream_kernel_branch_choice_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_decision_rows_score_policy_against_safe_path_oracle(tmp_path):
    module = _load_module()
    source_row = _source_row()
    scenario = {
        "decision_trace": [
            {
                "tick_before": 0,
                "agent_position": {"x": 1, "y": 1, "z": 0},
                "selected_action_id": "move_entity_0_dx1_dy0_dz0",
                "candidates": [
                    _candidate(
                        "move_entity_0_dx1_dy0_dz0",
                        policy=0.9,
                        branch=0.8,
                        accepted=True,
                        next_position={"x": 2, "y": 1, "z": 0},
                    ),
                    _candidate(
                        "move_entity_0_dx0_dy1_dz0",
                        policy=0.1,
                        branch=0.7,
                        accepted=True,
                        next_position={"x": 1, "y": 2, "z": 0},
                    ),
                    _candidate("wait", policy=-0.2, branch=0.3, accepted=True, next_position={"x": 1, "y": 1, "z": 0}),
                ],
            }
        ]
    }

    decisions, candidates = module.decision_rows_from_summary(
        source_row=source_row,
        scenario=scenario,
        map_rows=["#####", "#A.G#", "#...#", "#####"],
        sequence_path=tmp_path / "seq.json",
        summary_path=tmp_path / "summary.json",
    )

    assert len(decisions) == 1
    assert len(candidates) == 3
    assert decisions[0]["oracle_best_action_ids"] == ["move_entity_0_dx1_dy0_dz0"]
    assert decisions[0]["policy_selection_matches_oracle"] is True
    assert decisions[0]["value_selection_matches_oracle"] is True
    assert candidates[0]["safe_path_progress_delta"] == 1


def test_decision_rows_detect_policy_oracle_mismatch(tmp_path):
    module = _load_module()
    source_row = _source_row()
    scenario = {
        "decision_trace": [
            {
                "tick_before": 0,
                "agent_position": {"x": 1, "y": 1, "z": 0},
                "selected_action_id": "wait",
                "candidates": [
                    _candidate(
                        "move_entity_0_dx1_dy0_dz0",
                        policy=0.1,
                        branch=0.9,
                        accepted=True,
                        next_position={"x": 2, "y": 1, "z": 0},
                    ),
                    _candidate("wait", policy=0.5, branch=0.3, accepted=True, next_position={"x": 1, "y": 1, "z": 0}),
                ],
            }
        ]
    }

    decisions, _ = module.decision_rows_from_summary(
        source_row=source_row,
        scenario=scenario,
        map_rows=["#####", "#A.G#", "#...#", "#####"],
        sequence_path=tmp_path / "seq.json",
        summary_path=tmp_path / "summary.json",
    )

    assert decisions[0]["oracle_best_action_ids"] == ["move_entity_0_dx1_dy0_dz0"]
    assert decisions[0]["policy_selection_matches_oracle"] is False
    assert decisions[0]["value_selection_matches_oracle"] is True


def _source_row():
    return {
        "challenge_id": "arcdream:test",
        "curriculum_index": 7,
        "tier_label": "t1_local_translation",
        "map_path": "maps/test.map.txt",
    }


def _candidate(action_id, *, policy, branch, accepted, next_position):
    return {
        "action_id": action_id,
        "policy_score": policy,
        "branch_chrono_y_net": branch,
        "outcome_accepted": accepted,
        "outcome_reward": 0.0,
        "outcome_terminal": False,
        "outcome_reason": "moved into empty" if accepted else "blocked by wall",
        "next_position": next_position,
        "revisit_penalty_applied": False,
        "wait_penalty_applied": action_id == "wait",
        "selected": False,
    }
