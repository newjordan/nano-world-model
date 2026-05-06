import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_agi3_model_solve_scout.py"
    spec = importlib.util.spec_from_file_location("run_arc_agi3_model_solve_scout", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeObs:
    def __init__(self, *, state="NOT_FINISHED", levels_completed=0, win_levels=7):
        self.state = state
        self.levels_completed = levels_completed
        self.win_levels = win_levels


def _condition():
    return {
        "selected_game": {"game_id": "ls20-9607627b", "name": "ls20"},
        "online_submission": False,
        "scorecard_submission": False,
        "training_data_promoted": False,
    }


def _row(step_index, *, feedback_count):
    return {
        "step_index": step_index,
        "valid_standard_model_decision": True,
        "valid_standard_model_flow_step": True,
        "nemo3_external_model_invoked": True,
        "mlp_weights_updated": False,
        "training_data_promoted": False,
        "levels_completed_start": step_index,
        "selected_action": f"ACTION{step_index + 1}:{step_index + 1}",
        "frame_changed": True,
        "mlp_post_action_update_context_count": feedback_count,
    }


def test_offline_solved_uses_win_state_or_completed_levels():
    module = _load_module()

    assert module.offline_solved(FakeObs(state="WIN", levels_completed=0, win_levels=7)) is True
    assert module.offline_solved(FakeObs(levels_completed=7, win_levels=7)) is True
    assert module.offline_solved(FakeObs(levels_completed=6, win_levels=7)) is False


def test_solve_scout_requires_feedback_context_after_first_step():
    module = _load_module()
    rows = [_row(0, feedback_count=0), _row(1, feedback_count=1)]

    metrics = module.summarize_loop(
        condition=_condition(),
        games=[_condition()["selected_game"]],
        trace_rows=rows,
        candidate_packets=[{"action_value": 1}],
        initial_obs=None,
        final_obs=FakeObs(levels_completed=2, win_levels=7),
        stop_reason="max_steps_exhausted",
        prior_update_refs=[{"artifact": "artifact://update"}],
    )

    assert metrics["valid_model_solve_scout"] is True
    assert metrics["feedback_context_valid"] is True

    rows[1]["mlp_post_action_update_context_count"] = 0
    metrics = module.summarize_loop(
        condition=_condition(),
        games=[_condition()["selected_game"]],
        trace_rows=rows,
        candidate_packets=[{"action_value": 1}],
        initial_obs=None,
        final_obs=FakeObs(levels_completed=2, win_levels=7),
        stop_reason="max_steps_exhausted",
        prior_update_refs=[{"artifact": "artifact://update"}],
    )

    assert metrics["valid_model_solve_scout"] is False
    assert metrics["feedback_context_valid"] is False
