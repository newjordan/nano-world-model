# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v009_action6_coverage_tn36_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v009_action6_coverage_tn36_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `d82c1834f510cefc49eebe2506451fb064eda314`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/predictions.jsonl`
- records: `2744`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 1 | 1.25013 | -1.25013 | action:ACTION5|control_label:dominant_group:time_phase | 0.317883 |  |  |
| action:ACTION6|control_label:dominant_group:translation | 1 | 0.999479 | -0.999479 | action:ACTION2|control_label:dominant_group:time_phase | 0.335341 |  |  |
| action:ACTION4|control_label:dominant_group:translation | 14 | 0.0300284 | -0.0258547 | action:ACTION4|control_label:dominant_group:translation | 0.0490668 | 518 | 0.0490668 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0143605 | -0.0119456 | action:ACTION5|control_label:dominant_group:translation | 0.307636 |  |  |
| action:ACTION1|control_label:dominant_group:time_phase | 1 | 0.00781205 | -0.00781205 | action:ACTION1|control_label:dominant_group:time_phase | 0.0174086 | 26 | 0.0174086 |
| action:ACTION4|control_label:dominant_group:goal_progress | 1 | 0.00735569 | -0.00735569 | action:ACTION4|control_label:dominant_group:goal_progress | 2.54703e-17 | 25 | 2.54703e-17 |
| action:ACTION1|control_label:dominant_group:translation | 10 | 0.00536893 | -0.00455477 | action:ACTION1|control_label:dominant_group:translation | 0.0326159 | 316 | 0.0326159 |
| action:ACTION3|control_label:dominant_group:translation | 10 | 0.00401283 | -0.00401283 | action:ACTION1|control_label:dominant_group:translation | 0.04961 | 814 | 0.0743724 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
