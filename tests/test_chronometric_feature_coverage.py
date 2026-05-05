import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_feature_coverage import nearest_train_groups, summarize_feature_groups  # noqa: E402
from chronometric_bridge import synthetic_bridge_records  # noqa: E402


def _row(split: str, action: str, control: str, phase_eta: float, pred_signed: float, target_signed: float):
    row = copy.deepcopy(synthetic_bridge_records()[0])
    row.update(
        {
            "split": split,
            "action_id": action,
            "control_label": control,
            "target_signed_y": target_signed,
            "pred_signed_y": pred_signed,
            "target_progress": 0.0,
            "pred_progress_prob": 0.01,
            "potential_family_names": [
                "transition.changed_cells",
                "time_phase.repeated_effect_size",
                "goal_progress.level_delta",
                "stasis.no_change",
            ],
            "potential_family_vector": [0.1, phase_eta, 0.0, 0.0],
        }
    )
    return row


def test_feature_coverage_summarizes_action_control_errors_and_nearest_train():
    rows = [
        _row("train", "ACTION5", "dominant_group:stasis_loop", 0.0, -1.0, -1.0),
        _row("train", "ACTION6", "dominant_group:stasis_loop", 0.25, -1.0, -1.0),
        _row("heldout", "ACTION5", "dominant_group:stasis_loop", 0.25, 0.5, -1.0),
    ]

    summary = summarize_feature_groups(rows)
    nearest = nearest_train_groups(summary)
    heldout_label = "action:ACTION5|control_label:dominant_group:stasis_loop"

    heldout_stats = summary["action_control"]["heldout"][heldout_label]
    assert heldout_stats["signed_mae"] == 1.5
    assert heldout_stats["feature_mean"]["time_phase_eta"] == 0.25
    assert nearest[heldout_label]["same_label_train_records"] == 1
    assert nearest[heldout_label]["same_label_distance"] > 0
