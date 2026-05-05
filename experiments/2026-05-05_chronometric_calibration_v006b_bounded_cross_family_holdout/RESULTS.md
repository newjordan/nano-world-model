# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v006b_bounded_cross_family_holdout`
- run kind: `group_holdout_calibration_smoke`
- git commit: `6e330fd6be7bbd3a2ed62389e77ad8733b784439`
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
- train final total loss: `0.05816077068448067`
- train loss reduction vs baseline: `4.6077637784183025`
- train signed-Y MAE final: `0.10258574783802032`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.12871207296848297`

## Heldout Metrics

- heldout baseline total loss: `1.3680634498596191`
- heldout final total loss: `1.0726784467697144`
- heldout loss reduction vs baseline: `0.2953850030899048`
- heldout signed-Y MAE final: `0.7257595658302307`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.34233084321022034`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `1`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
