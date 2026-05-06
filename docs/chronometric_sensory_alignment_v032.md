# Chronometric Sensory Alignment V032

Status: deterministic visual + temporal confirmation record interface.

V031 made map perception trustable before raycasts influence planning. V032
separates that trust into two senses:

- visual sense: current observation, 2D map, 3D geometry projection, and ray
  contact accuracy.
- temporal sense: predicted next-state change versus observed next-state
  change after an action.

The output is one confirmation record per state/action. Each record can carry
an outcome label for later correlation, but the outcome label is not part of
the sensory trust gate.

## Confirmation Tuple

Each datapoint should be shaped as:

```text
observation -> 2D map -> 3D geometry -> rays/probes -> predicted transition
-> actual transition -> outcome label
```

The trust decision is made before the outcome label is considered:

- did the 2D visual map match truth?
- did the 3D internal world project back to the 2D map?
- did ray contacts match the trusted map?
- did the predicted next-state match the observed next-state?

Only then should the record be used as reliable evidence for later signed-Y
correlation.

## Implemented Surfaces

Code:

- `src/chronometric_sensory_alignment.py`
- `scripts/build_chronometric_sensory_record.py`

Tests:

- `tests/test_chronometric_sensory_alignment.py`

Primary functions:

- `project_geometry_to_grid`: flatten 3D cell geometry back to a 2D label map.
- `evaluate_2d_3d_alignment`: check visual 2D/3D projection trust.
- `evaluate_temporal_alignment`: compare predicted next map to actual next map.
- `build_sensory_confirmation_record`: combine visual sense, temporal sense,
  and optional outcome label into one state/action record.

## Harness

```bash
python scripts/build_chronometric_sensory_record.py \
  --run-label chronometric_sensory_alignment_v032_example \
  --state-id state_0001 \
  --action ACTION_RIGHT \
  --predicted-grid predicted_grid.json \
  --truth-grid truth_grid.json \
  --predicted-after-grid predicted_after_grid.json \
  --actual-after-grid actual_after_grid.json \
  --labels labels.json \
  --out-dir experiments/2026-05-05_chronometric_sensory_alignment_v032_example \
  --wall-values 9 \
  --signed-outcome-y 0.5
```

The harness writes `condition.json`, `sensory_record.json`, and `RESULTS.md`.
It exits with code `0` when the combined visual+temporal gate is trusted and
code `2` when the gate fails.

## Boundary

Run label: `new_experiment`.

No training data is promoted. No ARC solve claim is made. V032 is an evidence
record contract for future correlation and planner integration. It does not
train Nemo, alter NanoWM weights, or solve raw screenshot segmentation.
