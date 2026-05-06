# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v019_train_branch_consistency_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v019_train_branch_consistency_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `be766ec3eac2f6bb42a2cd7b64086e57f0777ba0`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v019_train_branch_consistency_v016_holdout_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.430918 | -0.430918 | action:ACTION6|control_label:dominant_group:time_phase | 0.048656 | 6 | 0.048656 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.221456 | -0.221456 | action:ACTION5|control_label:dominant_group:time_phase | 1.0009e-17 | 3 | 1.0009e-17 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.0996509 | -0.00316294 | action:ACTION6|control_label:dominant_group:translation | 0.0643453 | 16 | 0.0643453 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.0836921 | -0.0657058 | action:ACTION5|control_label:dominant_group:translation | 0.0631576 | 98 | 0.0631576 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0661581 | -0.0105749 | action:ACTION1|control_label:dominant_group:time_phase | 0.034289 | 47 | 0.225496 |
| action:ACTION1|control_label:dominant_group:time_phase | 3 | 0.0552368 | -0.0075488 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.1119 | 56 | 0.161167 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0329951 | -0.0240862 | action:ACTION1|control_label:dominant_group:translation | 0.0668025 | 203 | 0.0833139 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.0220075 | 0.0220075 | action:ACTION5|control_label:dominant_group:translation | 0.0738161 | 220 | 0.123507 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
