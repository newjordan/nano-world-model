# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v013_action6_support_v015_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v013_action6_support_v015_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `adbe5e54a65d7845a80ead064a1ae33e72e0a0ec`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v013_action6_support_v015_holdout_cpu/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.783472 | -0.783472 | action:ACTION6|control_label:dominant_group:time_phase | 0.12623 | 6 | 0.12623 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.18883 | -0.18883 | action:ACTION5|control_label:dominant_group:time_phase | 1.27848e-17 | 3 | 1.27848e-17 |
| action:ACTION6|control_label:dominant_group:translation | 12 | 0.151193 | -0.0804897 | action:ACTION6|control_label:dominant_group:translation | 0.0118266 | 21 | 0.0118266 |
| action:ACTION3|control_label:dominant_group:time_phase | 5 | 0.12085 | -0.0746261 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.107027 | 208 | 0.198391 |
| action:ACTION4|control_label:dominant_group:time_phase | 4 | 0.0501249 | 0.0501249 | action:ACTION5|control_label:dominant_group:time_phase | 0.0889971 | 219 | 0.23104 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0446588 | 0.0225326 | action:ACTION6|control_label:dominant_group:translation | 0.101996 | 495 | 0.110063 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0338239 | 0.0291338 | action:ACTION1|control_label:dominant_group:translation | 0.144382 | 47 | 0.27804 |
| action:ACTION2|control_label:dominant_group:translation | 61 | 0.028005 | 0.0173302 | action:ACTION1|control_label:dominant_group:translation | 0.0292296 | 610 | 0.0808047 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
