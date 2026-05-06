# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `c31024f38a2bf424b9bd73642c3512513bb0c2f4`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu/metrics.json`
- records: `7332`
- splits: `{'heldout': 400, 'train': 6932}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `6932` positives=`52` signed_MAE=`0.005090498779847135` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.041139831532927926` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0.0544693 | 0.0768462 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0165893 | 0.00338943 |
| control_label:stasis_no_change | 65 | 0 | 1 | 0.000684462 | 0.000216266 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.101884 | 0.00220571 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.10524 | 0.0768462 |
| action:ACTION2 | 69 | 0 | 1 | 0.0120559 | 2.91904e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.00657089 | 7.1203e-05 |
| action:ACTION3 | 58 | 0 | 1 | 0.0140397 | 0.000182038 |
| action:ACTION5 | 58 | 0 | 1 | 0.0486609 | 0.000126609 |
| action:ACTION1 | 51 | 0 | 1 | 0.0146446 | 6.78197e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.0244428 | 0.0277721 |
| movement:none | 75 | 0 | 1 | 0.00118593 | 0.000216266 |
| movement:y_positive | 67 | 0 | 1 | 0.153056 | 0.0768462 |
| movement:x_positive | 49 | 0 | 1 | 0.00569447 | 3.57812e-05 |
| movement:y_negative | 28 | 0 | 1 | 0.0503234 | 0.0282854 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0399046 | 0.0713912 |
| time:post_progress_step | 130 | 0 | 1 | 0.0457452 | 0.0733318 |
| time:progress_step | 10 | 0 | 1 | 0.0133848 | 0.0768462 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
