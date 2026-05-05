# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v011_nonlocal_second_family_v033_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v011_nonlocal_second_family_v033_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `986a3299ea548a0aef6cafd01ef282824aac48ea`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu/metrics.json`
- records: `6932`
- splits: `{'heldout': 3112, 'train': 3820}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `3820` positives=`27` signed_MAE=`0.009147306591810546` progress_acc=`1.0`
- heldout records: `3112` positives=`25` signed_MAE=`0.010573881841384372` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `13.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 2618 | 0 | 1 | 0.00857963 | 0.000195519 |
| control_label:dominant_group:time_phase | 319 | 0 | 1 | 0.0320567 | 3.88215e-05 |
| control_label:stasis_no_change | 150 | 0 | 1 | 0.000738578 | 5.91755e-05 |
| control_label:dominant_group:goal_progress | 25 | 25 | 1 | 0.00430226 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 1313 | 25 | 1 | 0.0127505 | 0.000195519 |
| action:ACTION3 | 1283 | 0 | 1 | 0.00964904 | 9.41342e-05 |
| action:ACTION1 | 348 | 0 | 1 | 0.00644558 | 2.24628e-05 |
| action:ACTION2 | 96 | 0 | 1 | 0.0105415 | 1.04314e-05 |
| action:ACTION5 | 72 | 0 | 1 | 0.00735684 | 4.72259e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:none | 1437 | 0 | 1 | 0.0130453 | 0.000195519 |
| movement:y_positive | 1275 | 0 | 1 | 0.00885642 | 0.000169523 |
| movement:y_negative | 300 | 25 | 1 | 0.00678069 | 2.24628e-05 |
| movement:x_negative | 50 | 0 | 1 | 0.00838343 | 1.64573e-05 |
| movement:x_positive | 50 | 0 | 1 | 0.00829057 | 9.16704e-06 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:post_progress_step | 2437 | 0 | 1 | 0.0118212 | 0.000195519 |
| time:pre_progress_step | 650 | 0 | 1 | 0.00613849 | 0.000169523 |
| time:progress_step | 25 | 25 | 1 | 0.00430226 |  |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
