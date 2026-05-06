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
- V032: Added visual and temporal sensory alignment records. Result: 2D map,
  3D geometry projection, ray trust, predicted next-state, observed next-state,
  and outcome confirmation now form one confirmation record per state/action.
- V033: Corrected outcome handling. Result: imagined signed-Y outcome is now a
  pre-action simulation channel with confidence, observed signed-Y outcome is
  post-action calibration truth, and the record compares the two without
  leaking observed outcome into visual/temporal perception.
- V034: Added a deterministic sensory smattering harness. Result: five
  human-review cases cover direct positive movement, wall-blocked movement,
  temporal miss, visual map misread, and outcome-sign miss; the harness writes
  condition, metrics, records, results, and a `HUMAN_EVAL.md` review sheet.
- V034 run: Executed the human-eval smattering batch under clean conditions.
  Result: `2/5` combined trusted, `3/5` sensory trusted, `2/5`
  outcome-imagination trusted, with isolated visual, temporal, and outcome-sign
  failures available for human review.
- V035: Converted the ARC-Dream proxy eval branch-rank mismatch into a goal
  artifact. Result: `48` reachable solved proxy maps became calibration cases,
  all with terminal-positive branch rank `5`; cases split evenly across
  `t2_action_coordinate` and `t3_object_relative_branching`, while the one
  unsolved row remains isolated as `proxy_goal_unreachable_in_projection`.
- V036: Calibrated Dream Kernel branch values and repaired the isolated
  unreachable tier-4 projection. Result: the refreshed ARC-Dream proxy eval
  solved `96/96`, reached `96/96` goals avoiding hazards, passed planner
  integrity on `96/96`, produced terminal branch rank counts `{'1': 96}`, and
  left `0` branch-rank calibration cases.
- V037: Added a pre-action branch-choice scout over the V036 proxy maps. Result:
  the first run exposed one tier-4 detour where policy score chose a longer safe
  route (`529/530` policy/oracle matches), then V037B added reachable safe-path
  progress to policy scoring and reached `528/528` policy/oracle matches while
  the ARC-Dream proxy re-gate stayed `96/96` passed.
- V038: Added a real CEM rollout-complexity smoke over the V037B proxy maps.
  Result: the repository CEM planner with default mean-return policy solved
  `94/96`; a larger `512/64/12/h18` budget solved `95/96` but still exposed a
  zero-loss miss caused by averaging solved elite samples into a bad discrete
  decoded action sequence.
- V039B: Added an opt-in `best_sample` CEM return policy and reran the original
  `128/16/8/h16` budget against the V038 mean-return comparator artifact.
  Result: solved `96/96`, final safe path steps `0.0`, hazard hits `0`, and no
  training data promoted. The rollout complexity failure is now isolated to
  return semantics, not Dream Kernel reachability.
- V040: Promoted `best_sample` to the default CEM return policy across
  `CEMPlanner`, planning experiment wiring, CEM configs, and the rollout smoke
  CLI. Result: default-path V040 solved `96/96` at the original `128/16/8/h16`
  budget against the V038 comparator, with final safe path steps `0.0` and no
  training data promoted.
- V041: Added an ARC-AGI-3 offline I/O smoke over the real toolkit surface.
  Result: loaded downloaded `ls20-9607627b` from `/home/frosty40/world_model_1`,
  reset/read `64x64` frames, emitted `8` candidate action packets, executed
  one local offline step, and recorded no online submission, no score claim,
  and no training promotion.
- V042: Invalidated an ARC-AGI-3 actuator-only trace. Result: the runner
  stepped `ls20-9607627b` for `40` local actions with `repeat_capped_cycle`,
  but it bypassed the Nemo3/world-model flow, 3D geometry, ray gates, temporal
  simulation, and ModelDecision artifact. It is actuator plumbing evidence
  only, not model evidence. The runner now fails closed for multi-step use.
- V043: Added the ARC-AGI-3 standard model-flow boundary. Result:
  `src/arc_agi3_model_flow.py` defines the required ModelDecision contract,
  `scripts/run_arc_agi3_model_step.py` executes exactly one actuator step from
  that artifact, and direct multi-step actuator policy remains blocked.
- V044: Added the internal-thinking lock to the ARC-AGI-3 ModelDecision
  contract. Result: every model action now requires an
  `arc_agi3.internal_thinking_lock.v001` artifact with path, sha256,
  pre-actuator ordering, and selected-action binding before the actuator can
  step.
- V045: Added the mandatory Nemo3 final-confirmation contract. Result: every
  model action now requires final Nemo3 signoff after the internal-thinking
  lock and before the actuator step; Nemo3 is explicitly confirmation, not the
  action source, and interim Nemo3 confirmations are required when internal
  thinking records ambiguity or open questions.
