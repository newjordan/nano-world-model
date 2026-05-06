import copy
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import torch

from chronometric_calibration import (  # noqa: E402
    FEATURE_NAMES,
    ChronometricCalibrationMLP,
    action6_time_phase_geometry_key,
    branch_consistency_pairs,
    calibration_example,
    calibration_features,
    examples_to_action6_time_phase_mask,
    examples_to_negative_control_mask,
    is_action6_coordinate_time_phase_record,
    records_with_temporal_context,
    split_examples_by_group,
)
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
                "stasis.no_change",
                "loop.repeated_action",
                "mirror.progress_path",
                "mirror.progress_blocker",
                "hazard.env_failure",
            ],
            "potential_family_vector": [0.25, 0.5, 10.0, 1.0, 0.75, 0.125, 0.0625, 0.25],
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


def test_calibration_features_include_safe_potential_family_inputs():
    record = synthetic_bridge_records()[0]
    record["action_id"] = "ACTION4"
    record["action_context"] = [0.4, 1.0, 0.2, 0.3, 0.125, 1.0, 1.0, 1.0]
    record["potential_family_names"] = [
        "transition.changed_cells",
        "time_phase.repeated_effect_size",
        "goal_progress.level_delta",
        "stasis.no_change",
        "loop.repeated_action",
        "mirror.progress_path",
        "mirror.progress_blocker",
        "hazard.env_failure",
    ]
    record["potential_family_vector"] = [0.25, 0.5, 10.0, 1.0, 0.75, 0.125, 0.0625, 0.25]

    features = dict(zip(FEATURE_NAMES, calibration_features(record), strict=True))

    assert features["transition_changed_eta"] == 0.25
    assert features["time_phase_eta"] == 0.5
    assert features["stasis_no_change_eta"] == 1.0
    assert features["loop_repeated_action_eta"] == 0.75
    assert features["mirror_progress_path_eta"] == 0.125
    assert features["mirror_progress_blocker_eta"] == 0.0625
    assert features["hazard_env_failure_eta"] == 0.25
    assert features["coordinate_time_phase_eta"] == 0.5
    assert features["action6_time_phase_eta"] == 0.0
    assert features["action6_coordinate_time_phase_eta"] == 0.0
    assert features["action6_coordinate_transition_eta"] == 0.0
    assert math.isclose(features["action_data_x_centered"], -0.3)
    assert math.isclose(features["action_data_y_centered"], -0.2)
    assert math.isclose(features["action_data_center_l2"], math.hypot(-0.3, -0.2))
    assert features["action_data_wall_distance"] == 0.2
    assert features["action6_time_phase_wall_distance"] == 0.0
    assert features["action6_time_phase_center_l2"] == 0.0
    assert "goal_progress_level_delta" not in features


def test_calibration_features_include_safe_action6_time_phase_interactions():
    record = synthetic_bridge_records()[0]
    record["action_id"] = "ACTION6"
    record["action_context"] = [0.6, 1.0, 0.2, 0.3, 0.125, 1.0, 1.0, 1.0]
    record["potential_family_names"] = [
        "transition.changed_cells",
        "time_phase.repeated_effect_size",
        "goal_progress.level_delta",
        "stasis.no_change",
    ]
    record["potential_family_vector"] = [0.000244140625, 0.25, 10.0, 0.0]

    features = dict(zip(FEATURE_NAMES, calibration_features(record), strict=True))

    assert features["coordinate_time_phase_eta"] == 0.25
    assert features["action6_time_phase_eta"] == 0.25
    assert features["action6_coordinate_time_phase_eta"] == 0.25
    assert features["action6_coordinate_transition_eta"] == 0.000244140625
    assert math.isclose(features["action_data_x_centered"], -0.3)
    assert math.isclose(features["action_data_y_centered"], -0.2)
    assert features["action_data_wall_distance"] == 0.2
    assert math.isclose(features["action6_time_phase_wall_distance"], 0.25 * 0.2)
    assert math.isclose(features["action6_time_phase_center_l2"], 0.25 * math.hypot(-0.3, -0.2))
    assert "goal_progress_level_delta" not in features


