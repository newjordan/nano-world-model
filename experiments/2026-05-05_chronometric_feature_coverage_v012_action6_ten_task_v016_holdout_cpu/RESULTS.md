# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v012_action6_ten_task_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v012_action6_ten_task_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `2c2c3c513726ee50d66935b6cb1e70ce93f3267f`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v012_action6_ten_task_v016_holdout_cpu/predictions.jsonl`
- records: `7332`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.757464 | -0.757464 | action:ACTION6|control_label:dominant_group:time_phase | 0.0889746 | 4 | 0.0889746 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.513397 | -0.477616 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.139627 | 4 | 0.201059 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.154609 | -0.154609 | action:ACTION5|control_label:dominant_group:time_phase | 0 | 2 | 0 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.114932 | -0.076177 | action:ACTION5|control_label:dominant_group:translation | 0.0770718 | 92 | 0.0770718 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0892192 | -0.0701533 | action:ACTION1|control_label:dominant_group:time_phase | 0.0431143 | 44 | 0.29517 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0605307 | -0.0490795 | action:ACTION1|control_label:dominant_group:translation | 0.0862786 | 198 | 0.108872 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.0545148 | 0.0545148 | action:ACTION5|control_label:dominant_group:translation | 0.0992743 | 216 | 0.158985 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0302067 | 0.0130362 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.119214 | 457 | 0.119214 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
