# Chronometric Testing

Status: first test protocol for the chronometric NanoWM foundation.

The initial test surface is a mechanics smoke, not a model-quality benchmark.
It proves the installed chronometric primitives run under a recorded condition
before quarantined ARC data is allowed into this repo.

## V001 Mechanics Smoke

Runner:

```bash
python scripts/chronometric_mechanics_smoke.py --device auto
```

Default output:

```text
experiments/2026-05-05_chronometric_mechanics_smoke/
  condition.json
  metrics.json
  synthetic_bridge_manifest.jsonl
  RESULTS.md
```

Run label: `mechanics_smoke`

Run kind: `new_experiment`

Data policy: synthetic tokens only. No quarantined ARC Sprint 0 artifact is
read or converted.

## Gates

The runner checks:

- log-time phase advances by one cycle when internal time is scaled by
  `3722/2705`
- projector preserves the timelike invariant and enforces
  `u_mu F_cont^mu = 0`
- chronometric layer preserves invariant/orthogonality constraints over supplied
  branch directions
- same state can score distinct supplied branch directions
- action context changes `F_ext`
- residual mode applies a nonzero token update
- tiny NanoWM audit mode records metrics without changing model output
- a synthetic bridge manifest validates against the required ARC-to-NanoWM
  schema

## Bridge Rule

ARC-derived rows are still blocked until they appear in a manifest with:

```text
source_repo
source_commit
source_artifact_path
source_condition_artifact
quarantine_status
split
task_id
attempt_id
t
observation_shape
action_id
action_context
event_mu
branch_direction_n
potential_family_vector
signed_outcome_y
progress_label
control_label
chronometric_transform_version
```

Schema helpers live in `src/chronometric_bridge.py`. Existing Sprint 0 ARC data
should enter, if at all, with a quarantine status such as:

```text
control_source: arc_scaffold_non_chronometric
```

## V002 ARC Bridge Manifest Smoke

Runner:

```bash
python scripts/build_arc_bridge_manifest.py
```

Default source:

```text
/home/frosty40/world_model_1/
  experiments/2026-05-04_v019b_target_discriminated_scorer_scout/
    grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl
```

Default output:

```text
experiments/2026-05-05_arc_bridge_manifest_smoke/
  arc_bridge_manifest.jsonl
  condition.json
  summary.json
  RESULTS.md
```

This converts grid transition rows into the required bridge schema. It preserves
`control_source: arc_scaffold_non_chronometric` and does not promote the output
to training data.

## V003 Chronometric Calibration Smoke

Runner:

```bash
python scripts/train_chronometric_calibrator.py
```

Default source:

```text
experiments/2026-05-05_arc_bridge_manifest_smoke/arc_bridge_manifest.jsonl
```

Default output:

```text
experiments/2026-05-05_chronometric_calibration_smoke/
  condition.json
  metrics.json
  predictions.jsonl
  RESULTS.md
```

This trains a small calibration MLP over bridge-manifest features. It predicts
`signed_outcome_y`, progress probability, and potential-family activations.
Inputs intentionally exclude direct outcome labels and post-outcome fields:
`signed_outcome_y`, `event_mu.y`, `branch_direction_n.y`, `level_delta`,
`next_levels_completed`, `eta_total`, `outcome_sign`, and
`goal_progress.level_delta`.

The default condition is train-fit only on the 40-row V019B bridge smoke. It is
a learning-path verification, not a held-out model-quality claim.

## What This Test Does Not Prove

- no learned world-model quality
- no ARC solve evidence
- no signed-Y supervision quality
- no potential-family interpretability
- no comparison against plain NanoWM

Those require a later registered dataset condition, comparator, seed, hardware,
metric, and bridge manifest.