def test_action6_time_phase_mask_uses_safe_bucket_fields():
    match = synthetic_bridge_records()[0]
    match["action_id"] = "ACTION6"
    match["control_label"] = "dominant_group:time_phase"
    match["action_context"] = [0.6, 1.0, 0.2, 0.3, 0.125, 1.0, 1.0, 1.0]
    match["potential_family_names"] = [
        "transition.changed_cells",
        "time_phase.repeated_effect_size",
    ]
    match["potential_family_vector"] = [0.000244140625, 0.25]

    no_time_phase = copy.deepcopy(match)
    no_time_phase["potential_family_vector"] = [0.000244140625, 0.0]

    no_coordinate = copy.deepcopy(match)
    no_coordinate["action_context"] = [0.6, 0.0, 0.2, 0.3, 0.125, 1.0, 1.0, 1.0]

    not_action6 = copy.deepcopy(match)
    not_action6["action_id"] = "ACTION4"
    not_action6["action_context"][0] = 0.4

    not_dominant_time_phase = copy.deepcopy(match)
    not_dominant_time_phase["control_label"] = "dominant_group:translation"

    assert is_action6_coordinate_time_phase_record(match)
    assert not is_action6_coordinate_time_phase_record(no_time_phase)
    assert not is_action6_coordinate_time_phase_record(no_coordinate)
    assert not is_action6_coordinate_time_phase_record(not_action6)
    assert not is_action6_coordinate_time_phase_record(not_dominant_time_phase)

    examples = [
        calibration_example(record)
        for record in (match, no_time_phase, no_coordinate, not_action6, not_dominant_time_phase)
    ]
    mask = examples_to_action6_time_phase_mask(examples, device=torch.device("cpu"))

    assert mask.squeeze(-1).tolist() == [1.0, 0.0, 0.0, 0.0, 0.0]


def test_branch_consistency_pairs_match_geometry_across_families_without_targets():
    train_a = synthetic_bridge_records()[0]
    train_a["source_condition_artifact"] = "family_a"
    train_a["source_artifact_path"] = "family_a/ka59.jsonl"
    train_a["action_id"] = "ACTION6"
    train_a["control_label"] = "dominant_group:time_phase"
    train_a["action_context"] = [0.6, 1.0, 0.4375, 0.46875, 0.125, 1.0, 1.0, 1.0]
    train_a["potential_family_names"] = ["time_phase.repeated_effect_size"]
    train_a["potential_family_vector"] = [0.25]
    train_a["signed_outcome_y"] = -1.0

    train_b = copy.deepcopy(train_a)
    train_b["source_condition_artifact"] = "family_b"
    train_b["source_artifact_path"] = "family_b/ka59.jsonl"
    train_b["signed_outcome_y"] = 1.0

    heldout = copy.deepcopy(train_a)
    heldout["source_condition_artifact"] = "family_c"
    heldout["source_artifact_path"] = "family_c/ka59.jsonl"
    heldout["signed_outcome_y"] = 0.0

    not_matching = copy.deepcopy(train_a)
    not_matching["source_condition_artifact"] = "family_d"
    not_matching["action_context"][2] = 0.953125

    assert action6_time_phase_geometry_key(train_a) == "ACTION6|dominant_group:time_phase|x:28|y:30"
    assert action6_time_phase_geometry_key(not_matching) == "ACTION6|dominant_group:time_phase|x:61|y:30"

    train_examples = [calibration_example(record) for record in (train_a, train_b, not_matching)]
    heldout_examples = [calibration_example(heldout)]

    train_pairs = branch_consistency_pairs(train_examples)
    transductive_pairs = branch_consistency_pairs(train_examples, heldout=heldout_examples, include_heldout=True)

    assert [(pair.left_split, pair.left_index, pair.right_split, pair.right_index) for pair in train_pairs] == [
        ("train", 0, "train", 1),
    ]
    assert [(pair.left_split, pair.left_index, pair.right_split, pair.right_index) for pair in transductive_pairs] == [
        ("train", 0, "train", 1),
        ("train", 0, "heldout", 0),
        ("train", 1, "heldout", 0),
    ]


def test_records_with_temporal_context_adds_prior_only_loop_features():
    records = []
    for index, action in enumerate(["ACTION1", "ACTION5", "ACTION5", "ACTION5", "ACTION2"]):
        record = copy.deepcopy(synthetic_bridge_records()[0])
        record["source_artifact_path"] = "branch.jsonl"
        record["t"] = index
        record["action_id"] = action
        record["action_context"] = [0.5, 0.0, 0.0, 0.0, 0.000244140625, 0.0, 0.0, 0.0]
        record["signed_outcome_y"] = 1.0 if index == 2 else -1.0
        records.append(record)

    annotated = records_with_temporal_context(records, max_streak=4.0)

    assert annotated[0]["same_action_streak_norm"] == 0.0
    assert annotated[1]["same_action_streak_norm"] == 0.0
    assert annotated[2]["same_action_streak_norm"] == 0.25
    assert annotated[3]["same_action_streak_norm"] == 0.5
    assert annotated[3]["same_action_low_change_streak_norm"] == 0.5
    assert annotated[4]["same_action_streak_norm"] == 0.0

    original_features = calibration_features(annotated[2])
    mutated = copy.deepcopy(annotated[2])
    mutated["signed_outcome_y"] = -1.0
    mutated["progress_label"] = "no_level_progress"

    assert calibration_features(mutated) == original_features


