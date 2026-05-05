# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v011_nonlocal_second_family_v033_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v011_nonlocal_second_family_v033_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `a23190e09743297d3be4558fa1d3c4e8148c1d3b`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu/predictions.jsonl`
- records: `6932`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION4|control_label:dominant_group:time_phase | 154 | 0.0431167 | -0.0209972 | action:ACTION4|control_label:dominant_group:time_phase | 0.0691907 | 62 | 0.0691907 |
| action:ACTION3|control_label:dominant_group:time_phase | 134 | 0.0257188 | -0.00198501 | action:ACTION3|control_label:dominant_group:time_phase | 0.0400344 | 64 | 0.0400344 |
| action:ACTION2|control_label:dominant_group:translation | 60 | 0.0162702 | 0.0162702 | action:ACTION2|control_label:dominant_group:translation | 0.147134 | 487 | 0.147134 |
| action:ACTION5|control_label:dominant_group:translation | 32 | 0.0157365 | 0.00925269 | action:ACTION4|control_label:dominant_group:translation | 0.0252681 | 60 | 0.0515287 |
| action:ACTION4|control_label:dominant_group:translation | 1132 | 0.00882666 | 0.00358526 | action:ACTION3|control_label:dominant_group:translation | 0.0552084 | 608 | 0.0664068 |
| action:ACTION3|control_label:dominant_group:translation | 1124 | 0.00793823 | 0.0065321 | action:ACTION2|control_label:dominant_group:translation | 0.0410792 | 885 | 0.0520486 |
| action:ACTION1|control_label:dominant_group:translation | 270 | 0.00765681 | 0.00765681 | action:ACTION1|control_label:dominant_group:translation | 0.0113723 | 375 | 0.0113723 |
| action:ACTION1|control_label:dominant_group:time_phase | 25 | 0.00466439 | 0.00466439 | action:ACTION1|control_label:dominant_group:time_phase | 0.0312154 | 29 | 0.0312154 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
