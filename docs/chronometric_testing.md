# Chronometric Testing

Status: first test protocol for the chronometric NanoWM foundation.

The initial test surface is a mechanics smoke, not a model-quality benchmark.
It proves the installed chronometric primitives run under a recorded condition
before quarantined ARC data is allowed into this repo.

## V001 Mechanics Smoke

Runner:

```bash
python scripts/chronometric_mechanics_smoke.py --device auto
```

Default output:

```text
experiments/2026-05-05_chronometric_mechanics_smoke/
  condition.json
  metrics.json
  synthetic_bridge_manifest.jsonl
  RESULTS.md
```

Run label: `mechanics_smoke`

Run kind: `new_experiment`

Data policy: synthetic tokens only. No quarantined ARC Sprint 0 artifact is
read or converted.

## Gates

The runner checks:

- log-time phase advances by one cycle when internal time is scaled by
  `3722/2705`
- projector preserves the timelike invariant and enforces
  `u_mu F_cont^mu = 0`
- chronometric layer preserves invariant/orthogonality constraints over supplied
  branch directions
- same state can score distinct supplied branch directions
- action context changes `F_ext`
- residual mode applies a nonzero token update
- tiny NanoWM audit mode records metrics without changing model output
- a synthetic bridge manifest validates against the required ARC-to-NanoWM
  schema

## Bridge Rule

ARC-derived rows are still blocked until they appear in a manifest with:

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

Schema helpers live in `src/chronometric_bridge.py`. Existing Sprint 0 ARC data
should enter, if at all, with a quarantine status such as:

```text
control_source: arc_scaffold_non_chronometric
```

## V002 ARC Bridge Manifest Smoke

Runner:

```bash
python scripts/build_arc_bridge_manifest.py
```

Default source:

```text
/home/frosty40/world_model_1/
  experiments/2026-05-04_v019b_target_discriminated_scorer_scout/
    grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl
```

Default output:

```text
experiments/2026-05-05_arc_bridge_manifest_smoke/
  arc_bridge_manifest.jsonl
  condition.json
  summary.json
  RESULTS.md
```

This converts grid transition rows into the required bridge schema. It preserves
`control_source: arc_scaffold_non_chronometric` and does not promote the output
to training data.

## V003 Chronometric Calibration Smoke

Runner:

```bash
python scripts/train_chronometric_calibrator.py
```

Default source:

```text
experiments/2026-05-05_arc_bridge_manifest_smoke/arc_bridge_manifest.jsonl
```

Default output:

```text
experiments/2026-05-05_chronometric_calibration_smoke/
  condition.json
  metrics.json
  predictions.jsonl
  RESULTS.md
```

This trains a small calibration MLP over bridge-manifest features. It predicts
`signed_outcome_y`, progress probability, and potential-family activations.
Inputs intentionally exclude direct outcome labels and post-outcome fields:
`signed_outcome_y`, `event_mu.y`, `branch_direction_n.y`, `level_delta`,
`next_levels_completed`, `eta_total`, `outcome_sign`, and
`goal_progress.level_delta`.

The default condition is train-fit only on the 40-row V019B bridge smoke. It is
a learning-path verification, not a held-out model-quality claim.

## V004 Controlled Batch Holdout

Bridge runner:

```bash
python scripts/build_arc_bridge_manifest.py \
  --run-label arc_bridge_manifest_v004_controlled_batch \
  --source-condition-artifact experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md \
  --source-transition-glob 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/grid/transition_events/*.jsonl' \
  --split arc_sprint0_v031b_m0r0_post_progress_group_holdout_v004 \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch
```

Calibration runner:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v004_group_holdout \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v004_group_holdout \
  --holdout-key source_artifact_path \
  --holdout-fraction 0.24
```

This is the first medium controlled batch. The split is by whole
`source_artifact_path` groups, not random rows, so a replay branch file cannot
appear in both train and heldout. The source condition remains a quarantined
ARC scaffold/control replay, and `training_data_promoted` remains false.

## V005 Bucket Diagnostics

Runner:

```bash
python scripts/analyze_chronometric_error_buckets.py
```

Default source:

```text
experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch/arc_bridge_manifest.jsonl
experiments/2026-05-05_chronometric_calibration_v004_group_holdout/predictions.jsonl
experiments/2026-05-05_chronometric_calibration_v004_group_holdout/metrics.json
```

Default output:

```text
experiments/2026-05-05_chronometric_bucket_eval_v005/
  condition.json
  bucket_metrics.json
  bucket_rows.jsonl
  RESULTS.md
```

This is a no-training diagnostic. It joins V004 predictions back to bridge rows
and reports errors by split, control label, action, dominant group, signed-Y
band, movement axis, time window, and changed-cell bucket.

## V006 Cross-Family Holdout

V006 keeps the V031B replay family as the training family and holds out the
V019B ten-task current-state family by `source_condition_artifact`.

V019B family bridge:

```bash
python scripts/build_arc_bridge_manifest.py \
  --run-label arc_bridge_manifest_v006_v019b_ten_task_family \
  --source-condition-artifact experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md \
  --source-transition-glob 'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/*.jsonl' \
  --split arc_sprint0_v019b_ten_task_family_v006 \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v006_v019b_ten_task_family
