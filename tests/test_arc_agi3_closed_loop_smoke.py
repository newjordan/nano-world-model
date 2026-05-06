import importlib.util
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_agi3_closed_loop_smoke.py"
    spec = importlib.util.spec_from_file_location("run_arc_agi3_closed_loop_smoke", path)
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


def test_repeat_capped_cycle_repeats_changed_action_then_rotates_at_cap():
    module = _load_module()
    state = module.RepeatCappedCycleState()

    chosen, rationale = module.choose_repeat_capped_cycle_action([2, 1, 3], state, max_repeat=2)
    assert chosen == 1
    assert rationale["reason"] == "initial_cycle"

    state = module.update_repeat_capped_cycle_state(
        state,
        chosen_action_value=chosen,
        available_action_values=[1, 2, 3],
        frame_changed=True,
        max_repeat=2,
    )
    chosen, rationale = module.choose_repeat_capped_cycle_action([1, 2, 3], state, max_repeat=2)
    assert chosen == 1
    assert rationale["reason"] == "repeat_after_changed_frame"

    state = module.update_repeat_capped_cycle_state(
        state,
        chosen_action_value=chosen,
        available_action_values=[1, 2, 3],
        frame_changed=True,
        max_repeat=2,
    )
    chosen, rationale = module.choose_repeat_capped_cycle_action([1, 2, 3], state, max_repeat=2)
    assert chosen == 2
    assert rationale["reason"] == "cycle_after_stasis_or_cap"


def test_repeat_capped_cycle_rotates_after_no_change():
    module = _load_module()
    state = module.RepeatCappedCycleState()
    state = module.update_repeat_capped_cycle_state(
        state,
        chosen_action_value=1,
        available_action_values=[1, 2],
        frame_changed=False,
        max_repeat=2,
    )

    chosen, rationale = module.choose_repeat_capped_cycle_action([1, 2], state, max_repeat=2)

    assert chosen == 2
    assert rationale["reason"] == "cycle_after_stasis_or_cap"


def test_actuator_only_runner_requires_explicit_one_step_ack():
    module = _load_module()

    with pytest.raises(RuntimeError, match="does not invoke the Nemo3/world-model flow"):
        module.validate_actuator_only_scope(SimpleNamespace(max_steps=1, allow_actuator_only=False))

    with pytest.raises(RuntimeError, match="multi-step ARC runs must enter through the standard model flow"):
        module.validate_actuator_only_scope(SimpleNamespace(max_steps=40, allow_actuator_only=True))

    module.validate_actuator_only_scope(SimpleNamespace(max_steps=1, allow_actuator_only=True))


def test_summarize_closed_loop_counts_progress_and_keeps_non_submission_flags():
    module = _load_module()
    condition = {
        "selected_game": {"game_id": "ls20-9607627b", "name": "ls20"},
        "loader_settings": {
            "policy": "repeat_capped_cycle",
            "max_steps": 40,
            "max_repeat": 2,
        },
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }
    trace_rows = [
        {
            "state": "NOT_FINISHED",
            "next_state": "NOT_FINISHED",
            "levels_completed": 0,
            "next_levels_completed": 1,
            "win_levels": 7,
            "next_win_levels": 7,
            "frame_shape": [64, 64],
            "next_frame_shape": [64, 64],
            "frame_min": 0,
            "frame_max": 12,
            "next_frame_min": 0,
            "next_frame_max": 12,
            "frame_sha256": "a",
            "next_frame_sha256": "b",
            "frame_changed": True,
            "available_action_values": [1, 2],
            "chosen_action_name": "ACTION1",
            "chosen_action_value": 1,
        }
    ]

    metrics = module.summarize_closed_loop(
        condition=condition,
        games=[condition["selected_game"]],
        trace_rows=trace_rows,
        candidate_packets=[{"action_value": 1}],
        executed_steps=1,
        final_obs=FakeObs(levels_completed=1, win_levels=7),
    )

    assert metrics["valid_closed_loop_smoke"] is True
    assert metrics["levels_completed_delta"] == 1
    assert metrics["changed_frame_steps"] == 1
    assert metrics["online_submission"] is False
    assert metrics["arc_solve_claim"] is False
