import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_dream_curriculum_eval.py"
    spec = importlib.util.spec_from_file_location("run_arc_dream_curriculum_eval", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_eval_row_tracks_proxy_solve_object_ids_and_nemo_relay(tmp_path):
    module = _load_module()
    challenge = _challenge()
    summary = {
        "schema": "dream_kernel.solve_map.v001",
        "scenario": {
            "name": challenge["challenge_id"],
            "solved": True,
            "final_reward": 1.0,
            "terminal": True,
            "steps": 3,
            "planned_actions": ["move_entity_0_dx1_dy0_dz0"],
            "final_reason": "moved into goal",
            "sequence_file": "case.dream_sequence.json",
            "sequence_hash": "hash123",
            "branch_rank_top_match": True,
            "accepted_steps": 3,
            "rejected_steps": 0,
            "invariant_passed": True,
        },
    }
    sequence = {
        "schema": "dream_kernel.sequence.v003",
        "object_registry": [
            {"object_id": "agent"},
            {"object_id": "goal:3:1:0"},
            {"object_id": "wall:0:0:0"},
        ],
        "frames": [
            {
                "outcome": None,
                "rays": [
                    {
                        "network": "beneficial",
                        "contact": {"object_id": "goal:3:1:0", "category_id": "map.terminal.positive"},
                    }
                ]
            },
            {
                "outcome": {"branch_id": "tick2.move_entity_0_dx1_dy0_dz0", "reward": 1.0},
                "rays": [],
            }
        ],
        "branch_matrix": [
            {"branch_id": "tick2.move_entity_0_dx1_dy0_dz0", "chrono_y_net": 1.0},
            {"branch_id": "tick0.move_entity_0_dx1_dy0_dz0", "chrono_y_net": 0.2},
        ],
        "branch_potentials": [{"nemo_relay_required": True}],
        "nemo_relay": {"open_questions": [{"question_id": "q1"}]},
    }

    row = module.eval_row_from_outputs(
        challenge,
        summary,
        sequence,
        tmp_path / "case.map.txt",
        tmp_path / "case.dream_sequence.json",
        tmp_path / "case.solver_summary.json",
        16,
    )

    assert row["schema"] == "dream_kernel.arc_dream_curriculum_eval_row.v001"
    assert row["proxy_goal_solved"] is True
    assert row["planner_integrity_passed"] is True
    assert row["proxy_goal_reachable_avoiding_hazard"] is True
    assert row["proxy_goal_shortest_safe_path_steps"] == 2
    assert row["object_identity_integrity"] is True
    assert row["missing_expected_object_ids"] == []
    assert row["ray_network_counts"] == {"beneficial": 1}
    assert row["terminal_positive_branch_rank"] == 1
    assert row["kernel_nemo_relay_required"] is True
    assert row["source_expected_outcome_aligned"] is True
    assert row["failure_reason"] == "passed_proxy_gate"


def test_aggregate_rows_reports_rates_by_tier():
    module = _load_module()
    passed = {
        "tier_label": "t1_local_translation",
        "proxy_goal_solved": True,
        "proxy_goal_reachable_avoiding_hazard": True,
        "planner_integrity_passed": True,
        "invariant_passed": True,
        "object_identity_integrity": True,
        "branch_rank_top_match": True,
        "accepted_steps": 3,
        "rejected_steps": 0,
        "nemo_policy_callback_required": False,
        "kernel_nemo_relay_required": True,
        "nemo_callback_available_for_policy": True,
        "source_expected_outcome_tested": True,
        "source_expected_outcome_aligned": True,
        "terminal_positive_branch_rank": 1,
        "steps": 3,
        "failure_reason": "passed_proxy_gate",
        "ray_network_counts": {"beneficial": 2},
    }
    failed = dict(passed)
    failed.update(
        {
            "tier_label": "t2_action_coordinate",
            "proxy_goal_solved": False,
            "proxy_goal_reachable_avoiding_hazard": False,
            "planner_integrity_passed": False,
            "branch_rank_top_match": False,
            "accepted_steps": 1,
            "rejected_steps": 1,
            "source_expected_outcome_aligned": False,
            "terminal_positive_branch_rank": None,
            "failure_reason": "proxy_goal_unsolved:blocked by wall",
            "ray_network_counts": {"structural": 3},
        }
    )

    aggregate = module.aggregate_rows([passed, failed])

    assert aggregate["overall"]["challenge_count"] == 2
    assert aggregate["overall"]["proxy_goal_solve_rate"] == 0.5
    assert aggregate["overall"]["proxy_goal_reachable_avoiding_hazard_rate"] == 0.5
    assert aggregate["overall"]["terminal_branch_rank_counts"] == {"1": 1, "none": 1}
    assert aggregate["overall"]["accepted_step_rate"] == 4 / 5
    assert aggregate["by_tier"]["t1_local_translation"]["planner_integrity_pass_rate"] == 1.0
    assert aggregate["by_tier"]["t2_action_coordinate"]["planner_integrity_pass_rate"] == 0.0
    assert aggregate["failure_reasons"]["passed_proxy_gate"] == 1
    assert aggregate["ray_network_totals"] == {"beneficial": 2, "structural": 3}


def test_write_map_rejects_ragged_rows(tmp_path):
    module = _load_module()
    with pytest_raises(ValueError, "equal width"):
        module.write_map(tmp_path / "bad.map.txt", ["###", "#A"])
    good = tmp_path / "good.map.txt"
    module.write_map(good, ["###", "#A#"])
    assert good.read_text(encoding="utf-8") == "###\n#A#\n"


class pytest_raises:
    def __init__(self, error_type, text):
        self.error_type = error_type
        self.text = text
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        assert error_type is self.error_type
        self.error = error
        assert self.text in str(error)
        return True


def _challenge():
    return {
        "challenge_id": "arcdream:testcase",
        "curriculum_index": 0,
        "tier_index": 1,
        "tier_label": "t1_local_translation",
        "difficulty_score": 2.0,
        "quarantine_status": "control_source: arc_scaffold_non_chronometric",
        "source": {"task_id": "task"},
        "dream_kernel_projection": {
            "expected_outcome_class": "positive_goal_progress",
            "object_ids_expected": ["agent", "goal:3:1:0", "wall:0:0:0"],
            "known_map_ascii": ["#####", "#A.G#", "#####"],
        },
        "nemo_callback_policy": {"callback_required": True},
    }
