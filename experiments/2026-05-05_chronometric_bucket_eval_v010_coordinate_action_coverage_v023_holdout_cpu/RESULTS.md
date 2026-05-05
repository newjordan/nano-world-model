# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v010_coordinate_action_coverage_v023_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v010_coordinate_action_coverage_v023_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `05cce0cf4c3d8a8f0e0e399ecb45c6522e504195`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/metrics.json`
- records: `3820`
- splits: `{'heldout': 400, 'train': 3420}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `3420` positives=`26` signed_MAE=`0.007702412620361769` progress_acc=`1.0`
- heldout records: `400` positives=`1` signed_MAE=`0.015096905914833769` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 257 | 0 | 1 | 0.0129062 | 0.00126112 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0166379 | 0.000550144 |
| control_label:stasis_no_change | 50 | 0 | 1 | 0.000716212 | 0.000193346 |
| control_label:dominant_group:time_phase | 16 | 0 | 1 | 0.0884596 | 0.000227777 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.00622749 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 87 | 1 | 1 | 0.0186731 | 0.000214481 |
| action:ACTION6 | 80 | 0 | 1 | 0.0235673 | 0.00126112 |
| action:ACTION3 | 65 | 0 | 1 | 0.00802302 | 8.35619e-05 |
| action:ACTION2 | 61 | 0 | 1 | 0.00754761 | 3.15873e-05 |
| action:ACTION5 | 55 | 0 | 1 | 0.0108751 | 0.000242089 |
| action:ACTION1 | 52 | 0 | 1 | 0.0182459 | 1.83997e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 193 | 0 | 1 | 0.017925 | 0.000550144 |
| movement:x_positive | 67 | 0 | 1 | 0.0169731 | 0.00015104 |
| movement:none | 55 | 0 | 1 | 0.00166099 | 0.000214481 |
| movement:y_positive | 43 | 0 | 1 | 0.0200838 | 0.00126112 |
| movement:y_negative | 42 | 1 | 1 | 0.011597 | 3.19432e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0164947 | 0.00126112 |
| time:post_progress_step | 130 | 0 | 1 | 0.0124537 | 0.000216217 |
| time:progress_step | 10 | 1 | 1 | 0.0131167 | 0.000106641 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
