# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v017b_v015_support_v016_holdout_dominant_balance_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v017b_v015_support_v016_holdout_dominant_balance_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `eb700962f641525980061cf6c51a48a10d417171`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v017b_v015_support_v016_holdout_dominant_balance_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.465186 | -0.465186 | action:ACTION6|control_label:dominant_group:time_phase | 0.043888 | 6 | 0.043888 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.231957 | -0.231957 | action:ACTION5|control_label:dominant_group:time_phase | 1.162e-17 | 3 | 1.162e-17 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.202376 | -0.124666 | action:ACTION6|control_label:dominant_group:translation | 0.0733339 | 16 | 0.0733339 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.138969 | -0.129737 | action:ACTION5|control_label:dominant_group:translation | 0.0700742 | 98 | 0.0700742 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0717656 | 0.0717656 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.100046 | 495 | 0.100046 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0419481 | -0.0415552 | action:ACTION1|control_label:dominant_group:time_phase | 0.039428 | 47 | 0.261791 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0398745 | -0.0229242 | action:ACTION1|control_label:dominant_group:translation | 0.0775549 | 203 | 0.0961154 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.0250947 | 0.0210204 | action:ACTION5|control_label:dominant_group:translation | 0.0856826 | 220 | 0.143361 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
