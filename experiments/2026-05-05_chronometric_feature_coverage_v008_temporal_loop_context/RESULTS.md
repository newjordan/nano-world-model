# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v008_temporal_loop_context`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v008_temporal_loop_context`
- run kind: `diagnostic_analysis_no_training`
- git commit: `e8cf7fb02294ecd976bba7866cae0d4398afd9c3`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v008_temporal_loop_context_cross_family_holdout/predictions.jsonl`
- records: `2744`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:stasis_no_change | 40 | 2 | 2 | action:ACTION5|control_label:stasis_no_change | 0.347542 |  |  |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 1.98684 | 1.98684 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.348438 |  |  |
| action:ACTION6|control_label:dominant_group:translation | 1 | 0.999756 | 0.999756 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.330668 |  |  |
| action:ACTION6|control_label:dominant_group:time_phase | 1 | 0.749756 | 0.749756 | action:ACTION1|control_label:dominant_group:translation | 0.401921 |  |  |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.264614 | -0.264614 | action:ACTION1|control_label:dominant_group:translation | 0.237374 |  |  |
| action:ACTION4|control_label:dominant_group:time_phase | 8 | 0.14507 | -0.132504 | action:ACTION4|control_label:dominant_group:translation | 0.0868015 | 46 | 0.114048 |
| action:ACTION4|control_label:dominant_group:translation | 76 | 0.0619211 | -0.059296 | action:ACTION4|control_label:dominant_group:translation | 0.0681112 | 456 | 0.0681112 |
| action:ACTION3|control_label:dominant_group:time_phase | 2 | 0.0484925 | 0.0409067 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.170408 | 60 | 0.230643 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
