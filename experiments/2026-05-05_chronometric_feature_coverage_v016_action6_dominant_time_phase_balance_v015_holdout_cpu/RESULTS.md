# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v016_action6_dominant_time_phase_balance_v015_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v016_action6_dominant_time_phase_balance_v015_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `e0d8f43fd266aa5988e907386a7b3f47a037a69a`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.263191 | -0.263191 | action:ACTION5|control_label:dominant_group:time_phase | 1.162e-17 | 3 | 1.162e-17 |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.22554 | -0.22554 | action:ACTION6|control_label:dominant_group:time_phase | 0.11473 | 6 | 0.11473 |
| action:ACTION6|control_label:dominant_group:translation | 12 | 0.107459 | -0.0589074 | action:ACTION6|control_label:dominant_group:translation | 0.0107493 | 21 | 0.0107493 |
| action:ACTION3|control_label:dominant_group:time_phase | 5 | 0.0831364 | -0.0774786 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.0972765 | 208 | 0.180316 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0803128 | 0.0803128 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.100046 | 495 | 0.100046 |
| action:ACTION4|control_label:dominant_group:time_phase | 4 | 0.0346865 | 0.0062648 | action:ACTION5|control_label:dominant_group:time_phase | 0.0808888 | 219 | 0.209991 |
| action:ACTION2|control_label:dominant_group:translation | 61 | 0.0185893 | -0.00612669 | action:ACTION1|control_label:dominant_group:translation | 0.0265665 | 610 | 0.0734429 |
| action:ACTION1|control_label:dominant_group:time_phase | 2 | 0.0167216 | -0.0167216 | action:ACTION1|control_label:dominant_group:time_phase | 0.0584861 | 57 | 0.0584861 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
