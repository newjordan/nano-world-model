# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v007b_safe_potential_inputs`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v007b_safe_potential_inputs`
- run kind: `diagnostic_analysis_no_training`
- git commit: `cab2791fcf72b31ae3c44e87687508c289136ec5`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/predictions.jsonl`
- records: `2744`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION5|control_label:dominant_group:stasis_loop | 38 | 1.38013 | 1.38013 | action:ACTION4|control_label:dominant_group:translation | 0.0965639 | 3 | 0.132045 |
| action:ACTION6|control_label:dominant_group:time_phase | 1 | 1.25024 | -1.25024 | action:ACTION1|control_label:dominant_group:translation | 0.424821 |  |  |
| action:ACTION6|control_label:dominant_group:translation | 1 | 1.00024 | -1.00024 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.348161 |  |  |
| action:ACTION3|control_label:dominant_group:time_phase | 2 | 0.464747 | 0.464747 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.177389 | 60 | 0.243833 |
| action:ACTION2|control_label:dominant_group:time_phase | 2 | 0.264052 | 0.264052 | action:ACTION1|control_label:dominant_group:translation | 0.0818394 | 34 | 0.194819 |
| action:ACTION1|control_label:dominant_group:time_phase | 2 | 0.214629 | -0.214629 | action:ACTION1|control_label:dominant_group:translation | 0.0960812 | 25 | 0.239254 |
| action:ACTION4|control_label:dominant_group:translation | 76 | 0.128497 | 0.100376 | action:ACTION4|control_label:dominant_group:translation | 0.0720056 | 456 | 0.0720056 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.0962733 | 0.0962733 | action:ACTION1|control_label:dominant_group:translation | 0.250804 |  |  |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
