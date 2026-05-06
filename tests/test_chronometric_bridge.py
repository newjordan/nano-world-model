import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_bridge import (  # noqa: E402
    bridge_record_from_arc_transition,
    bridge_records_from_dream_sequence,
    synthetic_bridge_records,
    validate_bridge_manifest,
    validate_bridge_record,
    write_jsonl,
)


def test_synthetic_bridge_records_validate():
    records = synthetic_bridge_records()

    for record in records:
        assert validate_bridge_record(record) == []


def test_bridge_record_rejects_missing_required_field():
    record = synthetic_bridge_records()[0]
    del record["branch_direction_n"]

    errors = validate_bridge_record(record)

    assert any("branch_direction_n" in error for error in errors)


def test_bridge_manifest_validation_roundtrip(tmp_path):
    path = tmp_path / "manifest.jsonl"
    write_jsonl(path, synthetic_bridge_records())

    result = validate_bridge_manifest(path)

    assert result["valid"] is True
    assert result["records"] == 2
    assert result["errors"] == []


def test_arc_transition_converts_to_valid_bridge_record():
    transition = {
        "schema": "arcwm.grid.transition.v001",
        "attempt_id": "attempt_a",
        "task_id": "task_a",
        "step_idx": 26,
        "height": 64,
        "width": 64,
        "action": "ACTION4",
        "action_value": 4,
        "action_data": None,
        "changed_cells": 2982,
        "cell_events": 4096,
        "level_delta": 1,
        "levels_completed": 0,
        "next_levels_completed": 1,
        "next_state": "NOT_FINISHED",
        "eta_total": 10.72802734375,
        "outcome_sign": 1,
        "dominant_family": "goal_progress.level_delta",
        "dominant_group": "goal_progress",
        "family_eta": {
            "goal_progress.level_delta": 10.0,
            "transition.changed_cells": 0.72802734375,
        },
        "movement": {
            "dominant_vector": {
                "dx": 0.1279157548955112,
                "dy": -3.4958530352415487,
            }
        },
        "transition_id": "attempt_a:000026",
        "frame_hash": "before",
        "next_frame_hash": "after",
    }

    record = bridge_record_from_arc_transition(
        transition,
        source_repo="https://example.invalid/arc.git",
        source_commit="abc123",
        source_artifact_path="runs/grid/sprint0/transition_events/attempt_a.transitions.jsonl",
        source_condition_artifact="experiments/example/CONDITION.md",
    )

    assert validate_bridge_record(record) == []
    assert record["progress_label"] == "progress_level_delta_positive"
    assert record["control_label"] == "dominant_group:goal_progress"
    assert record["signed_outcome_y"] == 1.0
    assert record["event_mu"][2] == 1.0
    assert record["branch_direction_n"][2] > 0.99


def test_dream_kernel_sequence_converts_to_valid_bridge_records():
    sequence = {
        "schema": "dream_kernel.sequence.v003",
        "integrity": {"sequence_hash": "dreamhash", "invariant_passed": True},
        "branch_matrix": [
            {
                "branch_id": "tick0.move",
                "action_id": "move_entity_0_dx1_dy0_dz0",
                "start_tick": 0,
                "end_tick": 1,
                "chrono_y_net": 0.75,
                "chrono_y_min": 0.0,
                "positive_mass": 1.0,
                "negative_exposure": 0.0,
                "supporting_objects": ["agent", "goal:2:1:0"],
                "risk_objects": [],
                "frame_hash": "frame1",
            }
        ],
        "frames": [
            {"tick": 0, "render_top_down": ["###", "#A#", "###"]},
            {
                "tick": 1,
                "render_top_down": ["###", "#.A", "###"],
                "chronometric": {
                    "event_mu": [1.0, 0.5, 1.0, 0.5],
                    "branch_direction_n": [0.0, 0.0, 1.0, 0.0],
                    "potential_family_names": [
                        "transition.changed_cells",
                        "goal_progress.level_delta",
                    ],
                    "potential_family_vector": [1.0, 1.0],
                    "signed_outcome_y": 1.0,
                },
                "outcome": {"terminal": True, "reward": 1.0},
            },
        ],
    }

    records = bridge_records_from_dream_sequence(
        sequence,
        source_repo="local://nano-world-model",
        source_commit="abc123",
        source_artifact_path="experiments/dream/dream_sequence.json",
        source_condition_artifact="experiments/dream/condition.json",
    )

    assert len(records) == 1
    assert validate_bridge_record(records[0]) == []
    assert records[0]["branch_id"] == "tick0.move"
    assert records[0]["split"] == "dream_kernel_sequence_v003"
    assert records[0]["quarantine_status"] == "quarantine: dream_kernel_deterministic_no_training"
    assert records[0]["source_artifact_path"] == "experiments/dream/dream_sequence.json"
    assert records[0]["source_condition_artifact"] == "experiments/dream/condition.json"
    assert records[0]["progress_label"] == "dream_kernel_goal_terminal_positive"
