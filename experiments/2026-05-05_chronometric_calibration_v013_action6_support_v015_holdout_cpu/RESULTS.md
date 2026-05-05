# Chronometric Calibration Smoke Results

Status: grouped held-out smoke for a small chronometric calibration head.

This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion.

## Condition

- run label: `chronometric_calibration_v013_action6_support_v015_holdout_cpu`
- run kind: `group_holdout_calibration_smoke`
- git commit: `f066d1042bbd6bfb1edabf44371f74b154f9dcec`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- records: `7732`
- progress-positive records: `52`
- train records: `7332`
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

- train baseline total loss: `5.140894412994385`
- train final total loss: `0.02290751039981842`
- train loss reduction vs baseline: `5.117986902594566`
- train signed-Y MAE final: `0.014974744990468025`
- train progress accuracy final: `1.0`
- train positive best rank final: `1`
- train family MSE final: `0.08651918172836304`

## Heldout Metrics

- heldout baseline total loss: `0.28638404607772827`
- heldout final total loss: `0.012371068820357323`
- heldout loss reduction vs baseline: `0.27401297725737095`
- heldout signed-Y MAE final: `0.027918638661503792`
- heldout progress accuracy final: `1.0`
- heldout positive best rank final: `None`
- heldout positive mean rank final: `None`
- heldout family MSE final: `0.01962633803486824`

## Split

- key: `source_condition_artifact`
- holdout fraction: `0.0`
- train groups: `8`
- heldout groups: `1`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- heldout split is by group, not by random row, when heldout records are present
