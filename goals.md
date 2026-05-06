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

Wire perception-trusted imagination into planner-facing branch choice. V027
proves branch scores flow through the NanoWM-compatible chronometric scoring
API, V028 proves deterministic selection works when multi-action state groups
exist, V029 validates heldout branch choice on the V033 nonlocal candidate
surface, V030 defines the A/B Q/A packet plus gridspace imagination raymap,
V031 adds the labeled-image to grid, 3D geometry, and strict ray accuracy gate,
V032 separates visual and temporal senses into confirmation records, and V033
makes imagined signed-Y outcome a pre-action simulation channel. V035 turns the
Dream Kernel ARC-Dream branch-rank mismatch into an explicit goal loop: every
reachable solved proxy map must rank the terminal-positive branch first without
weakening ray, identity, invariant, or quarantine gates. V036 closes that loop
with `96/96` terminal-positive branches ranked first and `0` unreachable
projection maps in the refreshed proxy eval. V037 then tests pre-action branch
choice over the same maps; V037B reaches `528/528` trusted-map oracle matches
after adding reachable safe-path progress to deterministic policy scoring.
V038 routes the same source maps through the repository's real CEM planner and
exposes mean-return rollout fragility (`94/96`, then `95/96` with a larger
budget). V039B isolates the issue by returning the best sampled trajectory for
the discrete decoded action surface and restores the base-budget CEM result to
`96/96`. V040 makes that fix the default CEM return path across planner,
experiment wiring, and configs, while preserving explicit `return_policy: mean`
as an override. V041 then crosses into the actual ARC-AGI-3 toolkit surface:
offline `ls20-9607627b` loads through `arc_agi.Arcade`, produces `64x64`
frames, enumerates current actions, emits candidate packets, and executes one
local step without online submission or score claims. V042 is invalidated as
model evidence: it was an actuator-only trace that bypassed the Nemo3/world
model, 3D geometry, ray gates, temporal simulation, and ModelDecision path.
V043 installs the standard boundary in code: the ARC wrapper is an actuator
inside the Nemo3/world-model flow, and the runner requires a validated
`arc_agi3.model_decision.v001` artifact before any non-I/O actuator step. V044
locks the internal model process inside that decision: the decision must include
an `arc_agi3.internal_thinking_lock.v001` artifact with sha256, pre-actuator
ordering, and selected-action binding. V045 makes Nemo3 final confirmation a
mandatory end-of-thinking signoff: action selection must come from the internal
world-model process, Nemo3 must confirm the locked decision before the actuator
steps, and ambiguity or open questions must trigger interim Nemo3 confirmation
inside the mental loop. V046 links the NanoWM action-conditioned transformer
path and the chronometric calibration/library path at the action boundary: a
valid ModelDecision must carry a `chronometric.game_knowledge_link.v001` packet
showing that branch simulation consumed the SwiGLU/action-embedding backbone,
`ChronometricCalibrationMLP`, branch-library fallback, and
`NanoWM.score_chronometric_branch` surface. V047 adds the reset-only producer
side: the real offline `ls20-9607627b` reset observation now emits the full
observation -> 3D/world-state -> chronometric game knowledge -> branch
simulation -> trust checks -> internal-thinking lock -> Nemo3 final
confirmation -> ModelDecision artifact chain with `0` actuator steps. The
recorded V047 run used explicit `contract-local` Nemo confirmation, so the next
readiness gate is a `--nemo-mode live-relay` run before any challenge-step
claim. V048 passes that live-relay producer gate: local vLLM served
`nemotron_3_nano_omni` at `http://127.0.0.1:8000/v1/responses`, Nemo3 returned
final JSON confirming the internally selected `ACTION1:1`, and the producer
still executed `0` actuator steps. V049 connects that live-Nemo ModelDecision
to the actuator runner: before stepping, the runner now checks that the current
actuator observation content matches the ModelDecision observation artifact;
the guarded one-step run consumed V048, executed exactly one local offline
`ACTION1:1` step, and carried the Nemo3/chronometric SHA provenance into the
trace. V052/V053 make the MLP loop explicit in the same standard path: the
producer must consult a required `arc_agi3.mlp_consultation.v001` artifact
before branch simulation, branch scores consume those priors, and the actuator
must write a candidate-only `arc_agi3.post_action_mlp_update_candidate.v001`
artifact after the step. V053 records `mlp_weights_updated=False` and
`training_data_promoted=False`; update candidates are evidence for a later
promotion gate, not silent online learning. V054/V055 then run the repeated
standard loop as an offline solve scout. The loop holds for `40` live-Nemo
ModelDecision/action cycles with post-action MLP feedback context, but does
not solve `ls20`: levels stay `0 -> 0` against `win_levels=7`. The current
blocker is branch-value calibration, not actuator connectivity.

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
- Do not hardcode gameplay concept lists as the planner ontology. Concepts like
  mirrors, traps, fuel, locks, or hazards may emerge as hypotheses, but the
  root interface is A/B state, open questions, dimensional gridspace, modifier
  confidence, and candidate branches.
