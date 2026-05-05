# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v010_coordinate_action_coverage_v023_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v010_coordinate_action_coverage_v023_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `18c462e1c1670047572e9255d017b9f66eab2ee9`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/predictions.jsonl`
- records: `3820`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 1 | 0.58105 | -0.58105 | action:ACTION6|control_label:dominant_group:time_phase | 0.0973546 | 3 | 0.0973546 |
| action:ACTION6|control_label:dominant_group:translation | 1 | 0.158241 | -0.158241 | action:ACTION6|control_label:dominant_group:translation | 0.0332557 | 3 | 0.0332557 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.127664 | -0.127664 | action:ACTION5|control_label:dominant_group:time_phase | 0 | 1 | 0 |
| action:ACTION4|control_label:dominant_group:time_phase | 8 | 0.0723466 | 0.0220757 | action:ACTION4|control_label:dominant_group:translation | 0.0797759 | 54 | 0.097152 |
| action:ACTION1|control_label:dominant_group:time_phase | 2 | 0.0391689 | -0.0362964 | action:ACTION1|control_label:dominant_group:translation | 0.0888617 | 27 | 0.209548 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0295999 | 0.0120067 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.130026 | 419 | 0.130026 |
| action:ACTION5|control_label:dominant_group:translation | 16 | 0.0206738 | 0.00738145 | action:ACTION5|control_label:dominant_group:translation | 0.0643969 | 44 | 0.0643969 |
| action:ACTION3|control_label:dominant_group:time_phase | 2 | 0.0203953 | 0.0111384 | action:ACTION2|control_label:dominant_group:time_phase | 0.201924 | 62 | 0.223202 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
