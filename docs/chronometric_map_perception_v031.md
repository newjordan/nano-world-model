# Chronometric Map Perception Gate V031

Status: deterministic interface and accuracy gate for grid games.

V030 added the symbolic grid imagination layer. V031 adds the missing trust
surface before rays are allowed to matter:

1. take a clean labeled map image or screenshot-derived label image.
2. convert the image into an integer grid.
3. construct simple 3D cell geometry from the grid.
4. build the raymap from non-wall object anchors.
5. compare predicted labels, heights, and ray contacts against truth.
6. mark the map `trusted` only when the configured accuracy thresholds pass.

This is not a learned screenshot segmenter yet. The current contract assumes a
palette-labeled image. A raw game screenshot must first be converted by a
detector, segmenter, renderer hook, or human-labeled fixture into that palette.

## Map Contract

The first geometry is intentionally simple:

- playable cells use label `0` and height `0`.
- wall cells are raised blockers and do not emit rays.
- non-wall, non-playable cells are raised objects and emit rays.
- object identity and polarity are not hardcoded.
- ray contacts are a geometry trust signal, not the full gameplay answer.

The point is to prove that the internal drawing matches the environment before
the planner treats ray output as evidence.

## Implemented Surfaces

Code:

- `src/chronometric_map_perception.py`
- `scripts/evaluate_chronometric_map_perception.py`

Tests:

- `tests/test_chronometric_map_perception.py`

Primary functions:

- `label_image_to_grid`: deterministic palette image to integer grid.
- `build_grid_geometry`: integer grid to 3D cell boxes with heights.
- `evaluate_grid_perception`: cell/height/ray accuracy plus trust decision.
- `evaluate_ray_accuracy`: ray contact comparison by origin and direction.

Harness:

```bash
python scripts/evaluate_chronometric_map_perception.py \
  --run-label chronometric_map_perception_v031_example \
  --predicted-image labeled_map.png \
  --truth-grid truth_grid.json \
  --labels labels.json \
  --out-dir experiments/2026-05-05_chronometric_map_perception_v031_example \
  --cell-size 1 \
  --wall-values 9
```

The harness writes `condition.json`, `predicted_grid.json`, `geometry.json`,
`metrics.json`, and `RESULTS.md`. It exits with code `0` when the gate is
trusted and code `2` when the gate fails.

## Accuracy Gate

The default V031 gate is strict:

```text
min_cell_accuracy = 1.0
min_height_accuracy = 1.0
min_ray_exact_accuracy = 1.0
```

The gate returns:

- `trusted`: whether rays may be treated as reliable evidence.
- `gate_failures`: which metrics failed.
- `cell_accuracy`: exact label-grid match rate.
- `height_accuracy`: playable/blocker geometry match rate.
- `ray.ray_exact_accuracy`: exact ray blocked/contact/value match rate.
- `predicted_anchor_count` and `truth_anchor_count`: object-anchor sanity.

If the ray accuracy is unavailable because the predicted map missed every
object anchor, the strict gate fails.

## Research Label

Run label: `new_experiment`.

No training data is promoted. No ARC solve claim is made. This only creates the
perception and geometry trust layer needed before a Nemo/NanoWM planner loop can
use raycasts for action selection.