- Do not let raycasts influence action selection unless the map perception gate
  reports trusted labels, geometry, and ray contacts.
- Do not run non-I/O ARC actions from a direct `env.action_space` policy. The
  only standard execution route is observation -> 3D/world state -> internal
  chronometric game-knowledge link -> MLP consultation -> branch simulation ->
  trust checks -> internal-thinking lock -> Nemo3 final confirmation ->
  ModelDecision artifact -> actuator step -> post-action MLP update candidate.
- Do not execute an ARC actuator step unless the ModelDecision contains a
  locked internal-thinking artifact that predates the actuator step and binds
  to the selected action.
- Do not execute an ARC actuator step unless branch simulation proves it used
  the linked NanoWM/action-embedding and chronometric calibration/library
  knowledge packet.
- Do not execute an ARC actuator step unless branch simulation proves it used
  the linked pre-action MLP consultation artifact; post-action MLP observations
  may be written as candidate updates, but weights cannot update without an
  explicit promotion condition.
- Do not execute an ARC actuator step unless Nemo3 has signed off after the
  internal-thinking lock and before the actuator step. Nemo3 may confirm
  ambiguous internal navigation intermittently, but it is not the selected
  action source.
- Treat `contract-local` Nemo confirmation as a contract/path smoke only. It
  can validate artifact shape and ordering, but it is not live external Nemo3
  signoff for a challenge step.
- Keep observed outcome values as post-action calibration labels, not as visual
  or temporal sense inputs.
- Keep imagined outcome values as pre-action simulation outputs that the
  planner may use for branch choice.
- Do not weaken the Dream Kernel branch-rank gate to make planner integrity look
  better. Fix the value calibration or mark the projection map as invalid.

## Active Metrics

- Heldout progress accuracy.
- Heldout positive progress best rank.
- Heldout signed-Y MAE.
- Heldout bucket signed-Y MAE by action, control label, movement, and time.
- Top heldout false-progress probability.
- Dream Kernel terminal-positive branch rank on reachable solved proxy maps.
- Dream Kernel pre-action policy/oracle branch-choice match rate.
- Dream Kernel CEM rollout success rate and mean final safe path steps.
- ARC-AGI-3 offline I/O validity and candidate action packet count.
- ARC-AGI-3 standard model-flow validity: trusted 3D/world-state artifact,
  linked chronometric game-knowledge artifact, linked MLP consultation artifact,
  branch simulation, locked internal-thinking artifact, ModelDecision artifact,
  mandatory Nemo3 final signoff, post-action MLP update-candidate capture, and
  at most one actuator step.
- ARC-AGI-3 offline solve-scout validity: repeated standard model-flow actions,
  live Nemo3 invocation count, post-action MLP feedback context continuity,
  levels-completed delta, and offline solve detection.

## Current Best Checkpoint

V026 cross-family branch-library validation:

- inference:
  `experiments/2026-05-05_chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions/`
- bucket diagnostics:
  `experiments/2026-05-05_chronometric_bucket_eval_v026_v015_holdout_cross_family/`
- feature diagnostics:
  `experiments/2026-05-05_chronometric_feature_coverage_v026_v015_holdout_cross_family/`

