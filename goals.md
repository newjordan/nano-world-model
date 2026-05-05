# Chronometric World Model Goals

Status: active research foundation for a constrained 4D latent dynamics model.

This repo is the chronometric NanoWM integration lane. Quarantined ARC control
data may be bridged into chronometric manifests for diagnostics, but it is not
promoted to training data unless a later condition explicitly says so.

## Primary Goal

Build a small world-model foundation where state transitions are represented as
event-space motion with a signed Y outcome axis, learned potential-family
signals, phase/time features, and bounded branch calibration heads.

## Current Research Target

Turn bridge-manifest rows into a learnable chronometric calibration surface that
can separate progress branches from non-progress branches and localize signed-Y
failure families without manual scorer knob tuning.

## Hard Boundaries

- Preserve quarantined/control provenance on ARC-derived rows.
- Do not treat calibration smoke results as ARC solve evidence.
- Do not promote bridge rows into model training data without a recorded
  promotion condition.
- Keep direct outcome fields out of calibration inputs:
  `signed_outcome_y`, `event_mu.y`, `branch_direction_n.y`, `level_delta`,
  `next_levels_completed`, `eta_total`, `outcome_sign`, and
  `goal_progress.level_delta`.
- Record every run under `experiments/` with condition, metrics, predictions or
  analysis output, and a short result report.

## Active Metrics

- Heldout progress accuracy.
- Heldout positive progress best rank.
- Heldout signed-Y MAE.
- Heldout bucket signed-Y MAE by action, control label, movement, and time.
- Top heldout false-progress probability.

## Current Best Checkpoint

V007 safe potential inputs:

- calibration: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/`
- bucket diagnostics: `experiments/2026-05-05_chronometric_bucket_eval_v007_safe_potential_inputs_cross_family/`

V007 improves cross-family heldout signed-Y MAE from V006B `0.7257596` to
`0.1836818` while keeping heldout progress accuracy `1.0` and heldout positive
best rank `1`.
