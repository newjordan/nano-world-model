# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v023_translation_fallback`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v023_translation_fallback`
- run kind: `diagnostic_analysis_no_training`
- git commit: `5b4f137354ec3ec58156eb30e09272d20f87e31c`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_branch_library_v023_translation_fallback_v018_geometry_predictions/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION1|control_label:dominant_group:time_phase | 3 | 0.023844 | 0.023844 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.1119 | 56 | 0.161167 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0108481 | 0.0108481 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.0876674 | 495 | 0.0876674 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.00847347 | 0.00847347 | action:ACTION5|control_label:dominant_group:translation | 0.0738161 | 220 | 0.123507 |
| action:ACTION5|control_label:dominant_group:stasis_loop | 38 | 0.00760109 | 0.00760109 | action:ACTION5|control_label:dominant_group:stasis_loop | 0.0037148 | 117 | 0.0037148 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.00215648 | 8.86291e-05 | action:ACTION1|control_label:dominant_group:translation | 0.0668025 | 203 | 0.0833139 |
| action:ACTION1|control_label:stasis_no_change | 8 | 0.00101436 | 0.00101436 | action:ACTION1|control_label:stasis_no_change | 0.0598119 | 98 | 0.0598119 |
| action:ACTION2|control_label:stasis_no_change | 3 | 0.000920475 | 0.000920475 | action:ACTION1|control_label:stasis_no_change | 0.0842986 | 66 | 0.15312 |
| action:ACTION3|control_label:stasis_no_change | 4 | 0.000861749 | 0.000861749 | action:ACTION5|control_label:stasis_no_change | 0.0540199 | 169 | 0.0654366 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
