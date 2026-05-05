# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v006b_bounded_cross_family`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v006b_bounded_cross_family`
- run kind: `diagnostic_analysis_no_training`
- git commit: `a3aeb76b6c689fe709b504e2327c36d0706642d9`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v006b_bounded_cross_family_holdout/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v006b_bounded_cross_family_holdout/metrics.json`
- records: `2744`
- splits: `{'heldout': 400, 'train': 2344}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `2344` positives=`25` signed_MAE=`0.10258575521867226` progress_acc=`1.0`
- heldout records: `400` positives=`1` signed_MAE=`0.7257595679702353` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 257 | 0 | 1 | 0.419755 | 8.97835e-05 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 1.47032 | 1.00718e-07 |
| control_label:stasis_no_change | 50 | 0 | 1 | 1.30052 | 4.07274e-07 |
| control_label:dominant_group:time_phase | 16 | 0 | 1 | 0.352705 | 7.37401e-05 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.0134503 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 87 | 1 | 1 | 0.341925 | 1.31742e-05 |
| action:ACTION6 | 80 | 0 | 1 | 1.50313 | 0 |
| action:ACTION3 | 65 | 0 | 1 | 0.531869 | 7.22366e-05 |
| action:ACTION2 | 61 | 0 | 1 | 0.431351 | 9.32326e-07 |
| action:ACTION5 | 55 | 0 | 1 | 1.05587 | 1.00718e-07 |
| action:ACTION1 | 52 | 0 | 1 | 0.410562 | 8.97835e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 193 | 0 | 1 | 0.90084 | 5.88684e-06 |
| movement:x_positive | 67 | 0 | 1 | 0.356797 | 4.04112e-06 |
| movement:none | 55 | 0 | 1 | 1.19051 | 1.33606e-05 |
| movement:y_positive | 43 | 0 | 1 | 0.321957 | 7.22366e-05 |
| movement:y_negative | 42 | 1 | 1 | 0.314618 | 8.97835e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.709035 | 8.97835e-05 |
| time:post_progress_step | 130 | 0 | 1 | 0.762311 | 4.65229e-05 |
| time:progress_step | 10 | 1 | 1 | 0.685418 | 4.95132e-08 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
