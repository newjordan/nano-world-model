# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v014b_action6_time_phase_features_v016_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `f7561dadbe738ef194b84b6edf0be40104c7a590`
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
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.0795392990112305`
- train final total loss: `0.022922998294234276`
- train loss reduction vs baseline: `5.056616300716996`
- train signed-Y MAE final: `0.004472704604268074`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.09029892832040787`

## Heldout Metrics

- heldout baseline total loss: `0.2998008728027344`
- heldout final total loss: `0.030630581080913544`
- heldout loss reduction vs baseline: `0.26917029172182083`
- heldout signed-Y MAE final: `0.03931467607617378`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.021539704874157906`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `7`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
