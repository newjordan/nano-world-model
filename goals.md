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
