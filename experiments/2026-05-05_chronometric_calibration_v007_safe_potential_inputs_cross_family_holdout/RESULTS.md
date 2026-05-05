# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout`
- run kind: `group_holdout_calibration_smoke`
- git commit: `1a816115a8f22a588a6f063a8a5e388eac4121d3`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- records: `2744`
- progress-positive records: `26`
- train records: `2344`
- heldout records: `400`
- train progress-positive records: `25`
- heldout progress-positive records: `1`
- eval scope: `group_holdout_by_source_condition_artifact`
- device: `cpu`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

## Metrics

- train baseline total loss: `4.665924549102783`
- train final total loss: `0.03280029445886612`
- train loss reduction vs baseline: `4.633124254643917`
- train signed-Y MAE final: `0.011312737129628658`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.12102263420820236`

## Heldout Metrics

- heldout baseline total loss: `1.3680634498596191`
- heldout final total loss: `0.26092466711997986`
- heldout loss reduction vs baseline: `1.1071387827396393`
- heldout signed-Y MAE final: `0.18368175625801086`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.22625145316123962`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `1`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
