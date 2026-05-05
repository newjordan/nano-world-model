# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v009_action6_coverage_ft09_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v009_action6_coverage_ft09_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `2865cfff9204c83f443813a84950968723025e33`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/metrics.json`
- records: `2744`
- splits: `{'heldout': 80, 'train': 2664}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `2664` positives=`25` signed_MAE=`0.005236394294765628` progress_acc=`1.0`
- heldout records: `80` positives=`1` signed_MAE=`0.008341474298504181` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:stasis_no_change | 44 | 0 | 1 | 0.00414691 | 0.000242599 |
| control_label:dominant_group:translation | 34 | 0 | 1 | 0.0140218 | 0.000113473 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.00753534 |  |
| control_label:dominant_group:time_phase | 1 | 0 | 1 | 0.00057596 | 5.12861e-06 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 40 | 0 | 1 | 0.00453176 | 0.000242599 |
| action:ACTION4 | 17 | 1 | 1 | 0.0247423 | 0.000113473 |
| action:ACTION1 | 12 | 0 | 1 | 0.00322477 | 5.21513e-05 |
| action:ACTION3 | 11 | 0 | 1 | 0.00243014 | 0.000107558 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:none | 49 | 0 | 1 | 0.00447668 | 0.000242599 |
| movement:y_positive | 15 | 0 | 1 | 0.0260453 | 0.000107558 |
| movement:y_negative | 12 | 1 | 1 | 0.00382318 | 5.21513e-05 |
| movement:x_negative | 2 | 0 | 1 | 0.0025462 | 1.89941e-06 |
| movement:x_positive | 2 | 0 | 1 | 0.00315491 | 1.17005e-06 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 52 | 0 | 1 | 0.00402133 | 0.000230935 |
| time:post_progress_step | 26 | 0 | 1 | 0.0166809 | 0.000138724 |
| time:progress_step | 2 | 1 | 1 | 0.0122525 | 0.000242599 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