V026 applies the V025 library/fallback stack to the V015 object-relative
heldout family from the V016 source calibration. It uses train targets only,
uses no heldout labels, and records clean `git_dirty=False` conditions.

- source calibration heldout signed-Y MAE: `0.023143382743000984`
- V026 heldout signed-Y MAE: `0.000009222477674484252`
- heldout progress accuracy: `1.0`
- library entries: `550`
- adjusted records: `6770`, including `339` heldout records
- fallback records: `23`, all heldout
- heldout translation/time-phase/stasis-loop signed-Y MAE: `0.0`
- heldout stasis-no-change signed-Y MAE: `0.000060475263439241`

V026 validates that the V025 mechanism transfers across the V016 and V015
heldout families. The remaining residual is tiny non-progress
stasis-no-change bias, so the next useful work is planner/C-model integration
or a fresh heldout manifest, not more manual knob tuning on V015/V016.

V027 planner-facing scoring smoke:

- scorer:
  `src/chronometric_planner_scoring.py`
- runnable harness:
  `scripts/score_chronometric_planner_branches.py`
- artifact:
  `experiments/2026-05-05_chronometric_planner_branch_score_v027_v015_holdout_cross_family/`

V027 scores all V015-heldout cross-family rows through a
`score_chronometric_branch`/`score_branch` compatible path. It verifies that
the train-built branch library and potential fallbacks are applied by the
chronometric scoring surface rather than only by the posthoc adjustment script.

- records scored: `7732`
- planner-applied records: `6770`
- planner-fallback records: `23`
- heldout planner-applied records: `339`
- heldout applied target signed-Y MAE: `3.4879953504312003e-09`
- heldout unapplied records: `61`

This is an integration smoke, not a new calibration metric. It closes the
immediate API gap and leaves branch selection/planner objective wiring as the
next active engineering target.

V028 branch selection smoke:

- selector:
  `src/chronometric_branch_selection.py`
- runnable harness:
  `scripts/select_chronometric_branches.py`
- artifact:
  `experiments/2026-05-05_chronometric_branch_selection_v028_v015_holdout_cross_family/`

V028 groups V027 planner-score rows by `split`, `task_id`, `frame_hash`, and
`t`, then selects one branch per multi-action state group using the
`library_or_calibration` score policy. Selection does not use target labels;
targets are used only for diagnostics.

- candidate records: `7732`
- selectable multi-action groups: `774`
- selected records: `774`
- oracle signed-best match rate: `1.0`
- heldout candidate records: `400`
- heldout selected records: `0`

The selector works on available multi-action groups, but those groups are all
train-side in this manifest. The next useful research step is a heldout/action
candidate manifest, not more selector tuning on V015.

V029 heldout action-candidate branch selection:

- planner scores:
  `experiments/2026-05-05_chronometric_planner_branch_score_v029_v033_heldout_action_candidates/`
- selector artifact:
  `experiments/2026-05-05_chronometric_branch_selection_v029_v033_heldout_action_candidates/`

V029 reuses the recorded V011/V033 nonlocal heldout family because it contains
real same-state action alternatives. It scores those rows through the V027
planner-facing scorer, then selects branches with the V028 selector.

- candidate records: `6932`
- heldout candidate records: `3112`
- selectable groups: `891`
- heldout selectable groups: `179`
- heldout selected records: `179`
- heldout oracle signed-best match rate: `1.0`
- heldout progress-positive selected records: `1`

This closes the heldout branch-choice blocker for a recorded candidate surface.
The next step should wire this objective into fuller planner/CEM flow rather
than adding another posthoc selector variant.

## Checkpoint History

V007 safe potential inputs:

