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

## Active Queue

1. V007B: diagnose ACTION5/stasis-loop after V007.
   Evidence: V007 fixed ACTION6/stasis-no-change but ACTION5 stasis-loop remains
   the largest heldout signed-Y error bucket.

2. V008: add a loop/stasis branch-consistency objective or paired contrastive
   diagnostic.
   Goal: distinguish repeated-action loops from single-step stasis without
   leaking direct signed outcomes.

3. V009: expand cross-task coverage with a second heldout family.
   Goal: check whether safe potential inputs generalize beyond the current
   V031B to V019B family split.

4. C-model integration: route the calibration head output back into NanoWM
   chronometric branch scoring.
   Goal: move from posthoc calibration to world-model-planner scoring.

## Stop Rules

- Stop and inspect provenance if `git_dirty` is true for a recorded run.
- Stop if a split puts the same source artifact in both train and heldout.
- Stop if a new feature uses direct signed/progress target fields.
- Stop if progress rank improves while signed-Y bucket diagnostics regress
  without a named explanation.
