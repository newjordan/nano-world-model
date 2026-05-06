import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_map_perception import ColorLabel, build_grid_geometry  # noqa: E402
from chronometric_sensory_alignment import (  # noqa: E402
    build_sensory_confirmation_record,
    evaluate_2d_3d_alignment,
    evaluate_temporal_alignment,
    project_geometry_to_grid,
)


LABELS = (
    ColorLabel(value=0, rgb=(0, 0, 0), name="playable"),
    ColorLabel(value=2, rgb=(0, 255, 0), name="object"),
    ColorLabel(value=9, rgb=(255, 255, 255), name="wall"),
)


def test_geometry_projection_confirms_2d_and_3d_maps_line_up():
    grid = (
        (9, 9, 9),
        (9, 0, 2),
    )
    geometry = build_grid_geometry(grid, LABELS, playable_values=(0,), wall_values=(9,))

    projected = project_geometry_to_grid(geometry)
    metrics = evaluate_2d_3d_alignment(grid, geometry, playable_values=(0,))

    assert projected == grid
    assert metrics["trusted"] is True
    assert metrics["label_projection_accuracy"] == 1.0
    assert metrics["height_projection_accuracy"] == 1.0


def test_geometry_projection_fails_when_height_no_longer_matches_playability():
    grid = (
        (0, 2),
        (0, 0),
    )
    geometry = build_grid_geometry(grid, LABELS, playable_values=(0,), wall_values=())
    broken_cells = tuple(
        replace(cell, height=0.0) if cell.label == 2 else cell
        for cell in geometry.cells
    )
    broken_geometry = geometry.__class__(width=geometry.width, height=geometry.height, cells=broken_cells)

    metrics = evaluate_2d_3d_alignment(grid, broken_geometry, playable_values=(0,))

    assert metrics["trusted"] is False
    assert metrics["label_projection_accuracy"] == 1.0
    assert metrics["height_projection_accuracy"] == 0.75
    assert metrics["gate_failures"] == ("height_projection_accuracy",)


def test_temporal_alignment_confirms_predicted_next_state_matches_actual_change():
    before = (
        (9, 9, 9),
        (9, 2, 0),
        (9, 9, 9),
    )
    after = (
        (9, 9, 9),
        (9, 0, 2),
        (9, 9, 9),
    )

    metrics = evaluate_temporal_alignment(before, predicted_after_grid=after, actual_after_grid=after)

    assert metrics["trusted"] is True
    assert metrics["transition_cell_accuracy"] == 1.0
    assert metrics["actual_change_count"] == 2
    assert metrics["predicted_change_count"] == 2
    assert metrics["change_recall"] == 1.0
    assert metrics["change_precision"] == 1.0
    assert metrics["actual_label_flow"] == {"2->0": 1, "0->2": 1}


def test_temporal_alignment_blocks_trust_when_change_prediction_misses_motion():
    before = (
        (9, 9, 9),
        (9, 2, 0),
        (9, 9, 9),
    )
    actual_after = (
        (9, 9, 9),
        (9, 0, 2),
        (9, 9, 9),
    )

    metrics = evaluate_temporal_alignment(
        before,
        predicted_after_grid=before,
        actual_after_grid=actual_after,
    )

    assert metrics["trusted"] is False
    assert metrics["transition_cell_accuracy"] == pytest.approx(7 / 9)
    assert metrics["change_recall"] == 0.0
    assert set(metrics["gate_failures"]) == {"transition_cell_accuracy", "change_recall"}


def test_sensory_confirmation_record_combines_visual_temporal_and_outcome_label():
    before = (
        (9, 9, 9),
        (9, 2, 0),
        (9, 9, 9),
    )
    after = (
        (9, 9, 9),
        (9, 0, 2),
        (9, 9, 9),
    )

    record = build_sensory_confirmation_record(
        state_id="state-7",
        action="ACTION_RIGHT",
        predicted_grid=before,
        truth_grid=before,
        predicted_after_grid=after,
        actual_after_grid=after,
        labels=LABELS,
        playable_values=(0,),
        wall_values=(9,),
        signed_outcome_y=0.5,
    )

    assert record["state_id"] == "state-7"
    assert record["action"] == "ACTION_RIGHT"
    assert record["confirmation"]["trusted"] is True
    assert record["confirmation"]["failed_senses"] == ()
    assert record["senses"]["visual"]["map"]["trusted"] is True
    assert record["senses"]["visual"]["geometry_projection"]["trusted"] is True
    assert record["senses"]["temporal"]["trusted"] is True
    assert record["outcome_label"] == {"signed_y": 0.5, "polarity": "positive"}


def test_sensory_record_script_writes_confirmation_artifacts(tmp_path):
    before = (
        (9, 9, 9),
        (9, 2, 0),
        (9, 9, 9),
    )
    after = (
        (9, 9, 9),
        (9, 0, 2),
        (9, 9, 9),
    )
    labels_path = tmp_path / "labels.json"
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    out_dir = tmp_path / "out"
    labels_path.write_text(
        json.dumps([{"value": label.value, "rgb": label.rgb, "name": label.name} for label in LABELS]),
        encoding="utf-8",
    )
    before_path.write_text(json.dumps(before), encoding="utf-8")
    after_path.write_text(json.dumps(after), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_chronometric_sensory_record.py",
            "--run-label",
            "test_v032_senses",
            "--state-id",
            "state-7",
            "--action",
            "ACTION_RIGHT",
            "--predicted-grid",
            str(before_path),
            "--truth-grid",
            str(before_path),
            "--predicted-after-grid",
            str(after_path),
            "--actual-after-grid",
            str(after_path),
            "--labels",
            str(labels_path),
            "--out-dir",
            str(out_dir),
            "--wall-values",
            "9",
            "--signed-outcome-y",
            "0.5",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    record = json.loads((out_dir / "sensory_record.json").read_text(encoding="utf-8"))
    condition = json.loads((out_dir / "condition.json").read_text(encoding="utf-8"))
    assert record["confirmation"]["trusted"] is True
    assert record["outcome_label"]["polarity"] == "positive"
    assert condition["run_type"] == "chronometric_sensory_alignment_v032"
    assert (out_dir / "RESULTS.md").exists()
