import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "build_dream_kernel_branch_rank_goal.py"
    spec = importlib.util.spec_from_file_location("build_dream_kernel_branch_rank_goal", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_cases_selects_only_reachable_solved_branch_rank_mismatches():
    module = _load_module()
    rows = [
        _row(index=1, failure_reason="branch_rank_top_mismatch", reachable=True, solved=True),
        _row(index=2, failure_reason="branch_rank_top_mismatch", reachable=False, solved=False),
        _row(index=3, failure_reason="passed_proxy_gate", reachable=True, solved=True),
    ]

    cases = module.build_cases(rows)

    assert len(cases) == 1
    assert cases[0]["case_id"] == "branch_rank_goal:0001"
    assert cases[0]["terminal_positive_branch_rank_before"] == 5
    assert cases[0]["required_margin_delta"] > rows[0]["branch_rank_gap_to_top"]
    assert cases[0]["target_terminal_positive_branch_rank"] == 1
    assert cases[0]["training_data_promoted"] is False
    assert "source_arc_answer" in cases[0]["forbidden_inputs"]


def test_goal_run_writes_condition_goal_metrics_and_cases(tmp_path):
    module = _load_module()
    eval_rows = tmp_path / "rows.jsonl"
    eval_metrics = tmp_path / "metrics.json"
    out_dir = tmp_path / "goal"
    rows = [_row(index=4, failure_reason="branch_rank_top_mismatch", reachable=True, solved=True)]
    eval_rows.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    eval_metrics.write_text(
        json.dumps(
            {
                "aggregate": {
                    "overall": {
                        "proxy_goal_solve_rate": 0.99,
                        "planner_integrity_pass_rate": 0.49,
                        "branch_rank_top_match_rate": 0.49,
                        "terminal_branch_rank_counts": {"1": 23, "5": 48},
                    },
                    "failure_reasons": {"branch_rank_top_mismatch": 48},
                }
            }
        ),
        encoding="utf-8",
    )

    metrics = module.run(
        argparse.Namespace(
            eval_rows=eval_rows,
            eval_metrics=eval_metrics,
            out_dir=out_dir,
            run_label="test_goal_v035",
        )
    )

    assert metrics["calibration_case_count"] == 1
    assert metrics["ready_for_goal_loop"] is True
    assert metrics["goal"]["success_criteria"]["planner_integrity_pass_rate"] == 1.0
    assert (out_dir / "condition.json").exists()
    assert (out_dir / "goal.json").exists()
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "calibration_cases.jsonl").exists()
    assert "branch-value calibration target" in (out_dir / "RESULTS.md").read_text(encoding="utf-8")


def _row(*, index: int, failure_reason: str, reachable: bool, solved: bool):
    return {
        "challenge_id": f"arcdream:{index}",
        "curriculum_index": index,
        "tier_label": "t2_action_coordinate",
        "failure_reason": failure_reason,
        "proxy_goal_reachable_avoiding_hazard": reachable,
        "proxy_goal_solved": solved,
        "sequence_path": f"seq/{index}.json",
        "map_path": f"maps/{index}.txt",
        "source": {"task_id": f"task{index}"},
        "quarantine_status": "control_source: arc_scaffold_non_chronometric",
        "terminal_positive_branch_id": f"tick{index}.move",
        "terminal_positive_branch_rank": 5,
        "terminal_positive_branch_chrono_y_net": 0.343425,
        "top_branch_id": f"tick{index - 1}.move",
        "top_branch_chrono_y_net": 1.0,
        "branch_rank_gap_to_top": 0.656575,
    }