def test_temporal_context_does_not_streak_coordinate_actions():
    records = []
    for index in range(3):
        record = copy.deepcopy(synthetic_bridge_records()[0])
        record["source_artifact_path"] = "coordinate_branch.jsonl"
        record["t"] = index
        record["action_id"] = "ACTION6"
        record["action_context"] = [0.6, 1.0, 0.1 * index, 0.2, 0.000244140625, 0.0, 0.0, 0.0]
        records.append(record)

    annotated = records_with_temporal_context(records, max_streak=4.0)

    assert [record["same_action_streak_norm"] for record in annotated] == [0.0, 0.0, 0.0]
    assert [record["same_action_low_change_streak_norm"] for record in annotated] == [0.0, 0.0, 0.0]


def test_calibration_example_keeps_targets_separate_from_features():
    record = synthetic_bridge_records()[0]
    record["progress_label"] = "progress_level_delta_positive"
    example = calibration_example(record)

    assert example.progress == 1.0
    assert example.signed_y == record["signed_outcome_y"]
    assert len(example.features) == len(FEATURE_NAMES)


def test_negative_control_mask_marks_stasis_and_loop_labels():
    records = []
    for control_label in (
        "stasis_no_change",
        "dominant_group:stasis_loop",
        "dominant_group:translation",
    ):
        record = copy.deepcopy(synthetic_bridge_records()[0])
        record["control_label"] = control_label
        records.append(record)

    examples = [calibration_example(record) for record in records]
    mask = examples_to_negative_control_mask(examples, device=torch.device("cpu"))

    assert mask.squeeze(-1).tolist() == [1.0, 1.0, 0.0]


def test_split_examples_by_group_holds_out_whole_groups():
    records = []
    for index in range(4):
        record = copy.deepcopy(synthetic_bridge_records()[index % 2])
        record["source_artifact_path"] = f"group_{index}.jsonl"
        record["progress_label"] = "progress_level_delta_positive" if index < 2 else "no_level_progress"
        records.append(record)

    split = split_examples_by_group(
        [calibration_example(record) for record in records],
        key="source_artifact_path",
        holdout_fraction=0.5,
        seed=7,
    )
    train_groups = {example.record["source_artifact_path"] for example in split.train}
    heldout_groups = {example.record["source_artifact_path"] for example in split.heldout}

    assert train_groups.isdisjoint(heldout_groups)
    assert train_groups
    assert heldout_groups
    assert any(example.progress == 1.0 for example in split.train)
    assert any(example.progress == 1.0 for example in split.heldout)


def test_split_examples_by_group_accepts_explicit_heldout_group():
    records = []
    for group in ("train_family", "heldout_family"):
        record = copy.deepcopy(synthetic_bridge_records()[0])
        record["source_condition_artifact"] = group
        records.append(record)

    split = split_examples_by_group(
        [calibration_example(record) for record in records],
        key="source_condition_artifact",
        holdout_fraction=0.0,
        heldout_group_values=["heldout_family"],
    )

    assert {example.record["source_condition_artifact"] for example in split.train} == {"train_family"}
    assert {example.record["source_condition_artifact"] for example in split.heldout} == {"heldout_family"}


def test_split_examples_by_group_rejects_missing_explicit_heldout_group():
    records = [copy.deepcopy(synthetic_bridge_records()[0])]
    records[0]["source_condition_artifact"] = "present_family"

    try:
        split_examples_by_group(
            [calibration_example(record) for record in records],
            key="source_condition_artifact",
            heldout_group_values=["missing_family"],
        )
    except ValueError as exc:
        assert "missing_family" in str(exc)
    else:
        raise AssertionError("missing explicit heldout group should fail")


def test_calibration_mlp_bounds_signed_and_family_outputs():
    model = ChronometricCalibrationMLP(input_dim=3, family_dim=2, hidden_size=4, bounded_outputs=True)
    outputs = model(torch.full((2, 3), 1000.0))

    assert torch.all(outputs["signed_y"] <= 1.0)
    assert torch.all(outputs["signed_y"] >= -1.0)
    assert torch.all(outputs["family_vector"] <= 1.0)
    assert torch.all(outputs["family_vector"] >= -1.0)
