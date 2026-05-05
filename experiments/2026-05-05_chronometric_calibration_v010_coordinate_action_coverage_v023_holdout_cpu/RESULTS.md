# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `00985f285eaaa894fe67efd358f6f6c24425e3cf`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl`
- records: `3820`
- progress-positive records: `27`
- train records: `3420`
- heldout records: `400`
- train progress-positive records: `26`
- heldout progress-positive records: `1`
- eval scope: `group_holdout_by_source_condition_artifact`
- device: `cpu`
- seed: `20260505`
- steps: `800`
- negative-control weight: `0.0`
- negative-control margin: `-0.5`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.13267707824707`
- train final total loss: `0.025529200211167336`
- train loss reduction vs baseline: `5.107147878035903`
- train signed-Y MAE final: `0.00770241254940629`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.098454549908638`

## Heldout Metrics

- heldout baseline total loss: `1.8516876697540283`
- heldout final total loss: `0.012320181354880333`
- heldout loss reduction vs baseline: `1.839367488399148`
- heldout signed-Y MAE final: `0.015096906572580338`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.04127751663327217`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `5`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
