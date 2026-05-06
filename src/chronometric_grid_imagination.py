"""Gridspace imagination maps with object-attached ray probes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from chronometric_ab_overlay import ImaginationFrame, RaytraceProbe


DEFAULT_RAY_DIRECTIONS = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (1, 1),
    (1, -1),
    (-1, 1),
    (-1, -1),
)


@dataclass(frozen=True)
class GridObjectAnchor:
    object_id: str
    value: int
    position: tuple[int, int]
    assessment: str = "unknown"
    confidence: float = 0.0


@dataclass(frozen=True)
class GridRayHit:
    probe_id: str
    origin: tuple[int, int]
    direction: tuple[int, int]
    path: tuple[tuple[int, int], ...]
    hit_position: tuple[int, int] | None
    hit_value: int | None
    blocked: bool


@dataclass(frozen=True)
class GridImaginationMap:
    width: int
    height: int
    height_map: tuple[tuple[int, ...], ...]
    anchors: tuple[GridObjectAnchor, ...]
    rays: tuple[GridRayHit, ...]

    def to_imagination_frame(self, *, state_id: str, confidence: float = 1.0) -> ImaginationFrame:
        probes = tuple(
            RaytraceProbe(
                probe_id=ray.probe_id,
                question=(
                    f"From object at {ray.origin}, what does ray {ray.direction} contact "
                    "before open space continues?"
                ),
                origin=(float(ray.origin[0]), float(ray.origin[1]), 0.0),
                direction=(float(ray.direction[0]), float(ray.direction[1]), 0.0),
                expected_contact=str(ray.hit_value) if ray.hit_value is not None else None,
                confidence=confidence,
            )
            for ray in self.rays
        )
        return ImaginationFrame(
            representation_basis="grid2d",
            description=(
                f"grid raymap for {state_id}: playable cells height 0, raised blockers height 1, "
                f"{len(self.anchors)} object anchors, {len(self.rays)} rays"
            ),
            confidence=confidence,
            artifact_ref=f"grid_imagination://{state_id}",
            raytrace_probes=probes,
        )


def build_grid_imagination_map(
    grid: Sequence[Sequence[int]],
    *,
    playable_values: Iterable[int] = (0,),
    wall_values: Iterable[int] = (),
    ray_directions: Sequence[tuple[int, int]] = DEFAULT_RAY_DIRECTIONS,
    object_assessments: dict[int, str] | None = None,
) -> GridImaginationMap:
    """Build a height-map and object ray probes from a grid world.

    Playable values become height 0. Every other cell becomes a raised blocker.
    Wall values block rays but are not object anchors. Non-wall blockers become
    object anchors and emit rays.
    """
    rows = [list(row) for row in grid]
    if not rows or not rows[0]:
        raise ValueError("grid must be non-empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("grid rows must have equal width")

    playable = {int(value) for value in playable_values}
    walls = {int(value) for value in wall_values}
    assessments = object_assessments or {}
    height = len(rows)
    height_map: list[tuple[int, ...]] = []
    anchors: list[GridObjectAnchor] = []
    rays: list[GridRayHit] = []

    for y, row in enumerate(rows):
        height_row: list[int] = []
        for x, value in enumerate(row):
            cell = int(value)
            raised = 0 if cell in playable else 1
            height_row.append(raised)
            if raised and cell not in walls:
                anchors.append(
                    GridObjectAnchor(
                        object_id=f"obj_{x}_{y}_{cell}",
                        value=cell,
                        position=(x, y),
                        assessment=assessments.get(cell, "unknown"),
                        confidence=0.0 if cell not in assessments else 1.0,
                    )
                )
        height_map.append(tuple(height_row))

    for anchor in anchors:
        for direction in ray_directions:
            if direction == (0, 0):
                raise ValueError("ray direction cannot be (0, 0)")
            rays.append(_cast_ray(rows, playable, anchor, direction))

    return GridImaginationMap(
        width=width,
        height=height,
        height_map=tuple(height_map),
        anchors=tuple(anchors),
        rays=tuple(rays),
    )


def _cast_ray(
    rows: list[list[int]],
    playable: set[int],
    anchor: GridObjectAnchor,
    direction: tuple[int, int],
) -> GridRayHit:
    width = len(rows[0])
    height = len(rows)
    dx, dy = direction
    x, y = anchor.position
    path: list[tuple[int, int]] = []
    step = 0
    while True:
        step += 1
        x += dx
        y += dy
        if x < 0 or y < 0 or x >= width or y >= height:
            return GridRayHit(
                probe_id=f"{anchor.object_id}:ray:{dx},{dy}",
                origin=anchor.position,
                direction=direction,
                path=tuple(path),
                hit_position=None,
                hit_value=None,
                blocked=False,
            )
        path.append((x, y))
        value = int(rows[y][x])
        if value not in playable:
            return GridRayHit(
                probe_id=f"{anchor.object_id}:ray:{dx},{dy}",
                origin=anchor.position,
                direction=direction,
                path=tuple(path),
                hit_position=(x, y),
                hit_value=value,
                blocked=True,
            )
