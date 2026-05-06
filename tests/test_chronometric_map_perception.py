import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_map_perception import (  # noqa: E402
    ColorLabel,
    build_grid_geometry,
    evaluate_grid_perception,
    label_image_to_grid,
)


LABELS = (
    ColorLabel(value=0, rgb=(0, 0, 0), name="playable"),
    ColorLabel(value=2, rgb=(0, 255, 0), name="object"),
    ColorLabel(value=9, rgb=(255, 255, 255), name="wall"),
)


def _palette_image(grid, *, cell_size=2):
    image = Image.new("RGB", (len(grid[0]) * cell_size, len(grid) * cell_size))
    colors = {label.value: label.rgb for label in LABELS}
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            for py in range(y * cell_size, (y + 1) * cell_size):
                for px in range(x * cell_size, (x + 1) * cell_size):
                    image.putpixel((px, py), colors[value])
    return image


def test_label_image_to_grid_converts_clean_palette_screenshot_to_labels():
    grid = (
        (9, 9, 9, 9),
        (9, 0, 2, 9),
        (9, 0, 0, 9),
        (9, 9, 9, 9),
    )
    image = _palette_image(grid, cell_size=3)

    labeled = label_image_to_grid(image, LABELS, cell_size=3, tolerance=0)

    assert labeled == grid


def test_label_image_to_grid_marks_unknown_colors_when_tolerance_fails():
    image = Image.new("RGB", (1, 1), (128, 128, 128))

    labeled = label_image_to_grid(image, LABELS, cell_size=1, tolerance=0, unknown_label=-7)

    assert labeled == ((-7,),)


def test_build_grid_geometry_raises_walls_and_objects_over_playable_plane():
    grid = (
        (9, 9, 9),
        (9, 0, 2),
    )

    geometry = build_grid_geometry(
        grid,
        LABELS,
        playable_values=(0,),
        wall_values=(9,),
        cell_size=1.5,
        blocker_height=2.0,
        object_height=0.75,
    )

    cells = {(cell.x, cell.y): cell for cell in geometry.cells}
    assert geometry.width == 3
    assert geometry.height == 2
    assert cells[(1, 1)].kind == "playable"
    assert cells[(1, 1)].height == 0.0
    assert cells[(0, 0)].kind == "wall"
    assert cells[(0, 0)].height == 2.0
    assert cells[(2, 1)].kind == "object"
    assert cells[(2, 1)].name == "object"
    assert cells[(2, 1)].height == 0.75
    assert cells[(2, 1)].width == 1.5
    assert cells[(2, 1)].depth == 1.5


def test_evaluate_grid_perception_trusts_only_exact_grid_and_ray_match():
    grid = (
        (9, 9, 9, 9),
        (9, 0, 2, 9),
        (9, 0, 0, 9),
        (9, 9, 9, 9),
    )

    metrics = evaluate_grid_perception(
        predicted_grid=grid,
        truth_grid=grid,
        playable_values=(0,),
        wall_values=(9,),
        ray_directions=((1, 0), (-1, 0), (0, 1)),
    )

    assert metrics["trusted"] is True
    assert metrics["gate_failures"] == ()
    assert metrics["cell_accuracy"] == 1.0
    assert metrics["height_accuracy"] == 1.0
    assert metrics["ray"]["ray_exact_accuracy"] == 1.0
    assert metrics["predicted_anchor_count"] == 1
    assert metrics["truth_anchor_count"] == 1


def test_evaluate_grid_perception_blocks_trust_when_labels_change_rays():
    truth = (
        (9, 9, 9, 9),
        (9, 0, 2, 9),
        (9, 0, 0, 9),
        (9, 9, 9, 9),
    )
    predicted = (
        (9, 9, 9, 9),
        (9, 0, 0, 9),
        (9, 0, 0, 9),
        (9, 9, 9, 9),
    )

    metrics = evaluate_grid_perception(
        predicted_grid=predicted,
        truth_grid=truth,
        playable_values=(0,),
        wall_values=(9,),
        ray_directions=((1, 0), (-1, 0), (0, 1)),
    )

    assert metrics["trusted"] is False
    assert "cell_accuracy" in metrics["gate_failures"]
    assert "height_accuracy" in metrics["gate_failures"]
    assert "ray_exact_accuracy" in metrics["gate_failures"]
    assert metrics["cell_correct"] == 15
    assert metrics["predicted_anchor_count"] == 0
    assert metrics["truth_anchor_count"] == 1
    assert metrics["ray"]["missing_predicted_rays"] == 3


def test_grid_perception_rejects_shape_mismatch():
    with pytest.raises(ValueError, match="matching shape"):
        evaluate_grid_perception(predicted_grid=((0,),), truth_grid=((0, 0),))


def test_map_perception_script_writes_lab_artifacts(tmp_path):
    grid = (
        (9, 9, 9, 9),
        (9, 0, 2, 9),
        (9, 0, 0, 9),
        (9, 9, 9, 9),
    )
    image_path = tmp_path / "labeled_map.png"
    truth_path = tmp_path / "truth_grid.json"
    labels_path = tmp_path / "labels.json"
    out_dir = tmp_path / "out"
    _palette_image(grid, cell_size=2).save(image_path)
    truth_path.write_text(json.dumps(grid), encoding="utf-8")
    labels_path.write_text(
        json.dumps([{"value": label.value, "rgb": label.rgb, "name": label.name} for label in LABELS]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/evaluate_chronometric_map_perception.py",
            "--run-label",
            "test_v031_gate",
            "--predicted-image",
            str(image_path),
            "--truth-grid",
            str(truth_path),
            "--labels",
            str(labels_path),
            "--out-dir",
            str(out_dir),
            "--cell-size",
            "2",
            "--wall-values",
            "9",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    condition = json.loads((out_dir / "condition.json").read_text(encoding="utf-8"))
    assert metrics["trusted"] is True
    assert metrics["ray"]["ray_exact_accuracy"] == 1.0
    assert condition["run_type"] == "chronometric_map_perception_v031"
    assert (out_dir / "predicted_grid.json").exists()
    assert (out_dir / "geometry.json").exists()
    assert (out_dir / "RESULTS.md").exists()
