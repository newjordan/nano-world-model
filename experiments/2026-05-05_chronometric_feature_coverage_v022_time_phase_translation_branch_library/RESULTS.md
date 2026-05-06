# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v022_time_phase_translation_branch_library`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v022_time_phase_translation_branch_library`
- run kind: `diagnostic_analysis_no_training`
- git commit: `798833a600faedd7a093253a2902d75c207ecaf8`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_branch_library_v022_time_phase_translation_v018_geometry_predictions/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.0751201 | -0.073397 | action:ACTION5|control_label:dominant_group:translation | 0.0631576 | 98 | 0.0631576 |
| action:ACTION1|control_label:dominant_group:time_phase | 3 | 0.023844 | 0.023844 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.1119 | 56 | 0.161167 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0108481 | 0.0108481 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.0876674 | 495 | 0.0876674 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.00847347 | 0.00847347 | action:ACTION5|control_label:dominant_group:translation | 0.0738161 | 220 | 0.123507 |
| action:ACTION5|control_label:dominant_group:stasis_loop | 38 | 0.00760109 | 0.00760109 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.0037148 | 117 | 0.0037148 |
| action:ACTION3|control_label:dominant_group:translation | 44 | 0.00283382 | -0.00283382 | action:ACTION1|control_label:dominant_group:translation | 0.0535643 | 2063 | 0.088541 |
| action:ACTION4|control_label:dominant_group:translation | 55 | 0.00262582 | -0.00254481 | action:ACTION5|control_label:dominant_group:translation | 0.0495716 | 1800 | 0.0734492 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.00215648 | 8.86291e-05 | action:ACTION1|control_label:dominant_group:translation | 0.0668025 | 203 | 0.0833139 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
