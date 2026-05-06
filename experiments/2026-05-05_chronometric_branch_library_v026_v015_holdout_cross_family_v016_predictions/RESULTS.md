# Chronometric Branch Library Results

Status: posthoc branch-library inference for `chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions`.

This is not a new training run and not training-data promotion. The library is built from train targets only.

## Condition

- run label: `chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions`
- run kind: `branch_library_posthoc_inference`
- git commit: `e69da9db0f0d4d6a1f9bc4dd3604665cf0d4c2f6`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu/predictions.jsonl`
- blend: `1.0`
- min records: `1`
- library scope: `time_phase_translation_stasis_loop`
- fallback scope: `time_phase_translation_potential`
- fallback source field: `potential_family_vector.time_phase.repeated_effect_size+transition.changed_cells;transition.changed_cells`
- library key strategy: `action_control_grid_coordinate_or_changed_cells`
- library entries: `550`
- adjusted records: `6770`
- fallback records: `23`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- train signed-Y MAE: `1.2584294833190051e-05`
- heldout signed-Y MAE: `9.222477674484252e-06`
- heldout progress accuracy: `1.0`
- heldout adjusted records: `339`
- heldout fallback records: `23`
