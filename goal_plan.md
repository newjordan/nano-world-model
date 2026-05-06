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
- V017: Added V015 object-relative family as support while holding out V016
  controllability movement. Result: support alone did not fit even the train
  V015 ka59 row (`-0.972088`); support plus narrow balance fit train ka59
  (`0.230786`) and partially improved V016 heldout ka59 (`-0.670377`), but
  `ACTION6|time_phase` remained the top heldout error at `0.465186`.
- V018: Added coordinate geometry features: centered x/y, center radius,
  wall-distance, movement magnitude, movement alignment, and ACTION6 time-phase
  geometry interactions. Result: heldout signed-Y MAE improved to `0.0201822`,
  and V016 heldout ka59 improved from V017B `-0.670377` to `-0.589080`, but
  `ACTION6|time_phase` remained the top error at `0.430918`.
- V019: Added branch-consistency objective over matched ACTION6 time-phase
  coordinate keys. Result: train-only consistency found only tn36 pairs and
  reproduced V018; V019B transductive consistency used unlabeled heldout
  features, paired the ka59 key, moved V016 heldout ka59 to `0.230412`, and
  reduced heldout `ACTION6|time_phase` MAE to `0.0136911`. V019B is diagnostic,
  not a clean heldout promotion.
- V020: Added a train-built branch-library hotload path and applied it to V018
  predictions. Result: adjusted `8` ACTION6 time-phase records, used no heldout
  labels, moved V016 heldout ka59 from raw `-0.589080` to `0.250244`, and
  reduced heldout `ACTION6|time_phase` MAE to `0.0`.
- V021: Integrated branch-library hotload into `ChronometricContortionLayer`
  and `NanoWM.score_chronometric_branch`. Result: planner-facing branch scoring
  can now apply train-built geometry-key prototypes through row-like branch
  contexts while leaving normal residual forward passes unchanged.
- V022: Broadened branch-library support beyond ACTION6 time-phase using
  explicit `dominant_time_phase`, `dominant_translation`, and combined
  `time_phase_translation` scopes. Result: heldout signed-Y MAE improved from
  V020 `0.0180276` to `0.0064036` with progress accuracy `1.0`; the blocker
  moved to missing exact ACTION5 translation prototypes.
- V023: Added an opt-in observation-derived translation fallback for missing
  branch-library prototypes. Result: heldout signed-Y MAE improved to
  `0.00214512`, translation MAE reached `0.0`, and progress accuracy stayed
  `1.0`.
- V024: Added an opt-in observation-derived time-phase fallback and combined it
  with the translation fallback. Result: heldout signed-Y MAE improved to
  `0.00184883`, translation/time-phase MAE reached `0.0`, and progress
  accuracy stayed `1.0`.
- V025: Broadened train-built branch-library coverage to stasis-loop behavior
  with time-separated stasis-loop keys. Result: heldout signed-Y MAE improved
  to `0.0000961539`, translation/time-phase/stasis-loop MAE all reached `0.0`,
  and progress accuracy stayed `1.0`.
- V026: Validated the V025 branch-library/fallback stack on the flipped V015
  object-relative heldout family using V016-source calibration predictions.
  Result: source calibration heldout signed-Y MAE `0.0231434` dropped to
  `0.00000922248`, translation/time-phase/stasis-loop MAE stayed `0.0`,
  progress accuracy stayed `1.0`, and the only residual was tiny
  stasis-no-change bias.
- V027: Added a planner-facing branch scoring harness that routes row-like
  branch contexts through a `score_chronometric_branch`/`score_branch`
  compatible surface. Result: scored `7732` rows, applied the
  branch-library/fallback path to `6770`, applied `339` heldout rows, and
  matched applied references with max absolute diff `1.19209e-07`.
- V028: Added deterministic branch selection over V027 planner scores. Result:
  found `774` selectable multi-action groups and selected signed-best branches
  with oracle match rate `1.0`, but all selectable groups were train-side; the
  V015 heldout split had `400` candidate records and `0` multi-action heldout
  groups.
- V029: Reused the existing V011/V033 nonlocal heldout family as a heldout
  action-candidate surface. Result: planner-scored `6932` rows, applied
  branch-library scoring to `2937` heldout rows, selected `179` heldout
  multi-action groups, and reached heldout oracle signed-best match rate `1.0`
  without target labels in selection.
- V030: Added the A/B-centered open Q/A overlay packet with an internal
  imagination frame. Result: unrestricted objective-modifier questions,
  free-form modifier names, confidence validation, branch-score row references,
  2D/3D/latent raytrace probes, and a deterministic gridspace raymap producer
  are now represented without hardcoded gameplay taxonomy.
- V031: Added a labeled map perception and accuracy gate. Result: clean
  palette-labeled screenshots can become integer grids, grids can become simple
  3D height geometry, non-wall objects emit rays, and cell/height/ray contact
  accuracy must pass a strict trust gate before ray evidence is usable; a
  harness now writes condition, geometry, metrics, and result artifacts.

## Active Queue

1. Ray-gated branch selection: feed V031 trusted ray evidence into V029-style
   candidate selection as an auxiliary explanation/trust signal, not as a
   target label.
   Goal: prove the internal map can constrain action choice without bypassing
   NanoWM scoring.

2. Raw screenshot perception adapter: add a renderer/screenshot fixture or
   detector stub that produces the palette-labeled image required by V031.
   Goal: separate image parsing accuracy from geometry/raycast correctness.

3. Full NanoWM/CEM integration: wire chronometric scoring into the real
   planner path once heldout branch choice has a small deterministic smoke.
   Goal: avoid hiding scorer bugs inside diffusion rollout complexity.

4. Fresh heldout family: build or select the next heldout family beyond
   V015/V016 after the action-candidate manifest is available.
   Goal: test whether the mechanism survives a new family with real branch
   alternatives instead of polishing a nearly saturated split.

5. Stasis-no-change guardrail: keep the tiny residual visible in diagnostics,
   but do not tune directly against it unless it grows on a new heldout family.
   Goal: prevent research drift into cosmetic residual chasing.

## Stop Rules

- Stop and inspect provenance if `git_dirty` is true for a recorded run.
- Stop if a split puts the same source artifact in both train and heldout.
- Stop if a new feature uses direct signed/progress target fields.
- Stop if progress rank improves while signed-Y bucket diagnostics regress
  without a named explanation.
