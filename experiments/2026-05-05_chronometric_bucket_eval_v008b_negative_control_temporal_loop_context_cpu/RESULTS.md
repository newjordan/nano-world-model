# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v008b_negative_control_temporal_loop_context_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v008b_negative_control_temporal_loop_context_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `94ea7db43d1f70e5e7266e9730a5c0c0a05b1fcd`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v008b_negative_control_temporal_loop_context_cpu_comparable/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v008b_negative_control_temporal_loop_context_cpu_comparable/metrics.json`
- records: `2744`
- splits: `{'heldout': 400, 'train': 2344}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `2344` positives=`25` signed_MAE=`0.00406673115525858` progress_acc=`1.0`
- heldout records: `400` positives=`1` signed_MAE=`0.4067221097235597` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 257 | 0 | 1 | 0.0616399 | 0.000303513 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.918486 | 7.64654e-07 |
| control_label:stasis_no_change | 50 | 0 | 1 | 1.48106 | 0.000228965 |
| control_label:dominant_group:time_phase | 16 | 0 | 1 | 0.186558 | 0.000461543 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.00431764 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 87 | 1 | 1 | 0.114722 | 0.000303513 |
| action:ACTION6 | 80 | 0 | 1 | 1.81562 | 0 |
| action:ACTION3 | 65 | 0 | 1 | 0.0696823 | 0.000137066 |
| action:ACTION2 | 61 | 0 | 1 | 0.0170351 | 4.10018e-05 |
| action:ACTION5 | 55 | 0 | 1 | 0.0216783 | 0.000461543 |
| action:ACTION1 | 52 | 0 | 1 | 0.0134216 | 0.000139106 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 193 | 0 | 1 | 0.39757 | 0.000461543 |
| movement:x_positive | 67 | 0 | 1 | 0.146399 | 5.34741e-05 |
| movement:none | 55 | 0 | 1 | 1.3466 | 0.000228965 |
| movement:y_positive | 43 | 0 | 1 | 0.0330495 | 0.000303513 |
| movement:y_negative | 42 | 1 | 1 | 0.0158323 | 7.72742e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.381085 | 0.000461543 |
| time:post_progress_step | 130 | 0 | 1 | 0.453065 | 0.000303513 |
| time:progress_step | 10 | 1 | 1 | 0.47084 | 2.34024e-05 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
