# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v014_action6_time_phase_features_v015_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v014_action6_time_phase_features_v015_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `a610fecfba12a3a44615735e6cf6587364530b0f`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v014_action6_time_phase_features_v015_holdout_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.663465 | -0.663465 | action:ACTION6|control_label:dominant_group:time_phase | 0.11473 | 6 | 0.11473 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.171489 | -0.171489 | action:ACTION5|control_label:dominant_group:time_phase | 1.162e-17 | 3 | 1.162e-17 |
| action:ACTION3|control_label:dominant_group:time_phase | 5 | 0.102426 | -0.0766925 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.0972765 | 208 | 0.180316 |
| action:ACTION6|control_label:dominant_group:translation | 12 | 0.0859006 | -0.0384253 | action:ACTION6|control_label:dominant_group:translation | 0.0107493 | 21 | 0.0107493 |
| action:ACTION1|control_label:dominant_group:time_phase | 2 | 0.0308885 | -0.0308885 | action:ACTION1|control_label:dominant_group:time_phase | 0.0584861 | 57 | 0.0584861 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.022137 | 0.016595 | action:ACTION1|control_label:dominant_group:translation | 0.131228 | 47 | 0.252709 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0218231 | 0.0187626 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.100046 | 495 | 0.100046 |
| action:ACTION2|control_label:dominant_group:translation | 61 | 0.0154492 | 0.00440707 | action:ACTION1|control_label:dominant_group:translation | 0.0265665 | 610 | 0.0734429 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
