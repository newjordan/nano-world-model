# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `0adfc2f54a6f575d7b6ea094c3dc6301ebf75df6`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- records: `7332`
- progress-positive records: `52`
- train records: `6932`
- heldout records: `400`
- train progress-positive records: `52`
- heldout progress-positive records: `0`
- eval scope: `group_holdout_by_source_condition_artifact`
- device: `cpu`
- seed: `20260505`
- steps: `800`
- negative-control weight: `0.0`
- negative-control margin: `-0.5`
- ACTION6 time-phase signed balance: `True`
- ACTION6 time-phase train records: `4`
- ACTION6 time-phase signed weight: `256.0`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.077504634857178`
- train final total loss: `0.023139294236898422`
- train loss reduction vs baseline: `5.054365340620279`
- train signed-Y MAE final: `0.005090498365461826`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.0902184471487999`

## Heldout Metrics

- heldout baseline total loss: `0.24400755763053894`
- heldout final total loss: `0.40745875239372253`
- heldout loss reduction vs baseline: `-0.1634511947631836`
- heldout signed-Y MAE final: `0.04113982990384102`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.021772723644971848`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `7`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
