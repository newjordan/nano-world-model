# Chronometric Calibration Smoke Results

Status: supervised fit smoke for a small chronometric calibration head.

This is not a held-out quality claim. It verifies that bridge rows can drive a learned calibration objective without manual scorer knob changes.

## Condition

- run label: `chronometric_calibration_smoke`
- run kind: `fit_smoke_no_generalization_claim`
- git commit: `9400860ab458fab16b255cebb6793ca1dbf5abcf`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_smoke/arc_bridge_manifest.jsonl`
- records: `40`
- progress-positive records: `1`
- device: `cuda`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

## Metrics

- baseline total loss: `3.833247661590576`
- final total loss: `5.0400052714394405e-05`
- loss reduction vs baseline: `3.8331972615378618`
- signed-Y MAE final: `0.000916401797439903`
- progress accuracy final: `1.0`
- positive progress rank final: `1`
- family MSE final: `8.45704780658707e-05`

## Integrity

- inputs exclude direct outcome labels and post-outcome fields
- all records preserve quarantine/control provenance
- eval scope is train-fit only; more bridge rows are required before held-out claims
