# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v008_temporal_loop_context_cross_family_holdout`
- run kind: `group_holdout_calibration_smoke`
- git commit: `5ba47a740df81ac564af4dc45f9f02160b9d88d9`
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
- train final total loss: `0.030321091413497925`
- train loss reduction vs baseline: `4.635603457689285`
- train signed-Y MAE final: `0.0029640840366482735`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.12107215076684952`

## Heldout Metrics

- heldout baseline total loss: `1.3680634498596191`
- heldout final total loss: `0.8733570575714111`
- heldout loss reduction vs baseline: `0.494706392288208`
- heldout signed-Y MAE final: `0.42049968242645264`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `1`
- heldout positive mean rank final: `1.0`
- heldout family MSE final: `0.34680381417274475`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `1`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
