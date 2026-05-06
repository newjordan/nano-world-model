# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v017_v015_support_v016_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `8e81011df436d4ee56adf3ae36998f98daed28a6`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- records: `7732`
- progress-positive records: `52`
- train records: `7332`
- heldout records: `400`
- train progress-positive records: `52`
- heldout progress-positive records: `0`
- eval scope: `group_holdout_by_source_condition_artifact`
- device: `cpu`
- seed: `20260505`
- steps: `800`
- negative-control weight: `0.0`
- negative-control margin: `-0.5`
- ACTION6 time-phase signed balance: `False`
- ACTION6 time-phase train records: `6`
- ACTION6 time-phase signed weight: `None`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.140374183654785`
- train final total loss: `0.022264212369918823`
- train loss reduction vs baseline: `5.118109971284866`
- train signed-Y MAE final: `0.005296235904097557`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.08651018887758255`

## Heldout Metrics

- heldout baseline total loss: `0.2960543632507324`
- heldout final total loss: `0.014106928370893002`
- heldout loss reduction vs baseline: `0.2819474348798394`
- heldout signed-Y MAE final: `0.023165112361311913`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.021809305995702744`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `8`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
