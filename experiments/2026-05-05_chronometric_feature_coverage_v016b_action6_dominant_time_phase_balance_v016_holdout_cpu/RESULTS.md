# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `7f32ab793b9c024f94e4e78ca3eca1eea28400d3`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu/predictions.jsonl`
- records: `7332`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION6|control_label:dominant_group:time_phase | 2 | 0.633624 | -0.633624 | action:ACTION6|control_label:dominant_group:time_phase | 0.0808698 | 4 | 0.0808698 |
| action:ACTION6|control_label:dominant_group:translation | 17 | 0.513739 | -0.498322 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.153937 | 4 | 0.182742 |
| action:ACTION5|control_label:dominant_group:time_phase | 1 | 0.185797 | -0.185797 | action:ACTION5|control_label:dominant_group:time_phase | 0 | 2 | 0 |
| action:ACTION5|control_label:dominant_group:translation | 18 | 0.122399 | -0.11657 | action:ACTION5|control_label:dominant_group:translation | 0.07005 | 92 | 0.07005 |
| action:ACTION3|control_label:dominant_group:time_phase | 10 | 0.0533581 | -0.0533575 | action:ACTION1|control_label:dominant_group:translation | 0.0784181 | 198 | 0.0989534 |
| action:ACTION2|control_label:dominant_group:time_phase | 3 | 0.0479814 | -0.0408144 | action:ACTION1|control_label:dominant_group:time_phase | 0.0391863 | 44 | 0.268278 |
| action:ACTION6|control_label:dominant_group:stasis_loop | 38 | 0.0218091 | -0.00359838 | action:ACTION6|control_label:dominant_group:stasis_loop | 0.108365 | 457 | 0.108365 |
| action:ACTION4|control_label:dominant_group:time_phase | 3 | 0.0190446 | 0.0155004 | action:ACTION5|control_label:dominant_group:translation | 0.0902298 | 216 | 0.144501 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