```

Merged cross-family bridge:

```bash
python scripts/merge_chronometric_bridge_manifests.py \
  --run-label arc_bridge_manifest_v006_cross_family \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch/arc_bridge_manifest.jsonl \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_v019b_ten_task_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v006_cross_family
```

Cross-family calibration:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v006_cross_family_holdout \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v006_cross_family_holdout \
  --holdout-key source_condition_artifact \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md
```

This is a family-transfer diagnostic. A good result means the progress head
stays calibrated outside the V031B replay family; it still does not establish
general ARC competence.

## V006B Bounded Cross-Family Holdout

V006 showed that the progress logit transferred, but the unbounded signed-Y and
family heads exploded on heldout ACTION6 rows. V006B reruns the same
cross-family condition with bounded signed-Y and potential-family outputs.

Runner:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v006b_bounded_cross_family_holdout \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v006b_bounded_cross_family_holdout \
  --holdout-key source_condition_artifact \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md
```

The progress head remains a logit. The signed-Y and family heads are passed
through `tanh` because their targets are bounded potential/outcome quantities.

## V007 Safe Potential Inputs

V006B stabilized the numeric failure, but its heldout bucket diagnostic still
put signed-Y error on ACTION6/stasis rows. The manifest already contains
non-outcome potential-family coordinates for stasis, loop, mirror, and hazard,
but the V006 calibrator only exposed transition-change and time-phase terms to
the MLP.

V007 expands the calibrator input surface with:

```text
stasis.no_change
loop.repeated_action
mirror.progress_path
mirror.progress_blocker
hazard.env_failure
```

It still excludes direct outcome/progress fields:
`signed_outcome_y`, `event_mu.y`, `branch_direction_n.y`, `level_delta`,
`next_levels_completed`, `eta_total`, `outcome_sign`, and
`goal_progress.level_delta`.

## V007B Feature Coverage Diagnostic

V007B is a no-training diagnostic over V007 predictions. It compares heldout
action/control feature means against train action/control feature means and
reports nearest train buckets.

Runner:

```bash
python scripts/analyze_chronometric_feature_coverage.py \
  --run-label chronometric_feature_coverage_v007b_safe_potential_inputs \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/predictions.jsonl \
  --out-dir experiments/2026-05-05_chronometric_feature_coverage_v007b_safe_potential_inputs
```

Use this diagnostic when a bucket remains wrong after a model/input change. A
small nearest-train distance with poor signed-Y means an objective/model issue;
sparse same-label rows or a high same-label distance means a coverage issue.

## V008 Temporal Loop Context

V008 adds prior-only temporal context features to the calibration input surface:

```text
same_action_streak_norm
same_action_low_change_streak_norm
```

These features are computed inside each `source_artifact_path` branch from rows
with lower or equal `t` only. They use action identity and low changed-cell
ratios, not signed outcomes, progress labels, future rows, or post-outcome
fields.

After V008/V008B diagnostics, V008C gates these features to non-coordinate
actions only. Coordinate-bearing rows can repeat an action id while pointing at
different cells, so treating those repeats as loop evidence aliases targeted
moves.

The V008 cross-family condition reuses the V006/V007 manifest and heldout split:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v008_temporal_loop_context_cross_family_holdout \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v008_temporal_loop_context_cross_family_holdout \
  --holdout-key source_condition_artifact \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md
```

## V008B Negative-Control Objective

V008 fixed the heldout ACTION5/stasis-loop bucket but regressed ACTION6 and
stasis/no-change. V008B keeps the temporal loop context and turns on an
auxiliary hinge objective for negative control rows:

```text
control_label in {stasis_no_change, dominant_group:stasis_loop}
signed_y <= negative_control_margin
```

The control label is used as supervision, not as an input feature.

Runner:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v008b_negative_control_temporal_loop_context \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v008b_negative_control_temporal_loop_context \
  --holdout-key source_condition_artifact \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md \
  --negative-control-weight 1.0 \
  --negative-control-margin -0.5
```

## V009 ACTION6 Coverage Proxy

V009 tests whether the V008 ACTION6 regression is a coverage failure. It is not
a clean cross-family promotion: one V019B ACTION6 artifact is held out while the
sibling V019B ACTION6 artifact remains in train.

ft09 holdout:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu \
  --holdout-key source_artifact_path \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_ft09_seed0.transitions.jsonl \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl \
  --device cpu
```

tn36 holdout:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu \
  --holdout-key source_artifact_path \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_tn36_seed0.transitions.jsonl \
  --heldout-group-value experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl \
  --device cpu
