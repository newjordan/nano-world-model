# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `83b85b2897edba1ecfcfd0c138925ea50ddc0bea`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/arc_bridge_manifest.jsonl`
- records: `6932`
- progress-positive records: `52`
- train records: `3820`
- heldout records: `3112`
- train progress-positive records: `27`
- heldout progress-positive records: `25`
- eval scope: `group_holdout_by_source_condition_artifact`
- device: `cpu`
- seed: `20260505`
- steps: `800`
- negative-control weight: `0.0`
- negative-control margin: `-0.5`
- training data promoted: `False`

## Metrics

- train baseline total loss: `5.203835487365723`
- train final total loss: `0.023878341540694237`
- train loss reduction vs baseline: `5.179957145825028`
- train signed-Y MAE final: `0.00914730690419674`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.09246167540550232`

## Heldout Metrics

- heldout baseline total loss: `5.7693705558776855`
- heldout final total loss: `0.02222723700106144`
- heldout loss reduction vs baseline: `5.747143318876624`
- heldout signed-Y MAE final: `0.01057388260960579`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `13.0`
- heldout family MSE final: `0.087530218064785`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `6`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