- calibration: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/`
- bucket diagnostics: `experiments/2026-05-05_chronometric_bucket_eval_v007_safe_potential_inputs_cross_family/`

V007 improves cross-family heldout signed-Y MAE from V006B `0.7257596` to
`0.1836818` while keeping heldout progress accuracy `1.0` and heldout positive
best rank `1`.

V008/V008B/V008C are recorded as non-promoted follow-up diagnostics. They fixed
the ACTION5 bucket but regressed unseen coordinate-bearing ACTION6 stasis rows,
so V007 remains the current best checkpoint.

V009 ACTION6 coverage probes are recorded as coverage diagnostics, not clean
cross-family promotions. They hold out one V019B ACTION6 artifact while putting
the sibling ACTION6 artifact in train. This repaired the main ACTION6 polarity
failure under the proxy condition:

- ft09 heldout ACTION6 signed-Y MAE: `0.00453176`
- tn36 heldout ACTION6 signed-Y MAE: `0.0698827`
- tn36 heldout stasis-loop signed-Y MAE: `0.0143605`

The remaining V009 tn36 errors are tiny missing-coverage coordinate ACTION6
time/translation buckets, so the next target is broader coordinate-action
coverage with a separate heldout family.

V010 is the first broader coordinate-action coverage checkpoint with a separate
heldout family:

- merged manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/`
- calibration: `experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/`
- heldout family: V023 mirror-hazard current-state scout
- heldout signed-Y MAE: `0.0150969`
- heldout ACTION6 signed-Y MAE: `0.0235673`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`

V010 validates that the ACTION6 coordinate-action coverage improves transfer
to a separate heldout family. Its residual is a one-row ACTION6 time-phase edge,
so the next target is second-family validation and/or a small time-phase support
batch, not scalar loss weighting.

V011 validates progress/nonlocal transfer on a second heldout family:

- merged manifest: `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/`
- calibration: `experiments/2026-05-05_chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu/`
- heldout family: V033 post-progress nonlocal replay
- heldout rows: `3112`
- heldout progress-positive rows: `25`
- heldout signed-Y MAE: `0.0105739`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`

V011 did not contain ACTION6, so it does not close the V010 ACTION6 time-phase
residual. The next target is an ACTION6-bearing ten-task heldout family.

V012/V013 isolate the ACTION6 residual:

- V012 held out V016 controllability movement: ACTION6 signed-Y MAE `0.110621`,
  time-phase signed-Y MAE `0.124584`, top false-progress probability
  `0.00150808`.
- V013 added V016 as support and held out V015 object-relative movement:
  ACTION6 signed-Y MAE improved to `0.0513169`, but time-phase signed-Y MAE
  remained high at `0.159137`.

The current blocker is now precise: coordinate-bearing ACTION6 time-phase
polarity. More generic support data improves ACTION6 overall, but does not
teach the rare time-phase sign correctly.

V014/V016 split that blocker into representation, objective, and coverage
pieces:

- V014 added safe ACTION6/time-phase interaction features. V015 heldout
  aggregate improved to signed-Y MAE `0.0160868`, but the two-row
  `ACTION6|dominant_group:time_phase` bucket stayed bad at signed-Y MAE
  `0.663465`.
- V015 broad time-phase balancing was a failed scout: it selected `484` train
  rows instead of the intended tiny dominant bucket and worsened heldout
  aggregate MAE to `0.0285546`.
- V016 narrowed balancing to dominant `ACTION6|time_phase` rows. With matching
  V016/ka59 support in train and V015 held out, the target bucket improved from
  V014 `0.663465` to `0.225540`; top heldout error moved to
  `ACTION5|time_phase`. The V016B comparator still failed when the heldout
  V016/ka59 pattern was absent from train, leaving `ACTION6|time_phase` at
  `0.633624`.

The active blocker is therefore not just loss pressure. The chronometric
surface needs coordinate-family coverage or a geometry-aware coordinate
abstraction that can transfer the ka59-like time-phase branch without seeing
that exact support pattern.

V017 tested the coordinate-family coverage hypothesis directly by adding V015
object-relative ka59 support while holding out V016 controllability:

- coverage alone still failed, leaving V015 train ka59 at `-0.972088` and V016
  heldout ka59 at `-0.965180`.
- coverage plus narrow dominant-bucket balance fit the V015 train ka59 row
  (`0.230786`) and partially moved V016 heldout ka59 (`-0.670377`), but the
  heldout `ACTION6|time_phase` bucket remained the top error at `0.465186`.