- V046: Added the chronometric game-knowledge link to the ARC-AGI-3
  ModelDecision contract. Result: branch simulation must now prove it consumed
  a linked NanoWM action-conditioned transformer/SwiGLU surface,
  action-embedding context, `ChronometricCalibrationMLP`, branch-library
  fallback, and `NanoWM.score_chronometric_branch` packet before any action can
  be selected.
- V047: Added the ARC-AGI-3 reset-only ModelDecision producer for `ls20`.
  Result: `scripts/run_arc_agi3_model_decision_producer.py` reads the real
  `ls20-9607627b` reset observation, emits observation, 3D/world-state,
  chronometric game-knowledge, branch-simulation, trust-check,
  internal-thinking-lock, Nemo3 final-confirmation, and ModelDecision
  artifacts, validates the decision through `require_standard_model_decision`,
  and executes `0` actuator steps. The recorded run used explicit
  `contract-local` Nemo mode, so it is a contract/path proof, not a live
  external Nemo3 invocation.
- V048: Ran the same producer through the live Nemo3 relay. Result: the real
  `ls20-9607627b` reset observation emitted a valid
  `arc_agi3.model_decision.v001` artifact chain with
  `nemo3_external_model_invoked=True`, relay model
  `nemotron_3_nano_omni`, final confirmation JSON
  `confirms_selected_action=true`, selected action `ACTION1:1` from
  `world_model_internal_thinking`, and `0` actuator steps.
- V049: Connected the V048 live-Nemo ModelDecision to the standard one-step
  actuator runner. Result: `scripts/run_arc_agi3_model_step.py` now fails
  closed unless the current actuator observation content matches the
  ModelDecision observation artifact, then consumed the V048 decision, executed
  exactly one offline `ls20` step with `ACTION1:1`, carried Nemo3 and
  chronometric SHA provenance into the trace, and recorded no online submission
  or solve claim.
- V050: Added pre-action MLP consultation as a required standard-flow artifact.
  Result: the live-Nemo producer emitted `mlp_consultation.json` before branch
  simulation, branch scores consumed MLP priors, the ModelDecision validated,
  and the producer still executed `0` actuator steps.
- V051: Added post-action MLP update-candidate capture to the one-step runner.
  Result: the actuator consumed the V050 ModelDecision, executed exactly one
  offline `ls20` step, wrote `post_action_mlp_update.json`, and kept
  `mlp_weights_updated=False` with no training promotion.
- V052/V053: Reran the MLP-connected producer/actuator pair with explicit
  action/source evidence fields. Result: V052 produced a clean live-Nemo
  ModelDecision selecting `ACTION3:3` with `mlp_consultation` in the standard
  flow; V053 consumed that artifact, executed exactly one offline action, wrote
  a candidate-only post-action MLP update, and recorded no online submission or
  solve claim.
- V054/V055: Added and ran the bounded standard-model solve scout. Result: the
  loop successfully repeated ModelDecision -> live Nemo3 confirmation ->
  actuator -> post-action MLP update-candidate for `12` and then `40` offline
  `ls20` actions with `0` invalid decisions, `0` invalid actuator steps, and
  feedback context carried into every post-step MLP consultation. It did not
  solve: levels stayed `0 -> 0` against `win_levels=7`.

## Active Queue

1. Ingest V034 human labels after review. Goal: compare human accept/reject
   judgments against visual, temporal, and outcome-imagination trust signals.

2. Batch sensory-record builder: convert recorded state/action traces into
   confirmation-record JSONL for correlation sweeps.
   Goal: turn each datapoint into comparable visual and temporal evidence.

3. Raw screenshot perception adapter: add a renderer/screenshot fixture or
   detector stub that produces the palette-labeled image required by V031.
   Goal: separate image parsing accuracy from geometry/raycast correctness.

4. ARC-AGI-3 goal/value calibration for `ls20`: use V054/V055 traces to add a
   goal-directed branch signal that can distinguish frame-changing motion from
   actions that actually increase `levels_completed`.
   Goal: keep the repeated standard loop intact while making branch simulation
   optimize local solve progress, not just stable MLP priors and frame change.

5. Fresh heldout family: build or select the next heldout family beyond
   V015/V016 after the action-candidate manifest is available.
   Goal: test whether the mechanism survives a new family with real branch
   alternatives instead of polishing a nearly saturated split.

6. Stasis-no-change guardrail: keep the tiny residual visible in diagnostics,
   but do not tune directly against it unless it grows on a new heldout family.
   Goal: prevent research drift into cosmetic residual chasing.

## Stop Rules

- Stop and inspect provenance if `git_dirty` is true for a recorded run.
- Stop if a split puts the same source artifact in both train and heldout.
- Stop if a new feature uses direct signed/progress target fields.
- Stop if progress rank improves while signed-Y bucket diagnostics regress
  without a named explanation.
