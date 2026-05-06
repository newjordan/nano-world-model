# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v014b_action6_time_phase_features_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v014b_action6_time_phase_features_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `da46b8f54119c05c20d51b0dd5fd3c7a55424ac2`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v014b_action6_time_phase_features_v016_holdout_cpu/predictions.jsonl`
- records: `7332`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.684408 | -0.684408 | action:ACTION6|control_label:dominant_group:time_phase | 0.0808698 | 4 | 0.0808698 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.506764 | -0.458941 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.153937 | 4 | 0.182742 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.152733 | -0.152733 | action:ACTION5|control_label:dominant_group:time_phase | 0 | 2 | 0 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.0974841 | -0.0851379 | action:ACTION5|control_label:dominant_group:translation | 0.07005 | 92 | 0.07005 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0645307 | -0.057308 | action:ACTION1|control_label:dominant_group:time_phase | 0.0391863 | 44 | 0.268278 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0428149 | -0.0296497 | action:ACTION1|control_label:dominant_group:translation | 0.0784181 | 198 | 0.0989534 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.0224851 | 0.0224851 | action:ACTION5|control_label:dominant_group:translation | 0.0902298 | 216 | 0.144501 |
| action:ACTION1|control_label:dominant_group:time_phase | 3 | 0.0222661 | -0.0222661 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.129905 | 54 | 0.188759 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
