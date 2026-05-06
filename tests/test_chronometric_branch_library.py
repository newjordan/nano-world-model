import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_branch_library import (  # noqa: E402
    blend_branch_library_signed_y,
    build_action6_time_phase_branch_library,
)
from chronometric_bridge import synthetic_bridge_records  # noqa: E402


def _row(split: str, x: float, y: float, target: float, pred: float):
    row = copy.deepcopy(synthetic_bridge_records()[0])
    row.update(
        {
            "split": split,
            "action_id": "ACTION6",
            "control_label": "dominant_group:time_phase",
            "action_context": [0.6, 1.0, x, y, 0.000244140625, 0.0, 0.0, 0.0],
            "potential_family_names": ["time_phase.repeated_effect_size"],
            "potential_family_vector": [0.25],
            "target_signed_y": target,
            "pred_signed_y": pred,
        }
    )
    return row


def test_branch_library_builds_from_train_targets_and_blends_predictions():
    rows = [
        _row("train", 0.4375, 0.46875, 0.25, -0.9),
        _row("train", 0.4375, 0.46875, 0.5, -0.8),
        _row("heldout", 0.4375, 0.46875, 0.0, -1.0),
        _row("heldout", 0.953125, 0.015625, 0.0, -0.5),
    ]

    library = build_action6_time_phase_branch_library(rows)
    adjusted, entry = blend_branch_library_signed_y(rows[2], library, blend=1.0)
    partial, _ = blend_branch_library_signed_y(rows[2], library, blend=0.5)
    unmatched, missing_entry = blend_branch_library_signed_y(rows[3], library, blend=1.0)

    assert library["ACTION6|dominant_group:time_phase|x:28|y:30"].records == 2
    assert library["ACTION6|dominant_group:time_phase|x:28|y:30"].signed_y_mean == 0.375
    assert adjusted == 0.375
    assert entry is not None
    assert partial == -0.3125
    assert unmatched == -0.5
    assert missing_entry is None
