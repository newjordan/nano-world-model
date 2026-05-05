# Chronometric Bucket Eval V005 Results

Status: posthoc bucket diagnostic over the recorded V004 group-holdout predictions.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v005`
- run kind: `diagnostic_analysis_no_training`
- git commit: `ad9ddcd3c1e29b72d0df2a12f9be89fddb6984dd`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v004_group_holdout/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v004_group_holdout/metrics.json`
- records: `2344`
- splits: `{'heldout': 576, 'train': 1768}`
- training data promoted: `False`

## Split Summary

- train records: `1768` positives=`19` signed_MAE=`0.09288970482582015` progress_acc=`1.0`
- heldout records: `576` positives=`6` signed_MAE=`0.09581121484128137` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `3.5`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 478 | 0 | 1 | 0.0956211 | 0.000345078 |
| control_label:dominant_group:time_phase | 50 | 0 | 1 | 0.0413131 | 6.02837e-05 |
| control_label:stasis_no_change | 42 | 0 | 1 | 0.169949 | 2.91567e-06 |
| control_label:dominant_group:goal_progress | 6 | 6 | 1 | 0.0461398 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION3 | 236 | 0 | 1 | 0.0857947 | 0.000200602 |
| action:ACTION4 | 176 | 6 | 1 | 0.0656461 | 4.02932e-05 |
| action:ACTION1 | 84 | 0 | 1 | 0.131193 | 0.000345078 |
| action:ACTION2 | 62 | 0 | 1 | 0.0700404 | 6.83621e-05 |
| action:ACTION5 | 18 | 0 | 1 | 0.445737 | 1.65155e-08 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:y_positive | 250 | 0 | 1 | 0.112885 | 0.000200602 |
| movement:none | 219 | 0 | 1 | 0.09468 | 6.48111e-05 |
| movement:y_negative | 80 | 6 | 1 | 0.0489121 | 0.000345078 |
| movement:x_negative | 15 | 0 | 1 | 0.117818 | 1.73098e-06 |
| movement:x_positive | 12 | 0 | 1 | 0.045906 | 2.20777e-07 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:post_progress_step | 414 | 0 | 1 | 0.116932 | 0.000345078 |
| time:pre_progress_step | 156 | 0 | 1 | 0.0416694 | 0.000200602 |
| time:progress_step | 6 | 6 | 1 | 0.0461398 |  |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- this remains one m0r0 replay family; V006 should add cross-task or cross-family holdout
