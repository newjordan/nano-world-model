import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_grid_imagination import build_grid_imagination_map  # noqa: E402


def test_grid_imagination_raises_nonplayable_cells_and_anchors_nonwall_objects():
    grid = [
        [9, 9, 9, 9],
        [9, 0, 2, 9],
        [9, 0, 0, 9],
        [9, 9, 9, 9],
    ]

    imagined = build_grid_imagination_map(
        grid,
        playable_values=(0,),
        wall_values=(9,),
        ray_directions=((1, 0), (-1, 0)),
        object_assessments={2: "unknown_movable_or_goal_relevant"},
    )

    assert imagined.height_map == (
        (1, 1, 1, 1),
        (1, 0, 1, 1),
        (1, 0, 0, 1),
        (1, 1, 1, 1),
    )
    assert len(imagined.anchors) == 1
    assert imagined.anchors[0].position == (2, 1)
    assert imagined.anchors[0].assessment == "unknown_movable_or_goal_relevant"
    assert len(imagined.rays) == 2
    assert imagined.rays[0].blocked is True
    assert imagined.rays[0].hit_value == 9


def test_grid_imagination_frame_exports_raytrace_probes():
    grid = [
        [0, 0, 0],
        [0, 3, 0],
        [0, 0, 0],
    ]

    imagined = build_grid_imagination_map(grid, ray_directions=((1, 0),))
    frame = imagined.to_imagination_frame(state_id="state-ray", confidence=0.75)

    assert frame.representation_basis == "grid2d"
    assert frame.artifact_ref == "grid_imagination://state-ray"
    assert len(frame.raytrace_probes) == 1
    assert frame.raytrace_probes[0].probe_id == "obj_1_1_3:ray:1,0"
    assert frame.raytrace_probes[0].expected_contact is None
    assert frame.raytrace_probes[0].confidence == 0.75


def test_grid_imagination_rejects_empty_grid_and_zero_direction():
    with pytest.raises(ValueError, match="grid must be non-empty"):
        build_grid_imagination_map([])

    with pytest.raises(ValueError, match="ray direction"):
        build_grid_imagination_map([[1]], ray_directions=((0, 0),))
