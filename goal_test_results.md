# Chronometric Goal Test Results

Status: rolling result ledger. Newest result first.

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
