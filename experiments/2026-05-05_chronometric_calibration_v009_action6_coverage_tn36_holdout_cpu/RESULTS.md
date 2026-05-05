# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `14365e87c0d3911a5eb5bafe4ad30b62fd6b7d79`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- records: `2744`
- progress-positive records: `26`
- train records: `2664`
- heldout records: `80`
- train progress-positive records: `25`
- heldout progress-positive records: `1`
- eval scope: `group_holdout_by_source_artifact_path`
- device: `cpu`
- seed: `20260505`
- steps: `800`
- negative-control weight: `0.0`
- negative-control margin: `-0.5`
- training data promoted: `False`

## Metrics

- train baseline total loss: `4.807387351989746`
- train final total loss: `0.027941321954131126`
- train loss reduction vs baseline: `4.779446030035615`
- train signed-Y MAE final: `0.006062301341444254`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.11051256954669952`

## Heldout Metrics

- heldout baseline total loss: `6.6675310134887695`
- heldout final total loss: `0.08591418713331223`
- heldout loss reduction vs baseline: `6.581616826355457`
- heldout signed-Y MAE final: `0.04159923642873764`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.19904227554798126`

## Split

- key: `source_artifact_path`
- holdout fraction: `0.0`
- train groups: `33`
- heldout groups: `2`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