```

Posthoc diagnostics:

```bash
python scripts/analyze_chronometric_error_buckets.py \
  --run-label chronometric_bucket_eval_v009_action6_coverage_ft09_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/predictions.jsonl \
  --calibration-metrics experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/metrics.json \
  --out-dir experiments/2026-05-05_chronometric_bucket_eval_v009_action6_coverage_ft09_holdout_cpu

python scripts/analyze_chronometric_feature_coverage.py \
  --run-label chronometric_feature_coverage_v009_action6_coverage_ft09_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/predictions.jsonl \
  --out-dir experiments/2026-05-05_chronometric_feature_coverage_v009_action6_coverage_ft09_holdout_cpu

python scripts/analyze_chronometric_error_buckets.py \
  --run-label chronometric_bucket_eval_v009_action6_coverage_tn36_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/predictions.jsonl \
  --calibration-metrics experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/metrics.json \
  --out-dir experiments/2026-05-05_chronometric_bucket_eval_v009_action6_coverage_tn36_holdout_cpu

python scripts/analyze_chronometric_feature_coverage.py \
  --run-label chronometric_feature_coverage_v009_action6_coverage_tn36_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/predictions.jsonl \
  --out-dir experiments/2026-05-05_chronometric_feature_coverage_v009_action6_coverage_tn36_holdout_cpu
```

Promotion rule: V009 can support the coverage-gap hypothesis, but V007 remains
the clean cross-family checkpoint until a broader coordinate-action batch uses a
separate heldout family.

## V010 Coordinate-Action Coverage With V023 Heldout

V010 turns the V009 coverage-proxy finding into a cleaner transfer test. It
adds recorded ACTION6 coordinate surfaces to train and holds out the separate
V023 mirror-hazard current-state family by `source_condition_artifact`.

Bridge sources:

```bash
python scripts/build_arc_bridge_manifest.py \
  --run-label arc_bridge_manifest_v010_ft09_action6_affordance \
  --source-condition-artifact experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md \
  --source-transition-glob 'experiments/2026-05-04_v009_ft09_action6_affordance_sweep/grid/transition_events/*.jsonl' \
  --split arc_sprint0_v009_ft09_action6_affordance_v010_train_coverage \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v010_ft09_action6_affordance

python scripts/build_arc_bridge_manifest.py \
  --run-label arc_bridge_manifest_v010_ft09_targeted_coordinate \
  --source-condition-artifact experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md \
  --source-transition-glob 'experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/grid/transition_events/*.jsonl' \
  --split arc_sprint0_v010_ft09_targeted_coordinate_v010_train_coverage \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v010_ft09_targeted_coordinate

python scripts/build_arc_bridge_manifest.py \
  --run-label arc_bridge_manifest_v010_tn36_action6_heatmap \
  --source-condition-artifact experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md \
  --source-transition-glob 'experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/grid/transition_events/*.jsonl' \
  --split arc_sprint0_v011_tn36_action6_heatmap_v010_train_coverage \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v010_tn36_action6_heatmap

python scripts/build_arc_bridge_manifest.py \
  --run-label arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family \
  --source-condition-artifact experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md \
  --source-transition-glob 'experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/*.jsonl' \
  --split arc_sprint0_v023_mirror_hazard_family_v010_heldout \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family
```

Merged manifest:

```bash
python scripts/merge_chronometric_bridge_manifests.py \
  --run-label arc_bridge_manifest_v010_coordinate_action_coverage \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_ft09_action6_affordance/arc_bridge_manifest.jsonl \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_ft09_targeted_coordinate/arc_bridge_manifest.jsonl \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_tn36_action6_heatmap/arc_bridge_manifest.jsonl \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage
```

Calibration and diagnostics:

```bash
python scripts/train_chronometric_calibrator.py \
  --run-label chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl \
  --out-dir experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu \
  --holdout-key source_condition_artifact \
  --heldout-group-value experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md \
  --device cpu

python scripts/analyze_chronometric_error_buckets.py \
  --run-label chronometric_bucket_eval_v010_coordinate_action_coverage_v023_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/predictions.jsonl \
  --calibration-metrics experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/metrics.json \
  --out-dir experiments/2026-05-05_chronometric_bucket_eval_v010_coordinate_action_coverage_v023_holdout_cpu

python scripts/analyze_chronometric_feature_coverage.py \
  --run-label chronometric_feature_coverage_v010_coordinate_action_coverage_v023_holdout_cpu \
  --manifest experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl \
  --predictions experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/predictions.jsonl \
  --out-dir experiments/2026-05-05_chronometric_feature_coverage_v010_coordinate_action_coverage_v023_holdout_cpu
```

Promotion rule: V010 is a coordinate-action transfer checkpoint with
`training_data_promoted: False`. It does not prove ARC solve competence. Its
residual is a rare ACTION6 time-phase signed-Y edge, not progress ranking.

## What This Test Does Not Prove

- no learned world-model quality
- no ARC solve evidence
- no signed-Y supervision quality
- no potential-family interpretability
- no comparison against plain NanoWM

Those require a later registered dataset condition, comparator, seed, hardware,
metric, and bridge manifest.
