# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v023_translation_fallback`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v023_translation_fallback`
- run kind: `diagnostic_analysis_no_training`
- git commit: `d87f8eb8bbb64c09801d83fb94fdb137c408eac7`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_branch_library_v023_translation_fallback_v018_geometry_predictions/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_branch_library_v023_translation_fallback_v018_geometry_predictions/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`0.001232115453260555` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.002145120054483414` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0 | 0.000526582 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0092246 | 0.0014542 |
| control_label:stasis_no_change | 65 | 0 | 1 | 0.000591716 | 6.12296e-05 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.00538715 | 9.8398e-05 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.00420897 | 0.0014542 |
| action:ACTION2 | 69 | 0 | 1 | 4.00206e-05 | 3.46886e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.000450239 | 0.000104785 |
| action:ACTION3 | 58 | 0 | 1 | 0.000431237 | 5.42714e-05 |
| action:ACTION5 | 58 | 0 | 1 | 0.00499378 | 0.000325672 |
| action:ACTION1 | 51 | 0 | 1 | 0.0015617 | 7.50393e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.00426852 | 0.0014542 |
| movement:none | 75 | 0 | 1 | 0.000800351 | 6.12296e-05 |
| movement:y_positive | 67 | 0 | 1 | 0 | 0.000526582 |
| movement:x_positive | 49 | 0 | 1 | 0.000518784 | 9.8398e-05 |
| movement:y_negative | 28 | 0 | 1 | 0 | 0.000186805 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.00248735 | 0.0014542 |
| time:post_progress_step | 130 | 0 | 1 | 0.0015313 | 0.000427192 |
| time:progress_step | 10 | 0 | 1 | 0.00122685 | 0.000218956 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
