# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `531de6e96bcb422e5519b591d88bf5205094caeb`
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

- train baseline total loss: `4.805081367492676`
- train final total loss: `0.02705361135303974`
- train loss reduction vs baseline: `4.778027756139636`
- train signed-Y MAE final: `0.005236394237726927`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.10683633387088776`

## Heldout Metrics

- heldout baseline total loss: `6.745943069458008`
- heldout final total loss: `0.05827900767326355`
- heldout loss reduction vs baseline: `6.687664061784744`
- heldout signed-Y MAE final: `0.008341473527252674`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.22853663563728333`

## Split

- key: `source_artifact_path`
- holdout fraction: `0.0`
- train groups: `33`
- heldout groups: `2`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