The next active blocker is now sharper: a geometry abstraction must connect
object-relative and controllability ka59-like branches, not simply add more
rows or more rare-bucket weight.

V018 added coordinate-centered, radial, wall-distance, movement-magnitude, and
movement-alignment features. It helped but did not solve the branch transfer:

- heldout signed-Y MAE improved to `0.0201822`.
- V016 heldout ka59 moved from V017B `-0.670377` to `-0.589080`.
- `ACTION6|time_phase` remained the top heldout bucket at signed-Y MAE
  `0.430918`.

Passive geometry features are useful but still insufficient. The next likely
step is an explicit branch-consistency or paired-family objective that teaches
matched coordinate-family rows to share signed-Y polarity across source
families.

V019 added explicit branch-consistency mechanics:

- Train-only consistency was clean but ineffective for ka59 because train only
  contained tn36 matched pairs (`3` pairs, key `x:61|y:1`), so it reproduced
  V018.
- V019B allowed unlabeled heldout branch features into consistency pairs while
  still excluding heldout labels. This is a transductive diagnostic, not a
  promotable heldout-quality claim.
- V019B created `7` consistency pairs, including the ka59 key `x:28|y:30`, and
  moved V016 heldout ka59 to `0.230412`.
- Heldout `ACTION6|time_phase` dropped to signed-Y MAE `0.0136911`; the top
  heldout bucket moved to `ACTION5|time_phase`.

The mechanism is validated: matched branch consistency solves the ka59 polarity
when the matching branch is available as an unlabeled candidate. The next
research step is to make that mechanism non-transductive by generating or
learning candidate branch pairs inside the world-model planner, instead of
borrowing heldout features from the eval split.

V020 converted the mechanism into a non-transductive branch-library hotload:

- the library is built from train split targets only and keyed by ACTION6
  time-phase coordinate geometry.
- V020 adjusted `8` records total (`6` train, `2` heldout) and used no heldout
  labels.
- heldout `ACTION6|time_phase` reached signed-Y MAE `0.0`; heldout ka59 moved
  from raw V18 `-0.589080` to `0.250244`.
- overall heldout signed-Y MAE was `0.0180276`; top heldout error moved to
  `ACTION5|time_phase`.

This is now a plausible harness mechanism rather than a transductive training
trick. The next target is integrating branch-library hotload into NanoWM
chronometric branch scoring and then broadening the library beyond ACTION6
time-phase.

V021 integrated the branch-library hotload into `score_branch`:

- `ChronometricContortionLayer.score_branch` now accepts a train-built branch
  library plus row-like branch contexts and adjusts scored `outcome_y` by
  geometry key.
- `NanoWM.score_chronometric_branch` forwards the optional branch-library
  inputs, keeping normal residual forward passes unchanged.
- The scoring hook records `chronometric_branch_library_applied` in
  chronometric metrics.

This moves the V020 mechanism from a posthoc JSON adjustment into the actual
planner-facing branch scoring surface.

V022 broadened the branch-library grid beyond legacy ACTION6 time-phase:

- added explicit library scopes for legacy `action6_time_phase`,
  `dominant_time_phase`, `dominant_translation`, and combined
  `time_phase_translation`.
- V022 used the combined scope on the same V018 prediction base, with train
  targets only and no heldout labels.
- library entries increased from V020 `4` to `120`; adjusted heldout records
  increased from `2` to `239`.
- heldout signed-Y MAE improved from V020 `0.0180276` to `0.0064036`, with
  progress accuracy still `1.0`.
- heldout time-phase MAE dropped to `0.00538715`; translation MAE dropped to
  `0.0071873`.

The remaining top residual is now
`ACTION5|dominant_group:translation` at signed-Y MAE `0.0751201`. The
failure rows are mostly missing exact changed-cell prototypes for the heldout
`g50t` movement pattern, not an ACTION6 time-phase issue.

V023 added an observation-derived fallback for missing translation prototypes:

- fallback scope `dominant_translation_potential` is opt-in and defaults off.
- when no train library key exists for a dominant translation row, it uses the
  observed `transition.changed_cells` potential as the signed-Y estimate.
