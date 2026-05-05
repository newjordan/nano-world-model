# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v012_action6_ten_task_v016_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `1014488ad8532cb9e6411397a7553388fa0cc020`
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
- train final total loss: `0.02315184287726879`
- train loss reduction vs baseline: `5.056387456133962`
- train signed-Y MAE final: `0.008138627745211124`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.09023137390613556`

## Heldout Metrics

- heldout baseline total loss: `0.2998008728027344`
- heldout final total loss: `0.03148259222507477`
- heldout loss reduction vs baseline: `0.2683182805776596`
- heldout signed-Y MAE final: `0.04510998725891113`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.021280985325574875`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `7`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
