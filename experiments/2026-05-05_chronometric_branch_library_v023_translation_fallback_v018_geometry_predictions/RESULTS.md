# Chronometric Branch Library Results

Status: posthoc branch-library inference for `chronometric_branch_library_v023_translation_fallback_v018_geometry_predictions`.

This is not a new training run and not training-data promotion. The library is built from train targets only.

## Condition

- run label: `chronometric_branch_library_v023_translation_fallback_v018_geometry_predictions`
- run kind: `branch_library_posthoc_inference`
- git commit: `c26418a871811b68337223f611d73c037079c265`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu/predictions.jsonl`
- blend: `1.0`
- min records: `1`
- library scope: `time_phase_translation`
- fallback scope: `dominant_translation_potential`
- fallback source field: `potential_family_vector.transition.changed_cells`
- library key strategy: `action_control_grid_coordinate_or_changed_cells`
- library entries: `120`
- adjusted records: `6072`
- fallback records: `15`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- train signed-Y MAE: `0.001232115453260555`
- heldout signed-Y MAE: `0.002145120054483414`
- heldout progress accuracy: `1.0`
- heldout adjusted records: `254`
- heldout fallback records: `15`
