# Chronometric Goal Plan

Status: rolling plan. Update this after each calibration or diagnostic
iteration.

## Completed

- V001: Chronometric mechanics smoke with projector/invariant checks.
- V002: ARC-to-chronometric bridge manifest smoke with quarantine preserved.
- V003: Calibration MLP smoke over bridge-manifest features.
- V004: Controlled V031B group holdout.
- V005: Bucket diagnostics by action, control label, movement, time, and signed
  bands.
- V006: Cross-family holdout using V031B train and V019B heldout.
- V006B: Bounded signed-Y and potential-family heads to stop unbounded
  cross-family output explosion.
- V007: Added safe non-outcome potential-family inputs for stasis, loop, mirror,
  and hazard while continuing to exclude direct outcome/progress fields.
- V007B: Added feature-coverage diagnostics over V007 predictions to separate
  train/heldout coverage gaps from objective failures.

## Active Queue

1. V008: add a loop/stasis branch-consistency objective or paired contrastive
   diagnostic.
   Goal: distinguish repeated-action loops from single-step stasis without
   leaking direct signed outcomes.
   Evidence: V007B found only 3 same-label train rows for heldout
   ACTION5/stasis-loop, under different time-phase and movement conditions.

2. V009: expand cross-task coverage with a second heldout family.
   Goal: check whether safe potential inputs generalize beyond the current
   V031B to V019B family split.

3. C-model integration: route the calibration head output back into NanoWM
   chronometric branch scoring.
   Goal: move from posthoc calibration to world-model-planner scoring.

## Stop Rules

- Stop and inspect provenance if `git_dirty` is true for a recorded run.
- Stop if a split puts the same source artifact in both train and heldout.
- Stop if a new feature uses direct signed/progress target fields.
- Stop if progress rank improves while signed-Y bucket diagnostics regress
  without a named explanation.