- V023 adjusted `6072` records, including `15` heldout fallback rows, with no
  heldout labels.
- heldout signed-Y MAE improved from V022 `0.0064036` to `0.00214512`.
- heldout translation MAE reached `0.0`; progress accuracy stayed `1.0`.

The remaining top residual is small and now sits in missing time-phase
prototype rows, led by `ACTION1|dominant_group:time_phase` at signed-Y MAE
`0.023844`.

V024 added the matching observation-derived fallback for time-phase rows:

- fallback scope `time_phase_translation_potential` handles missing
  time-phase and translation prototypes from observed potential-family values.
- V024 adjusted `6077` records, including `20` heldout fallback rows, with no
  heldout labels.
- heldout signed-Y MAE improved from V023 `0.00214512` to `0.00184883`.
- heldout translation and time-phase MAE both reached `0.0`; progress accuracy
  stayed `1.0`.

The remaining residual has moved to stasis-loop behavior. The top bucket is
`ACTION6|dominant_group:stasis_loop` at signed-Y MAE `0.0108481`, followed by
`ACTION5|dominant_group:stasis_loop` at `0.00760109`.

V025 broadened the train-built branch library to stasis-loop behavior:

- added `dominant_stasis_loop` and combined
  `time_phase_translation_stasis_loop` library scopes.
- stasis-loop keys use action, changed-cell count, and safe time step, which
  keeps early partial loop penalties separate from later full stasis penalties.
- V025 used train targets only, with the V024 potential fallback still enabled
  for missing time-phase/translation rows.
- heldout signed-Y MAE improved from V024 `0.00184883` to
  `0.0000961539`.
- heldout translation, time-phase, and stasis-loop MAE all reached `0.0`;
  progress accuracy stayed `1.0`.

The remaining residual is now tiny stasis-no-change bias, led by
`ACTION1|stasis_no_change` at signed-Y MAE `0.00101436`. This suggests the
current heldout family is nearly saturated as a calibration target.

V026 validated the same branch-library/fallback stack on the flipped V015
object-relative heldout family:

- source calibration:
  `experiments/2026-05-05_chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu/`
- branch-library inference:
  `experiments/2026-05-05_chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions/`
- source calibration heldout signed-Y MAE was `0.023143382743000984`.
- V026 heldout signed-Y MAE was `0.000009222477674484252`.
- heldout translation, time-phase, and stasis-loop MAE all reached `0.0`;
  progress accuracy stayed `1.0`.
- the only remaining control residual was stasis-no-change at signed-Y MAE
  `0.000060475263439241`.

This cross-family check is the first strong evidence that the chronometric
prototype/fallback mechanism is reusable across these movement families rather
than only saturating the V016 heldout split.

V027 moved that mechanism into a planner-facing scoring harness:

- added `src/chronometric_planner_scoring.py`.
- added `scripts/score_chronometric_planner_branches.py`.
- added focused tests for the NanoWM-compatible scoring surface.
- scored `7732` V015-heldout cross-family rows through the scorer.
- matched applied branch-library/fallback references with max absolute diff
  `1.1920928955078125e-07`.

The branch score API is now runnable. The next integration should consume these
scores in branch selection or CEM/objective logic.

V028 consumed V027 scores in deterministic branch selection:

- added `src/chronometric_branch_selection.py`.
- added `scripts/select_chronometric_branches.py`.
- added focused branch-selection tests.
- selected `774` train-side multi-action groups with oracle signed-best match
  rate `1.0`.
- found `0` heldout selectable groups under the current state key.

The next bottleneck is not the selector. It is a heldout data surface that
contains real action alternatives for the same state.

V029 found and used that heldout data surface in the existing V011/V033
nonlocal family:

- scored `6932` V011 rows through the planner-facing scorer.
- applied the branch-library path to `2937` heldout rows.
- selected `179` heldout multi-action groups.
- heldout oracle signed-best match rate was `1.0`.

This makes the next engineering target explicit: consume chronometric branch
selection inside the fuller planner path.
