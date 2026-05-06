# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v015_action6_time_phase_signed_balance_v015_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `e74c8decdebe7d4e21166728ea6d5a3602e3c258`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
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
- ACTION6 time-phase signed balance: `True`
- ACTION6 time-phase train records: `484`
- ACTION6 time-phase signed weight: `14.148760330578513`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.375084400177002`
- train final total loss: `0.023923387750983238`
- train loss reduction vs baseline: `5.351161012426019`
- train signed-Y MAE final: `0.006558678112924099`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.08640331029891968`

## Heldout Metrics

- heldout baseline total loss: `0.4635099172592163`
- heldout final total loss: `0.032636336982250214`
- heldout loss reduction vs baseline: `0.4308735802769661`
- heldout signed-Y MAE final: `0.028554601594805717`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.019372232258319855`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `8`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
