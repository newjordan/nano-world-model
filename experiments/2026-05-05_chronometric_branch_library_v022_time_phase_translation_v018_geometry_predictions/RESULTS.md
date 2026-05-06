# Chronometric Branch Library Results

Status: posthoc branch-library inference for `chronometric_branch_library_v022_time_phase_translation_v018_geometry_predictions`.

This is not a new training run and not training-data promotion. The library is built from train targets only.

## Condition

- run label: `chronometric_branch_library_v022_time_phase_translation_v018_geometry_predictions`
- run kind: `branch_library_posthoc_inference`
- git commit: `b4ddf5cfe1b864f06c673f3f2eab8260bbac7ca8`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu/predictions.jsonl`
- blend: `1.0`
- min records: `1`
- library scope: `time_phase_translation`
- library key strategy: `action_control_grid_coordinate_or_changed_cells`
- library entries: `120`
- adjusted records: `6057`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- train signed-Y MAE: `0.001232115453260555`
- heldout signed-Y MAE: `0.006403598150645848`
- heldout progress accuracy: `1.0`
- heldout adjusted records: `239`
