"""Visual and temporal sensory confirmation records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from chronometric_map_perception import (
    ColorLabel,
    GridGeometry,
    build_grid_geometry,
    evaluate_grid_perception,
)


Grid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class CellChange:
    x: int
    y: int
    before: int
    after: int


@dataclass(frozen=True)
class OutcomeLabel:
    signed_y: float | None = None
    polarity: str = "unknown"


@dataclass(frozen=True)
class ImaginedOutcome:
    signed_y: float | None = None
    polarity: str = "unknown"
    confidence: float = 0.0
    source: str = "pre_action_simulation"


def project_geometry_to_grid(geometry: GridGeometry) -> Grid:
    """Flatten 3D geometry labels back into a 2D label grid."""
    rows = [[0 for _ in range(geometry.width)] for _ in range(geometry.height)]
    seen: set[tuple[int, int]] = set()
    for cell in geometry.cells:
        position = (cell.x, cell.y)
        if position in seen:
            raise ValueError(f"duplicate geometry cell at {position}")
        if cell.x < 0 or cell.y < 0 or cell.x >= geometry.width or cell.y >= geometry.height:
            raise ValueError(f"geometry cell out of bounds at {position}")
        rows[cell.y][cell.x] = int(cell.label)
        seen.add(position)
    expected = geometry.width * geometry.height
    if len(seen) != expected:
        raise ValueError("geometry does not cover every grid cell")
    return tuple(tuple(row) for row in rows)


def evaluate_2d_3d_alignment(
    grid: Sequence[Sequence[int]],
    geometry: GridGeometry,
    *,
    playable_values: Sequence[int] = (0,),
    min_label_projection_accuracy: float = 1.0,
    min_height_projection_accuracy: float = 1.0,
) -> dict[str, Any]:
    """Check whether the internal 3D world projects back to the 2D map."""
    rows = _coerce_grid(grid)
    projected = project_geometry_to_grid(geometry)
    if len(rows) != len(projected) or len(rows[0]) != len(projected[0]):
        raise ValueError("grid and geometry projection must have matching shape")

    playable = {int(value) for value in playable_values}
    total = len(rows) * len(rows[0])
    label_correct = 0
    height_correct = 0
    height_by_position = {(cell.x, cell.y): cell.height for cell in geometry.cells}
    for y, row in enumerate(rows):
        for x, expected_label in enumerate(row):
            label_correct += int(projected[y][x] == expected_label)
            expected_raised = 0 if expected_label in playable else 1
            actual_raised = 0 if height_by_position[(x, y)] == 0 else 1
            height_correct += int(expected_raised == actual_raised)

    label_accuracy = label_correct / total if total else None
    height_accuracy = height_correct / total if total else None
    gate_failures: list[str] = []
    if label_accuracy is None or label_accuracy < min_label_projection_accuracy:
        gate_failures.append("label_projection_accuracy")
    if height_accuracy is None or height_accuracy < min_height_projection_accuracy:
        gate_failures.append("height_projection_accuracy")

    return {
        "cell_total": total,
        "label_projection_accuracy": label_accuracy,
        "height_projection_accuracy": height_accuracy,
        "trusted": not gate_failures,
        "gate_failures": tuple(gate_failures),
        "gate_thresholds": {
            "min_label_projection_accuracy": min_label_projection_accuracy,
            "min_height_projection_accuracy": min_height_projection_accuracy,
        },
    }


def evaluate_temporal_alignment(
    before_grid: Sequence[Sequence[int]],
    predicted_after_grid: Sequence[Sequence[int]],
    actual_after_grid: Sequence[Sequence[int]],
    *,
    min_transition_cell_accuracy: float = 1.0,
    min_change_recall: float = 1.0,
) -> dict[str, Any]:
    """Check whether imagined next-state changes match observed temporal change."""
    before = _coerce_grid(before_grid)
    predicted_after = _coerce_grid(predicted_after_grid)
    actual_after = _coerce_grid(actual_after_grid)
    _require_same_shape(before, predicted_after, "before_grid", "predicted_after_grid")
    _require_same_shape(before, actual_after, "before_grid", "actual_after_grid")

    total = len(before) * len(before[0])
    transition_correct = 0
    actual_changes: list[CellChange] = []
    predicted_changes: list[CellChange] = []
    actual_change_positions: set[tuple[int, int]] = set()
    predicted_change_positions: set[tuple[int, int]] = set()

    for y, before_row in enumerate(before):
        for x, before_value in enumerate(before_row):
            predicted_value = predicted_after[y][x]
            actual_value = actual_after[y][x]
            transition_correct += int(predicted_value == actual_value)
            if before_value != actual_value:
                actual_changes.append(CellChange(x=x, y=y, before=before_value, after=actual_value))
                actual_change_positions.add((x, y))
            if before_value != predicted_value:
                predicted_changes.append(CellChange(x=x, y=y, before=before_value, after=predicted_value))
                predicted_change_positions.add((x, y))

    transition_accuracy = transition_correct / total if total else None
    change_recall = _change_recall(actual_change_positions, predicted_change_positions)
    gate_failures: list[str] = []
    if transition_accuracy is None or transition_accuracy < min_transition_cell_accuracy:
        gate_failures.append("transition_cell_accuracy")
    if change_recall < min_change_recall:
        gate_failures.append("change_recall")

    return {
        "cell_total": total,
        "transition_cell_accuracy": transition_accuracy,
        "actual_change_count": len(actual_changes),
        "predicted_change_count": len(predicted_changes),
        "change_recall": change_recall,
        "change_precision": _change_precision(actual_change_positions, predicted_change_positions),
        "actual_changes": tuple(asdict(change) for change in actual_changes),
        "predicted_changes": tuple(asdict(change) for change in predicted_changes),
        "actual_label_flow": _label_flow(before, actual_after),
        "predicted_label_flow": _label_flow(before, predicted_after),
        "trusted": not gate_failures,
        "gate_failures": tuple(gate_failures),
        "gate_thresholds": {
            "min_transition_cell_accuracy": min_transition_cell_accuracy,
            "min_change_recall": min_change_recall,
        },
    }


def evaluate_outcome_imagination(
    *,
    imagined_signed_y: float | None,
    imagined_confidence: float,
    observed_signed_y: float | None = None,
    min_imagined_confidence: float = 0.0,
    max_signed_abs_error: float | None = None,
) -> dict[str, Any]:
    """Compare pre-action imagined outcome against post-action observed outcome.

    The imagined outcome is part of the branch simulation and is available
    before action. The observed outcome is an optional post-action label for
    calibration and must not be treated as pre-action evidence.
    """
    _validate_confidence(imagined_confidence, "imagined_confidence")
    imagined = ImaginedOutcome(
        signed_y=imagined_signed_y,
        polarity=_outcome_polarity(imagined_signed_y),
        confidence=imagined_confidence,
    )
    observed = OutcomeLabel(
        signed_y=observed_signed_y,
        polarity=_outcome_polarity(observed_signed_y),
    )
    gate_failures: list[str] = []
    if imagined.signed_y is None:
        gate_failures.append("imagined_outcome_missing")
    if imagined.confidence < min_imagined_confidence:
        gate_failures.append("imagined_outcome_confidence")

    signed_abs_error = None
    polarity_match = None
    if imagined.signed_y is not None and observed.signed_y is not None:
        signed_abs_error = abs(imagined.signed_y - observed.signed_y)
        polarity_match = imagined.polarity == observed.polarity
        if not polarity_match:
            gate_failures.append("outcome_polarity_match")
        if max_signed_abs_error is not None and signed_abs_error > max_signed_abs_error:
            gate_failures.append("outcome_signed_abs_error")

    return {
        "imagined": asdict(imagined),
        "observed": asdict(observed),
        "comparison": {
            "observed_available": observed.signed_y is not None,
            "signed_abs_error": signed_abs_error,
            "polarity_match": polarity_match,
        },
        "trusted": not gate_failures,
        "gate_failures": tuple(gate_failures),
        "gate_thresholds": {
            "min_imagined_confidence": min_imagined_confidence,
            "max_signed_abs_error": max_signed_abs_error,
        },
    }


def build_sensory_confirmation_record(
    *,
    state_id: str,
    action: str,
    predicted_grid: Sequence[Sequence[int]],
    truth_grid: Sequence[Sequence[int]],
    predicted_after_grid: Sequence[Sequence[int]],
    actual_after_grid: Sequence[Sequence[int]],
    labels: Sequence[ColorLabel],
    playable_values: Sequence[int] = (0,),
    wall_values: Sequence[int] = (),
    imagined_outcome_y: float | None = None,
    imagined_outcome_confidence: float = 0.0,
    signed_outcome_y: float | None = None,
) -> dict[str, Any]:
    """Build one state/action confirmation record from visual and temporal senses.

    Imagined outcome is pre-action simulation and can guide branch choice.
    Observed outcome is post-action truth for calibration and must not be
    leaked into the visual/temporal senses.
    """
    geometry = build_grid_geometry(
        predicted_grid,
        labels,
        playable_values=playable_values,
        wall_values=wall_values,
    )
    visual_map = evaluate_grid_perception(
        predicted_grid,
        truth_grid,
        playable_values=playable_values,
        wall_values=wall_values,
    )
    visual_geometry = evaluate_2d_3d_alignment(
        predicted_grid,
        geometry,
        playable_values=playable_values,
    )
    temporal = evaluate_temporal_alignment(
        truth_grid,
        predicted_after_grid,
        actual_after_grid,
    )
    outcome = evaluate_outcome_imagination(
        imagined_signed_y=imagined_outcome_y,
        imagined_confidence=imagined_outcome_confidence,
        observed_signed_y=signed_outcome_y,
    )
    trusted = bool(
        visual_map["trusted"]
        and visual_geometry["trusted"]
        and temporal["trusted"]
        and outcome["trusted"]
    )

    return {
        "state_id": state_id,
        "action": action,
        "pre_action_simulation": {
            "imagined_outcome": outcome["imagined"],
        },
        "senses": {
            "visual": {
                "map": visual_map,
                "geometry_projection": visual_geometry,
            },
            "temporal": temporal,
        },
        "post_action_observation": {
            "observed_outcome": outcome["observed"],
        },
        "outcome_imagination": outcome,
        "confirmation": {
            "trusted": trusted,
            "sensory_trusted": bool(visual_map["trusted"] and visual_geometry["trusted"] and temporal["trusted"]),
            "outcome_imagination_trusted": outcome["trusted"],
            "failed_senses": _failed_senses(visual_map, visual_geometry, temporal),
            "failed_outcome": tuple(outcome["gate_failures"]),
        },
    }


def _coerce_grid(grid: Sequence[Sequence[int]]) -> Grid:
    rows = [tuple(int(value) for value in row) for row in grid]
    if not rows or not rows[0]:
        raise ValueError("grid must be non-empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("grid rows must have equal width")
    return tuple(rows)


def _require_same_shape(left: Grid, right: Grid, left_name: str, right_name: str) -> None:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError(f"{left_name} and {right_name} must have matching shape")


def _change_recall(
    actual_positions: set[tuple[int, int]],
    predicted_positions: set[tuple[int, int]],
) -> float:
    if not actual_positions:
        return 1.0
    return len(actual_positions & predicted_positions) / len(actual_positions)


def _change_precision(
    actual_positions: set[tuple[int, int]],
    predicted_positions: set[tuple[int, int]],
) -> float:
    if not predicted_positions:
        return 1.0 if not actual_positions else 0.0
    return len(actual_positions & predicted_positions) / len(predicted_positions)


def _label_flow(before: Grid, after: Grid) -> dict[str, int]:
    flow: dict[str, int] = {}
    for y, before_row in enumerate(before):
        for x, before_value in enumerate(before_row):
            after_value = after[y][x]
            if before_value == after_value:
                continue
            key = f"{before_value}->{after_value}"
            flow[key] = flow.get(key, 0) + 1
    return flow


def _outcome_polarity(signed_outcome_y: float | None) -> str:
    if signed_outcome_y is None:
        return "unknown"
    if signed_outcome_y > 0:
        return "positive"
    if signed_outcome_y < 0:
        return "negative"
    return "neutral"


def _validate_confidence(value: float, name: str) -> None:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def _failed_senses(
    visual_map: dict[str, Any],
    visual_geometry: dict[str, Any],
    temporal: dict[str, Any],
) -> tuple[str, ...]:
    failed = []
    if not visual_map["trusted"]:
        failed.append("visual.map")
    if not visual_geometry["trusted"]:
        failed.append("visual.geometry_projection")
    if not temporal["trusted"]:
        failed.append("temporal.transition")
    return tuple(failed)
