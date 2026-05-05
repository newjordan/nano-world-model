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

## What This Test Does Not Prove

- no learned world-model quality
- no ARC solve evidence
- no signed-Y supervision quality
- no potential-family interpretability
- no comparison against plain NanoWM

Those require a later registered dataset condition, comparator, seed, hardware,
metric, and bridge manifest.
