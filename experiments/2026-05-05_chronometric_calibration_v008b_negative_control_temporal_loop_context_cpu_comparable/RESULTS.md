# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v008b_negative_control_temporal_loop_context_cpu_comparable`
- run kind: `group_holdout_calibration_smoke`
- git commit: `7518801342f13393812fbc66c023e1f4c4c68330`
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
- negative-control weight: `1.0`
- negative-control margin: `-0.5`
- training data promoted: `False`

## Metrics

- train baseline total loss: `4.855112075805664`
- train final total loss: `0.03034052811563015`
- train loss reduction vs baseline: `4.824771547690034`
- train signed-Y MAE final: `0.004066730849444866`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.12112537771463394`

## Heldout Metrics

- heldout baseline total loss: `1.557251214981079`
- heldout final total loss: `2.1029090881347656`
- heldout loss reduction vs baseline: `-0.5456578731536865`
- heldout signed-Y MAE final: `0.4067220985889435`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.32695406675338745`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `1`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
