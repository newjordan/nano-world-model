# Chronometric Branch Library Results

Status: posthoc branch-library inference for `chronometric_branch_library_v025_stasis_loop_scope_v018_geometry_predictions`.

This is not a new training run and not training-data promotion. The library is built from train targets only.

## Condition

- run label: `chronometric_branch_library_v025_stasis_loop_scope_v018_geometry_predictions`
- run kind: `branch_library_posthoc_inference`
- git commit: `bcfd99c4d67dfac01ecb75a0acaccd88d22059d3`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu/predictions.jsonl`
- blend: `1.0`
- min records: `1`
- library scope: `time_phase_translation_stasis_loop`
- fallback scope: `time_phase_translation_potential`
- fallback source field: `potential_family_vector.time_phase.repeated_effect_size+transition.changed_cells;transition.changed_cells`
- library key strategy: `action_control_grid_coordinate_or_changed_cells`
- library entries: `548`
- adjusted records: `6770`
- fallback records: `20`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- train signed-Y MAE: `5.528278774858757e-05`
- heldout signed-Y MAE: `9.615391492843628e-05`
- heldout progress accuracy: `1.0`
- heldout adjusted records: `335`
- heldout fallback records: `20`
