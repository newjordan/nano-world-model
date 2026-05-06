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
- V010: Built a broader coordinate-action bridge batch from V006 plus ft09 and
  tn36 ACTION6 coordinate surfaces, then held out the separate V023
  mirror-hazard family. Result: strong transfer with heldout signed-Y MAE
  `0.0150969`, ACTION6 MAE `0.0235673`, progress accuracy `1.0`, and positive
  best rank `1`; residual is a one-row ACTION6 time-phase edge.
- V011: Added V033 post-progress nonlocal replay as a second heldout family.
  Result: heldout signed-Y MAE `0.0105739`, progress accuracy `1.0`, positive
  best rank `1`, and top false-progress probability `0.000195519`; this gates
  progress/nonlocal transfer but does not test ACTION6.
- V012: Held out V016 controllability movement as an ACTION6-bearing ten-task
  family. Result: progress stayed safe, stasis stayed safe, but ACTION6 signed-Y
  MAE regressed to `0.110621` and ACTION6 time-phase remained the top residual.
- V013: Added V016 as support and held out V015 object-relative movement.
  Result: ACTION6 aggregate improved to `0.0513169`, but time-phase remained
  high at `0.159137`; generic support data is not enough.
- V014: Added safe coordinate/ACTION6/time-phase interaction features and
  reran V013/V012 comparable holdouts. Result: V015 heldout aggregate improved
  to signed-Y MAE `0.0160868`, and V016 heldout improved to `0.0393147`, but
  the two-row `ACTION6|dominant_group:time_phase` bucket remained the top
  error at `0.663465` and `0.684408`.
- V015: Added an opt-in signed-Y balancing objective for ACTION6 time-phase
  rows. Result: failed scout because the initial mask selected all ACTION6
  rows with nonzero time-phase potential (`484` train rows), not just the rare
  dominant bucket, and worsened V015 heldout aggregate to `0.0285546`.
- V016: Narrowed signed-Y balancing to dominant
  `ACTION6|dominant_group:time_phase` rows. Result: with matching ka59 support
  in train, the V015-heldout target bucket improved to `0.225540` and stopped
  being the top error; V016B still failed when the V016/ka59 pattern was held
  out and absent from train (`0.633624`).

## Active Queue

1. V017: build a coordinate-family coverage or abstraction probe for the
   ka59-like ACTION6 time-phase branch.
   Goal: transfer the time-phase sign without requiring the exact heldout
   coordinate family in train. Candidate directions: coordinate-normalized
   relative-position features, paired coordinate-family support rows, or a
   small geometry-aware branch consistency objective.

2. C-model integration: route the calibration head output back into NanoWM
   chronometric branch scoring.
   Goal: move from posthoc calibration to world-model-planner scoring.

## Stop Rules

- Stop and inspect provenance if `git_dirty` is true for a recorded run.
- Stop if a split puts the same source artifact in both train and heldout.
- Stop if a new feature uses direct signed/progress target fields.
- Stop if progress rank improves while signed-Y bucket diagnostics regress
  without a named explanation.
