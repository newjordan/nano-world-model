# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v008b_negative_control_temporal_loop_context`
- run kind: `group_holdout_calibration_smoke`
- git commit: `86b08d18840e44ced6ef84066670bd4e84376f6c`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- records: `2744`
- progress-positive records: `26`
- train records: `2344`
- heldout records: `400`
- train progress-positive records: `25`
- heldout progress-positive records: `1`
- eval scope: `group_holdout_by_source_condition_artifact`
- device: `cuda`
- seed: `20260505`
- steps: `800`
- negative-control weight: `1.0`
- negative-control margin: `-0.5`
- training data promoted: `False`

## Metrics

- train baseline total loss: `4.855111122131348`
- train final total loss: `0.03032567724585533`
- train loss reduction vs baseline: `4.824785444885492`
- train signed-Y MAE final: `0.002371200593188405`
- train progress accuracy final: `0.9999999403953552`
- train positive best rank final: `1`
- train family MSE final: `0.12111796438694`

## Heldout Metrics

- heldout baseline total loss: `1.557251214981079`
- heldout final total loss: `2.046684503555298`
- heldout loss reduction vs baseline: `-0.48943328857421875`
- heldout signed-Y MAE final: `0.39658233523368835`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.323729008436203`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `1`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
