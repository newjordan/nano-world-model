# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v019b_transductive_branch_consistency_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v019b_transductive_branch_consistency_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `874c2f49bfbc290d370a2a40a67b7131019026a9`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v019b_transductive_branch_consistency_v016_holdout_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.217236 | -0.217236 | action:ACTION5|control_label:dominant_group:time_phase | 1.0009e-17 | 3 | 1.0009e-17 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.0867171 | -0.0686228 | action:ACTION5|control_label:dominant_group:translation | 0.0631576 | 98 | 0.0631576 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0639625 | -0.00505047 | action:ACTION1|control_label:dominant_group:time_phase | 0.034289 | 47 | 0.225496 |
| action:ACTION1|control_label:dominant_group:time_phase | 3 | 0.0497928 | -0.0129256 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.1119 | 56 | 0.161167 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.0477399 | 0.0193942 | action:ACTION6|control_label:dominant_group:translation | 0.0643453 | 16 | 0.0643453 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0378963 | -0.0191122 | action:ACTION1|control_label:dominant_group:translation | 0.0668025 | 203 | 0.0833139 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.026203 | 0.026203 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.0876674 | 495 | 0.0876674 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.02144 | 0.02144 | action:ACTION5|control_label:dominant_group:translation | 0.0738161 | 220 | 0.123507 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
