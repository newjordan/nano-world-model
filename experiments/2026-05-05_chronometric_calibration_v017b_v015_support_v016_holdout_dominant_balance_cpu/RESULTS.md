# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v017b_v015_support_v016_holdout_dominant_balance_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `940c6698c93c018deb30f6e9019b1d1d2bf7c16a`
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
- ACTION6 time-phase signed balance: `True`
- ACTION6 time-phase train records: `6`
- ACTION6 time-phase signed weight: `256.0`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.138065814971924`
- train final total loss: `0.02279747650027275`
- train loss reduction vs baseline: `5.115268338471651`
- train signed-Y MAE final: `0.007228070870041847`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.08642512559890747`

## Heldout Metrics

- heldout baseline total loss: `0.24570952355861664`
- heldout final total loss: `0.2230938822031021`
- heldout loss reduction vs baseline: `0.022615641355514526`
- heldout signed-Y MAE final: `0.034029360860586166`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.021659748628735542`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `8`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
