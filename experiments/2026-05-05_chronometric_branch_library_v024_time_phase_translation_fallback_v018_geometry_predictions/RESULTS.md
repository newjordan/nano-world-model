# Chronometric Branch Library Results

Status: posthoc branch-library inference for `chronometric_branch_library_v024_time_phase_translation_fallback_v018_geometry_predictions`.

This is not a new training run and not training-data promotion. The library is built from train targets only.

## Condition

- run label: `chronometric_branch_library_v024_time_phase_translation_fallback_v018_geometry_predictions`
- run kind: `branch_library_posthoc_inference`
- git commit: `3a510db36abeea5088954c6dfebebc4df0aa8fb8`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu/predictions.jsonl`
- blend: `1.0`
- min records: `1`
- library scope: `time_phase_translation`
- fallback scope: `time_phase_translation_potential`
- fallback source field: `potential_family_vector.time_phase.repeated_effect_size+transition.changed_cells;transition.changed_cells`
- library key strategy: `action_control_grid_coordinate_or_changed_cells`
- library entries: `120`
- adjusted records: `6077`
- fallback records: `20`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- train signed-Y MAE: `0.001232115453260555`
- heldout signed-Y MAE: `0.0018488270044326781`
- heldout progress accuracy: `1.0`
- heldout adjusted records: `259`
- heldout fallback records: `20`
