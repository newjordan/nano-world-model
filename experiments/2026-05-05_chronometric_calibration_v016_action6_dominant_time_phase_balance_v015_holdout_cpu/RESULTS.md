# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `92428b289e8bb93211671a2895dba798ac877d6c`
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
- ACTION6 time-phase train records: `6`
- ACTION6 time-phase signed weight: `256.0`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.138560771942139`
- train final total loss: `0.02382648177444935`
- train loss reduction vs baseline: `5.114734290167689`
- train signed-Y MAE final: `0.009662496857345104`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.08649385720491409`

## Heldout Metrics

- heldout baseline total loss: `0.24051879346370697`
- heldout final total loss: `0.04740152508020401`
- heldout loss reduction vs baseline: `0.19311726838350296`
- heldout signed-Y MAE final: `0.023143382743000984`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.01962619461119175`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `8`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
