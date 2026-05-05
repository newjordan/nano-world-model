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
- V008: Added prior-only same-action streak features. Result: fixed ACTION5 but
  regressed unseen ACTION6 stasis/no-change rows, so not promoted.
- V008B: Added a named negative-control auxiliary objective. Result: did not
  restore ACTION6 polarity under comparable CPU conditions, so not promoted.
- V008C: Gated temporal loop context to non-coordinate actions. Result: same
  aggregate regression as V008, so not promoted.
- V009: ACTION6 coverage proxy. Held out ft09 and tn36 ACTION6 artifacts in
  separate runs while including the sibling ACTION6 artifact in train. Result:
  repaired main ACTION6 polarity under proxy coverage, but exposed tiny
  missing-coverage coordinate ACTION6 time/translation buckets, so not promoted
  as a clean cross-family checkpoint.

## Active Queue

1. V010: build a broader coordinate-action bridge batch with more ACTION6
   coordinate/stasis/time examples while reserving a separate heldout family.
   Goal: turn the V009 coverage-proxy finding into a cleaner transfer test.

2. V011: expand cross-task coverage with a second heldout family.
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
