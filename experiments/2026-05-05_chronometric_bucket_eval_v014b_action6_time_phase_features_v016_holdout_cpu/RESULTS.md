# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v014b_action6_time_phase_features_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v014b_action6_time_phase_features_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `3a6a1514c445aec190943d5828680227cf942e6c`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v014b_action6_time_phase_features_v016_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v014b_action6_time_phase_features_v016_holdout_cpu/metrics.json`
- records: `7332`
- splits: `{'heldout': 400, 'train': 6932}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `6932` positives=`52` signed_MAE=`0.004472704571801265` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.0393146797328518` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0.0522871 | 0.0296149 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0135322 | 0.000666292 |
| control_label:stasis_no_change | 65 | 0 | 1 | 0.000428428 | 7.43036e-05 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.103525 | 0.00063073 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.104114 | 0.0296149 |
| action:ACTION2 | 69 | 0 | 1 | 0.0115285 | 4.97383e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.00782317 | 9.18056e-05 |
| action:ACTION3 | 58 | 0 | 1 | 0.0120965 | 0.000204023 |
| action:ACTION5 | 58 | 0 | 1 | 0.0379641 | 0.000207424 |
| action:ACTION1 | 51 | 0 | 1 | 0.0161948 | 8.76244e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.0228037 | 0.00947775 |
| movement:none | 75 | 0 | 1 | 0.000940129 | 0.000204023 |
| movement:y_positive | 67 | 0 | 1 | 0.148637 | 0.0296149 |
| movement:x_positive | 49 | 0 | 1 | 0.00905601 | 4.40062e-05 |
| movement:y_negative | 28 | 0 | 1 | 0.0401961 | 0.00890406 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0372393 | 0.0296149 |
| time:post_progress_step | 130 | 0 | 1 | 0.0459468 | 0.0214058 |
| time:progress_step | 10 | 0 | 1 | 0.00705651 | 0.0263549 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
