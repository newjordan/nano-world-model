# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v009_action6_coverage_ft09_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v009_action6_coverage_ft09_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `865259cd32900d3baca4313619de73b7b5c31ee6`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/predictions.jsonl`
- records: `2744`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION4|control_label:dominant_group:translation | 14 | 0.0294623 | -0.0222563 | action:ACTION4|control_label:dominant_group:translation | 0.0490668 | 518 | 0.0490668 |
| action:ACTION4|control_label:dominant_group:goal_progress | 1 | 0.00753534 | -0.00753534 | action:ACTION4|control_label:dominant_group:goal_progress | 2.54703e-17 | 25 | 2.54703e-17 |
| action:ACTION6|control_label:stasis_no_change | 40 | 0.00453176 | 0.00453176 | action:ACTION5|control_label:stasis_no_change | 0.311281 |  |  |
| action:ACTION1|control_label:dominant_group:translation | 10 | 0.00377669 | 0.00207729 | action:ACTION1|control_label:dominant_group:translation | 0.0326159 | 316 | 0.0326159 |
| action:ACTION3|control_label:dominant_group:translation | 10 | 0.00265037 | 0.00223478 | action:ACTION1|control_label:dominant_group:translation | 0.04961 | 814 | 0.0743724 |
| action:ACTION1|control_label:dominant_group:time_phase | 1 | 0.00057596 | 0.00057596 | action:ACTION1|control_label:dominant_group:time_phase | 0.0174086 | 26 | 0.0174086 |
| action:ACTION1|control_label:stasis_no_change | 1 | 0.00035435 | 0.00035435 | action:ACTION1|control_label:stasis_no_change | 0.09653 | 41 | 0.09653 |
| action:ACTION4|control_label:stasis_no_change | 2 | 0.000305742 | 0.000305742 | action:ACTION4|control_label:stasis_no_change | 0 | 2 | 0 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
