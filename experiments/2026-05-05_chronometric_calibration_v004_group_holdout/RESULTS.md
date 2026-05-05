# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v004_group_holdout`
- run kind: `group_holdout_calibration_smoke`
- git commit: `30eff83e755521b3d5cf0142853c66ed65248d9b`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch/arc_bridge_manifest.jsonl`
- records: `2344`
- progress-positive records: `25`
- train records: `1768`
- heldout records: `576`
- train progress-positive records: `19`
- heldout progress-positive records: `6`
- eval scope: `group_holdout_by_source_artifact_path`
- device: `cuda`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

## Metrics

- train baseline total loss: `4.668223857879639`
- train final total loss: `0.02654724381864071`
- train loss reduction vs baseline: `4.641676614060998`
- train signed-Y MAE final: `0.0928897112607956`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.0119260149076581`

## Heldout Metrics

- heldout baseline total loss: `4.4902191162109375`
- heldout final total loss: `0.03465180844068527`
- heldout loss reduction vs baseline: `4.455567307770252`
- heldout signed-Y MAE final: `0.09581122547388077`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `3.5`
- heldout family MSE final: `0.0146353580057621`

## Split

- key: `source_artifact_path`
- holdout fraction: `0.24`
- train groups: `19`
- heldout groups: `6`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
