"""Labeled map perception, 3D grid geometry, and ray accuracy gates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image

from chronometric_grid_imagination import (
    DEFAULT_RAY_DIRECTIONS,
    GridImaginationMap,
    build_grid_imagination_map,
)


Grid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ColorLabel:
    value: int
    rgb: tuple[int, int, int]
    name: str


@dataclass(frozen=True)
class GeometryCell:
    label: int
    name: str
    kind: str
    x: int
    y: int
    z: float
    width: float
    depth: float
    height: float


@dataclass(frozen=True)
class GridGeometry:
    width: int
    height: int
    cells: tuple[GeometryCell, ...]


def label_image_to_grid(
    image: Image.Image | str | Path,
    labels: Sequence[ColorLabel],
    *,
    cell_size: int = 1,
    tolerance: int = 0,
    unknown_label: int = -1,
) -> Grid:
    """Convert a labeled map image into a grid of integer labels.

    This is deterministic labeling from a supplied palette. It is not learned
    vision. If a screenshot is not already cleanly color-coded, a separate
    detector/segmenter must produce this palette-compatible image first.
    """
    if cell_size <= 0:
        raise ValueError("cell_size must be positive")
    palette = {label.value: label.rgb for label in labels}
    if not palette:
        raise ValueError("labels must be non-empty")

    rgb_image = _load_rgb_image(image)
    width, height = rgb_image.size
    if width % cell_size != 0 or height % cell_size != 0:
        raise ValueError("image dimensions must be divisible by cell_size")
    grid_width = width // cell_size
    grid_height = height // cell_size
    rows: list[tuple[int, ...]] = []
    for gy in range(grid_height):
        row: list[int] = []
        for gx in range(grid_width):
            rgb = _cell_mean_rgb(rgb_image, gx, gy, cell_size)
            row.append(_nearest_label(rgb, palette, tolerance=tolerance, unknown_label=unknown_label))
        rows.append(tuple(row))
    return tuple(rows)


def build_grid_geometry(
    grid: Sequence[Sequence[int]],
    labels: Sequence[ColorLabel],
    *,
    playable_values: Sequence[int] = (0,),
    wall_values: Sequence[int] = (),
    cell_size: float = 1.0,
    blocker_height: float = 1.0,
    object_height: float = 0.5,
) -> GridGeometry:
    """Construct simple 3D cell geometry from a labeled grid."""
    rows = _coerce_grid(grid)
    names = {label.value: label.name for label in labels}
    playable = {int(value) for value in playable_values}
    walls = {int(value) for value in wall_values}
    cells: list[GeometryCell] = []
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            label = int(value)
            if label in playable:
                kind = "playable"
                height = 0.0
            elif label in walls:
                kind = "wall"
                height = blocker_height
            else:
                kind = "object"
                height = object_height
            cells.append(
                GeometryCell(
                    label=label,
                    name=names.get(label, f"label_{label}"),
                    kind=kind,
                    x=x,
                    y=y,
                    z=0.0,
                    width=cell_size,
                    depth=cell_size,
                    height=height,
                )
            )
    return GridGeometry(width=len(rows[0]), height=len(rows), cells=tuple(cells))


def evaluate_grid_perception(
    predicted_grid: Sequence[Sequence[int]],
    truth_grid: Sequence[Sequence[int]],
    *,
    playable_values: Sequence[int] = (0,),
    wall_values: Sequence[int] = (),
    ray_directions: Sequence[tuple[int, int]] = DEFAULT_RAY_DIRECTIONS,
    min_cell_accuracy: float = 1.0,
    min_height_accuracy: float = 1.0,
    min_ray_exact_accuracy: float | None = 1.0,
) -> dict[str, Any]:
    """Measure whether map labels and derived rays are accurate enough to trust."""
    predicted = _coerce_grid(predicted_grid)
    truth = _coerce_grid(truth_grid)
    if len(predicted) != len(truth) or len(predicted[0]) != len(truth[0]):
        raise ValueError("predicted_grid and truth_grid must have matching shape")

    cell_total = len(truth) * len(truth[0])
    cell_correct = sum(
        int(predicted[y][x] == truth[y][x]) for y in range(len(truth)) for x in range(len(truth[0]))
    )
    labels = sorted({value for row in truth for value in row} | {value for row in predicted for value in row})
    per_label = {
        label: _label_metrics(predicted, truth, label)
        for label in labels
    }

    predicted_imagination = build_grid_imagination_map(
        predicted,
        playable_values=playable_values,
        wall_values=wall_values,
        ray_directions=ray_directions,
    )
    truth_imagination = build_grid_imagination_map(
        truth,
        playable_values=playable_values,
        wall_values=wall_values,
        ray_directions=ray_directions,
    )
    ray_metrics = evaluate_ray_accuracy(predicted_imagination, truth_imagination)
    height_total = cell_total
    height_correct = sum(
        int(predicted_imagination.height_map[y][x] == truth_imagination.height_map[y][x])
        for y in range(len(truth))
        for x in range(len(truth[0]))
    )

    cell_accuracy = cell_correct / cell_total if cell_total else None
    height_accuracy = height_correct / height_total if height_total else None
    gate_failures = _gate_failures(
        cell_accuracy=cell_accuracy,
        height_accuracy=height_accuracy,
        ray_exact_accuracy=ray_metrics["ray_exact_accuracy"],
        min_cell_accuracy=min_cell_accuracy,
        min_height_accuracy=min_height_accuracy,
        min_ray_exact_accuracy=min_ray_exact_accuracy,
    )

    return {
        "cell_total": cell_total,
        "cell_correct": cell_correct,
        "cell_accuracy": cell_accuracy,
        "height_accuracy": height_accuracy,
        "per_label": per_label,
        "predicted_anchor_count": len(predicted_imagination.anchors),
        "truth_anchor_count": len(truth_imagination.anchors),
        "ray": ray_metrics,
        "trusted": not gate_failures,
        "gate_failures": tuple(gate_failures),
        "gate_thresholds": {
            "min_cell_accuracy": min_cell_accuracy,
            "min_height_accuracy": min_height_accuracy,
            "min_ray_exact_accuracy": min_ray_exact_accuracy,
        },
    }


def evaluate_ray_accuracy(
    predicted: GridImaginationMap,
    truth: GridImaginationMap,
) -> dict[str, Any]:
    """Compare ray hits by origin and direction between two imagination maps."""
    predicted_by_key = {_ray_key(ray): ray for ray in predicted.rays}
    truth_by_key = {_ray_key(ray): ray for ray in truth.rays}
    keys = sorted(set(predicted_by_key) | set(truth_by_key))
    if not keys:
        return {
            "ray_total": 0,
            "ray_exact_accuracy": None,
            "ray_blocked_accuracy": None,
            "ray_hit_position_accuracy": None,
            "ray_hit_value_accuracy": None,
            "missing_predicted_rays": 0,
            "extra_predicted_rays": 0,
        }
    exact = 0
    blocked = 0
    hit_position = 0
    hit_value = 0
    missing = 0
    extra = 0
    for key in keys:
        pred = predicted_by_key.get(key)
        actual = truth_by_key.get(key)
        if pred is None:
            missing += 1
            continue
        if actual is None:
            extra += 1
            continue
        blocked_match = pred.blocked == actual.blocked
        position_match = pred.hit_position == actual.hit_position
        value_match = pred.hit_value == actual.hit_value
        blocked += int(blocked_match)
        hit_position += int(position_match)
        hit_value += int(value_match)
        exact += int(blocked_match and position_match and value_match)
    total = len(keys)
    comparable = total - missing - extra
    return {
        "ray_total": total,
        "ray_comparable": comparable,
        "ray_exact_accuracy": exact / comparable if comparable else None,
        "ray_blocked_accuracy": blocked / comparable if comparable else None,
        "ray_hit_position_accuracy": hit_position / comparable if comparable else None,
        "ray_hit_value_accuracy": hit_value / comparable if comparable else None,
        "missing_predicted_rays": missing,
        "extra_predicted_rays": extra,
    }


def _load_rgb_image(image: Image.Image | str | Path) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB").copy()
    with Image.open(image) as opened:
        return opened.convert("RGB").copy()


def _cell_mean_rgb(image: Image.Image, gx: int, gy: int, cell_size: int) -> tuple[int, int, int]:
    pixels = []
    for y in range(gy * cell_size, (gy + 1) * cell_size):
        for x in range(gx * cell_size, (gx + 1) * cell_size):
            pixels.append(image.getpixel((x, y)))
    return tuple(int(round(sum(pixel[channel] for pixel in pixels) / len(pixels))) for channel in range(3))


def _nearest_label(
    rgb: tuple[int, int, int],
    palette: Mapping[int, tuple[int, int, int]],
    *,
    tolerance: int,
    unknown_label: int,
) -> int:
    best_label = unknown_label
    best_distance = float("inf")
    for label, target in palette.items():
        distance = sum((rgb[channel] - target[channel]) ** 2 for channel in range(3))
        if distance < best_distance:
            best_distance = distance
            best_label = int(label)
    if tolerance >= 0 and best_distance > tolerance * tolerance * 3:
        return unknown_label
    return best_label


def _coerce_grid(grid: Sequence[Sequence[int]]) -> Grid:
    rows = [tuple(int(value) for value in row) for row in grid]
    if not rows or not rows[0]:
        raise ValueError("grid must be non-empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("grid rows must have equal width")
    return tuple(rows)


def _label_metrics(predicted: Grid, truth: Grid, label: int) -> dict[str, float | int | None]:
    tp = fp = fn = 0
    for y in range(len(truth)):
        for x in range(len(truth[0])):
            pred_match = predicted[y][x] == label
            truth_match = truth[y][x] == label
            tp += int(pred_match and truth_match)
            fp += int(pred_match and not truth_match)
            fn += int(not pred_match and truth_match)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def _ray_key(ray: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    return (tuple(ray.origin), tuple(ray.direction))


def _gate_failures(
    *,
    cell_accuracy: float | None,
    height_accuracy: float | None,
    ray_exact_accuracy: float | None,
    min_cell_accuracy: float,
    min_height_accuracy: float,
    min_ray_exact_accuracy: float | None,
) -> list[str]:
    failures: list[str] = []
    if cell_accuracy is None or cell_accuracy < min_cell_accuracy:
        failures.append("cell_accuracy")
    if height_accuracy is None or height_accuracy < min_height_accuracy:
        failures.append("height_accuracy")
    if min_ray_exact_accuracy is not None:
        if ray_exact_accuracy is None or ray_exact_accuracy < min_ray_exact_accuracy:
            failures.append("ray_exact_accuracy")
    return failures
