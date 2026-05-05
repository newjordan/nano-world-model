# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v012_action6_ten_task_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v012_action6_ten_task_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `152d998841706af882898ab11e1de81749c596e9`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v012_action6_ten_task_v016_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v012_action6_ten_task_v016_holdout_cpu/metrics.json`
- records: `7332`
- splits: `{'heldout': 400, 'train': 6932}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `6932` positives=`52` signed_MAE=`0.008138627609466022` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.045109987236573945` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0.058857 | 0.00150808 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0176769 | 0.000287269 |
| control_label:stasis_no_change | 65 | 0 | 1 | 0.000162866 | 0.000257299 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.124584 | 0.00068154 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.110621 | 0.00150808 |
| action:ACTION2 | 69 | 0 | 1 | 0.0199093 | 6.54812e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.0119351 | 0.000203179 |
| action:ACTION3 | 58 | 0 | 1 | 0.0184463 | 0.000239495 |
| action:ACTION5 | 58 | 0 | 1 | 0.0417113 | 0.000287269 |
| action:ACTION1 | 51 | 0 | 1 | 0.0207674 | 3.12789e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.0298423 | 0.000836533 |
| movement:none | 75 | 0 | 1 | 0.000868756 | 0.000257299 |
| movement:y_positive | 67 | 0 | 1 | 0.150723 | 0.00150808 |
| movement:x_positive | 49 | 0 | 1 | 0.0100224 | 0.000203179 |
| movement:y_negative | 28 | 0 | 1 | 0.0709955 | 0.000708356 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0451547 | 0.00150808 |
| time:post_progress_step | 130 | 0 | 1 | 0.0466109 | 0.000997405 |
| time:progress_step | 10 | 0 | 1 | 0.0244361 | 0.00124197 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
