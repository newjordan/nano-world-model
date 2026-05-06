# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v017_v015_support_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v017_v015_support_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `547083cdebe64c2a343c9fe8fe3e6468959fb4fa`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v017_v015_support_v016_holdout_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.659954 | -0.659954 | action:ACTION6|control_label:dominant_group:time_phase | 0.043888 | 6 | 0.043888 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.177574 | -0.177574 | action:ACTION5|control_label:dominant_group:time_phase | 1.162e-17 | 3 | 1.162e-17 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.118465 | -0.111342 | action:ACTION5|control_label:dominant_group:translation | 0.0700742 | 98 | 0.0700742 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.10095 | -0.0411231 | action:ACTION6|control_label:dominant_group:translation | 0.0733339 | 16 | 0.0733339 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.064303 | -0.0350522 | action:ACTION1|control_label:dominant_group:time_phase | 0.039428 | 47 | 0.261791 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0463156 | -0.00950278 | action:ACTION1|control_label:dominant_group:translation | 0.0775549 | 203 | 0.0961154 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.023415 | 0.0190903 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.100046 | 495 | 0.100046 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.0167587 | 0.00705612 | action:ACTION5|control_label:dominant_group:translation | 0.0856826 | 220 | 0.143361 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
