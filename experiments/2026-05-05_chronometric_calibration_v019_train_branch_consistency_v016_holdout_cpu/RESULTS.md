# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v019_train_branch_consistency_v016_holdout_cpu`
- run kind: `group_holdout_calibration_smoke_with_train_branch_consistency`
- git commit: `aed97c8f2cd06d55654ead5f3d9f4921621295db`
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
- branch consistency enabled: `True`
- branch consistency weight: `1.0`
- branch consistency pairs: `3`
- branch consistency uses heldout features: `False`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.138065814971924`
- train final total loss: `0.022109542042016983`
- train loss reduction vs baseline: `5.115956272929907`
- train signed-Y MAE final: `0.006915335077792406`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.0865027904510498`

## Heldout Metrics

- heldout baseline total loss: `0.24570952355861664`
- heldout final total loss: `0.1835705190896988`
- heldout loss reduction vs baseline: `0.06213900446891785`
- heldout signed-Y MAE final: `0.02018224261701107`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.021275747567415237`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `8`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
