# Project Intent And Boundaries

Status: canonical boundary for the chronometric NanoWM fork.

This repo is the active chronometric model-body repo. The ARC scaffold repo at
`/home/frosty40/world_model_1` is preserved as non-chronometric control data and
harness evidence unless a future bridge manifest explicitly promotes a source
artifact into chronometric training/evaluation use.

## Active Model Body

Chronometric architecture work belongs here:

- `src/models/chronometric_contortion.py`
- `src/models/nanowm.py`
- `src/configs/model/nanowm_*.yaml`
- `tests/test_chronometric_contortion.py`
- `docs/chronometric_contortion_foundation.md`
- `docs/chronometric_foundation_review_v002.md`

This repo owns the 4D event-state dynamics, learned `4x4` contortion tensor,
projected force constraint, log-time phase modulation, branch-direction hook,
potential-family hook, and NanoWM integration surfaces.

## Quarantined ARC Scaffold

`/home/frosty40/world_model_1` is quarantined as the ARC-AGI-3
non-chronometric scaffold and control harness. Its Sprint 0 artifacts are useful,
but they are not chronometric model samples by default.

Allowed uses:

- preserve ARC harness provenance and failed/successful scout evidence
- mine labels, movement semantics, mirror-alignment hypotheses, and router
  control signals
- run harness/control smoke tests under recorded conditions
- generate bridge manifests for later NanoWM ingestion

Blocked uses:

- training this chronometric NanoWM fork as if old ARC scaffold rows were native
  chronometric samples
- claiming Sprint 0 router/MCTS metrics are model-training metrics
- silently importing ARC trajectories without quarantine provenance
- comparing non-chronometric control metrics to chronometric model metrics as if
  they share the same condition

## Required Bridge Manifest

Any future ARC-to-NanoWM ingestion must write a typed bridge manifest before data
is used here. Minimum required fields:

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

The default quarantine status for current `world_model_1` artifacts is:

```text
control_source: arc_scaffold_non_chronometric
```

## Current Rule

Develop the chronometric foundation in this repo first. Treat ARC scaffold data
as an external control corpus until a bridge artifact proves exactly how it was
converted into event-state, action-context, branch-direction, potential-family,
and signed-outcome tensors.
