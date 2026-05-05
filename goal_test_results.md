# Chronometric Goal Test Results

Status: rolling result ledger. Newest result first.

## V008 Temporal Loop Context Line

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v008_temporal_loop_context_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v008_temporal_loop_context_cross_family/`
- `experiments/2026-05-05_chronometric_feature_coverage_v008_temporal_loop_context/`
- `experiments/2026-05-05_chronometric_calibration_v008b_negative_control_temporal_loop_context_cpu_comparable/`
- `experiments/2026-05-05_chronometric_bucket_eval_v008b_negative_control_temporal_loop_context_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v008c_gated_temporal_context_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v008c_gated_temporal_context_cpu/`

Condition:

- same V006/V007 cross-family manifest
- train family: V031B post-progress avoidance replay
- heldout family: V019B ten-task target-discriminated scout
- split key: `source_condition_artifact`
- seed: `20260505`
- comparable CPU reads recorded for V008, V008B, and V008C
- training data promoted: `False`

Findings:

- V008 temporal context fixed ACTION5 heldout signed-Y MAE:
  V007 `0.972137` to V008 `0.0199724`.
- V008 regressed ACTION6 heldout signed-Y MAE:
  V007 `0.0343842` to V008 `1.96562`.
- V008B negative-control objective did not restore ACTION6 under CPU:
  ACTION6 MAE `1.81562`, heldout total `2.1029090881347656`.
- V008C coordinate-action gating did not change the V008 aggregate:
  heldout total `0.8733570575714111`, ACTION6 MAE `1.96562`.

Decision:

Do not promote V008/V008B/V008C. V007 remains current best. The next step is
ACTION6 coordinate-action coverage, not stronger scalar weighting.

## V007B Feature Coverage Diagnostic

Artifacts:

- `experiments/2026-05-05_chronometric_feature_coverage_v007b_safe_potential_inputs/`

Condition:

- diagnostic over V007 predictions
- no new training
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/predictions.jsonl`
- training data promoted: `False`

Findings:

- worst heldout action/control bucket:
  `action:ACTION5|control_label:dominant_group:stasis_loop`
- rows: `38`
- signed-Y MAE: `1.3801347401581312`
- signed bias: `1.3801347401581312`
- nearest train bucket:
  `action:ACTION4|control_label:dominant_group:translation`
- nearest distance: `0.09656388286876233`
- same-label train rows: `3`
- same-label distance: `0.13204518981801616`

Decision:

V008 should not be a scalar knob change. The next issue is loop/stasis
representation and data coverage: heldout ACTION5/stasis-loop has sparse
same-label training support and aliases toward translation-like features.

## V007 Safe Potential Inputs

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v007_safe_potential_inputs_cross_family/`

Condition:

- train family: V031B post-progress avoidance replay
- heldout family: V019B ten-task target-discriminated scout
- split key: `source_condition_artifact`
- seed: `20260505`
- steps: `800`
- requested device: `auto`
- resolved device: `cpu`
- fallback: CUDA OOM due local GPU pressure
- training data promoted: `False`

Metrics:

- heldout final total: `0.26092466711997986`
- heldout loss reduction vs baseline: `1.1071387827396393`
- heldout signed-Y MAE: `0.18368175625801086`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- heldout top false-progress probability: `0.000129215550259687`

Bucket findings:

- ACTION6 signed-Y MAE improved to `0.0343842`.
- `stasis_no_change` signed-Y MAE improved to `0.000478867`.
- ACTION5/stasis-loop is now the main weakness:
  ACTION5 signed-Y MAE `0.972137`, stasis-loop signed-Y MAE `0.69665`.

Decision:

V007 is a real stabilization and feature-coverage gain. Next work should target
loop/repeated-action semantics, not learning-rate tuning.

## V006B Bounded Cross-Family Holdout

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v006b_bounded_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v006b_bounded_cross_family/`

Metrics:

- heldout final total: `1.0726784467697144`
- heldout signed-Y MAE: `0.7257595658302307`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- ACTION6 signed-Y MAE: `1.50313`

Decision:

Bounding signed-Y and family outputs stopped the V006 numerical explosion, but
the model still lacked the input surface needed to recognize stasis and loop
potentials across family holdout.

## V006 Cross-Family Holdout

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v006_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v006_cross_family/`

Metrics:

- heldout final total: `306464768.0`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- heldout signed-Y MAE: `6074.74`
- ACTION6 signed-Y MAE: `30371`

Decision:

Progress classification transferred, but unbounded signed-Y/family outputs made
the calibration numerically invalid on heldout ACTION6 rows.
