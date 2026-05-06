import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_branch_library import (  # noqa: E402
    blend_branch_library_signed_y,
    build_action6_time_phase_branch_library,
    build_chronometric_branch_library,
    dominant_time_phase_grid_key,
    dominant_translation_grid_key,
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


def test_dominant_time_phase_scope_builds_non_coordinate_grid_prototypes():
    train = _row("train", 0.0, 0.0, 0.25, -0.9)
    train.update(
        {
            "action_id": "ACTION5",
            "action_context": [0.5, 0.0, 0.0, 0.0, 0.000244140625, 0.0, 0.25, 1.0],
            "changed_cells": 1,
        }
    )
    heldout = copy.deepcopy(train)
    heldout.update({"split": "heldout", "target_signed_y": 0.0, "pred_signed_y": -0.25})

    library = build_chronometric_branch_library([train, heldout], scope="dominant_time_phase")
    adjusted, entry = blend_branch_library_signed_y(heldout, library, blend=1.0)

    assert dominant_time_phase_grid_key(train) == "ACTION5|dominant_group:time_phase|no_coord|changed:1"
    assert library["ACTION5|dominant_group:time_phase|no_coord|changed:1"].records == 1
    assert adjusted == 0.25
    assert entry is not None


def test_time_phase_translation_scope_builds_translation_grid_prototypes():
    train = _row("train", 0.0, 0.0, 0.01171875, -0.9)
    train.update(
        {
            "action_id": "ACTION5",
            "control_label": "dominant_group:translation",
            "action_context": [0.5, 0.0, 0.0, 0.0, 0.01171875, 0.0, 0.0, 1.0],
            "changed_cells": 48,
            "potential_family_names": ["transition.changed_cells"],
            "potential_family_vector": [0.01171875],
        }
    )
    heldout = copy.deepcopy(train)
    heldout.update({"split": "heldout", "target_signed_y": 0.0, "pred_signed_y": -0.25})

    library = build_chronometric_branch_library([train, heldout], scope="time_phase_translation")
    adjusted, entry = blend_branch_library_signed_y(heldout, library, blend=1.0)

    assert dominant_translation_grid_key(train) == "ACTION5|dominant_group:translation|no_coord|changed:48"
    assert library["ACTION5|dominant_group:translation|no_coord|changed:48"].records == 1
    assert adjusted == 0.01171875
    assert entry is not None


def test_translation_potential_fallback_uses_safe_observed_potential():
    heldout = _row("heldout", 0.0, 0.0, 0.0, -0.25)
    heldout.update(
        {
            "action_id": "ACTION5",
            "control_label": "dominant_group:translation",
            "action_context": [0.5, 0.0, 0.0, 0.0, 0.0234375, 0.0, 0.0, 1.0],
            "changed_cells": 96,
            "potential_family_names": ["transition.changed_cells"],
            "potential_family_vector": [0.0234375],
        }
    )

    default_adjusted, default_entry = blend_branch_library_signed_y(heldout, {}, blend=1.0)
    fallback_adjusted, fallback_entry = blend_branch_library_signed_y(
        heldout,
        {},
        blend=1.0,
        fallback_scope="dominant_translation_potential",
    )

    assert default_adjusted == -0.25
    assert default_entry is None
    assert fallback_adjusted == 0.0234375
    assert fallback_entry is not None
    assert fallback_entry.records == 0
    assert fallback_entry.key.startswith("fallback:dominant_translation_potential|")


def test_time_phase_translation_fallback_uses_safe_observed_potentials():
    time_phase = _row("heldout", 0.0, 0.0, 0.0, -0.25)
    time_phase.update(
        {
            "action_id": "ACTION1",
            "control_label": "dominant_group:time_phase",
            "action_context": [0.1, 0.0, 0.0, 0.0, 0.0029296875, 0.0, 0.25, 1.0],
            "changed_cells": 12,
            "potential_family_names": ["transition.changed_cells", "time_phase.repeated_effect_size"],
            "potential_family_vector": [0.0029296875, 0.25],
        }
    )
    translation = _row("heldout", 0.0, 0.0, 0.0, -0.25)
    translation.update(
        {
            "action_id": "ACTION5",
            "control_label": "dominant_group:translation",
            "action_context": [0.5, 0.0, 0.0, 0.0, 0.0234375, 0.0, 0.0, 1.0],
            "changed_cells": 96,
            "potential_family_names": ["transition.changed_cells"],
            "potential_family_vector": [0.0234375],
        }
    )

    time_phase_adjusted, time_phase_entry = blend_branch_library_signed_y(
        time_phase,
        {},
        blend=1.0,
        fallback_scope="time_phase_translation_potential",
    )
    translation_adjusted, translation_entry = blend_branch_library_signed_y(
        translation,
        {},
        blend=1.0,
        fallback_scope="time_phase_translation_potential",
    )

    assert time_phase_adjusted == 0.2529296875
    assert time_phase_entry is not None
    assert time_phase_entry.key.startswith("fallback:dominant_time_phase_potential|")
    assert translation_adjusted == 0.0234375
    assert translation_entry is not None
    assert translation_entry.key.startswith("fallback:dominant_translation_potential|")
