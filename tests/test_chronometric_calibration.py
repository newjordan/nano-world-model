import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_calibration import calibration_example, calibration_features  # noqa: E402
from chronometric_bridge import synthetic_bridge_records  # noqa: E402


def test_calibration_features_exclude_direct_outcome_labels():
    record = synthetic_bridge_records()[0]
    record.update(
        {
            "phase_theta": 1.5,
            "dominant_movement_vector": [2.0, -3.0],
            "potential_family_names": [
                "transition.changed_cells",
                "time_phase.repeated_effect_size",
                "goal_progress.level_delta",
            ],
            "potential_family_vector": [0.25, 0.5, 10.0],
            "action_context": [0.4, 1.0, 0.2, 0.3, 0.125, 1.0, 1.0, 1.0],
        }
    )
    mutated = copy.deepcopy(record)
    mutated["signed_outcome_y"] = -1.0
    mutated["progress_label"] = "no_level_progress"
    mutated["event_mu"][2] = -1.0
    mutated["branch_direction_n"][2] = -1.0
    mutated["potential_family_vector"][2] = -10.0
    mutated["action_context"][5] = -1.0
    mutated["action_context"][6] = -1.0
    mutated["action_context"][7] = -1.0

    assert calibration_features(record) == calibration_features(mutated)


def test_calibration_example_keeps_targets_separate_from_features():
    record = synthetic_bridge_records()[0]
    record["progress_label"] = "progress_level_delta_positive"
    example = calibration_example(record)

    assert example.progress == 1.0
    assert example.signed_y == record["signed_outcome_y"]
    assert len(example.features) == 12
