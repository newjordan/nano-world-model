import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_bridge import synthetic_bridge_records  # noqa: E402
from chronometric_bucket_eval import (  # noqa: E402
    bucket_labels,
    join_predictions_to_manifest,
    movement_axis_bucket,
    summarize_rows,
)


def test_join_predictions_to_manifest_uses_source_step_action_key():
    manifest = synthetic_bridge_records()
    manifest[0]["source_artifact_path"] = "group_a.jsonl"
    manifest[0]["action_id"] = "ACTION4"
    manifest[0]["t"] = 26
    prediction = {
        "source_artifact_path": "group_a.jsonl",
        "action_id": "ACTION4",
        "t": 26,
        "split": "heldout",
        "target_progress": 1.0,
        "pred_progress_prob": 0.99,
        "target_signed_y": 1.0,
        "pred_signed_y": 0.9,
        "pred_progress_rank": 1,
    }

    joined = join_predictions_to_manifest(manifest, [prediction])

    assert len(joined) == 1
    assert joined[0]["split"] == "heldout"
    assert joined[0]["source_commit"] == manifest[0]["source_commit"]


def test_bucket_labels_cover_movement_time_and_control():
    record = copy.deepcopy(synthetic_bridge_records()[0])
    record.update(
        {
            "split": "heldout",
            "control_label": "dominant_group:goal_progress",
            "progress_label": "progress_level_delta_positive",
            "action_id": "ACTION4",
            "dominant_group": "goal_progress",
            "dominant_movement_vector": [0.0, -5.0],
            "changed_cells": 100,
            "target_signed_y": 1.0,
            "t": 26,
        }
    )

    labels = bucket_labels(record)

    assert labels["control_label"] == "control_label:dominant_group:goal_progress"
    assert labels["time_window"] == "time:progress_step"
    assert labels["signed_outcome"] == "signed:progress_positive_y"
    assert movement_axis_bucket(record) == "movement:y_negative"


def test_summarize_rows_reports_false_positive_and_positive_rank():
    rows = [
        {
            "target_progress": 1.0,
            "pred_progress_prob": 0.9,
            "target_signed_y": 1.0,
            "pred_signed_y": 0.8,
            "pred_progress_rank": 1,
        },
        {
            "target_progress": 0.0,
            "pred_progress_prob": 0.2,
            "target_signed_y": 0.0,
            "pred_signed_y": 0.1,
            "pred_progress_rank": 2,
        },
    ]

    summary = summarize_rows(rows)

    assert summary["records"] == 2
    assert summary["positive_records"] == 1
    assert summary["progress_accuracy"] == 1.0
    assert summary["positive_best_rank"] == 1
    assert summary["top_false_positive"]["pred_progress_prob"] == 0.2
