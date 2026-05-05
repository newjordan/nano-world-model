# Chronometric Bucket Eval V005 Results

Status: posthoc bucket diagnostic over the recorded V004 group-holdout predictions.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v006_cross_family`
- run kind: `diagnostic_analysis_no_training`
- git commit: `7ae4b50f5e7baf3d26cda5c92e68b4730ad46535`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v006_cross_family_holdout/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v006_cross_family_holdout/metrics.json`
- records: `2744`
- splits: `{'heldout': 400, 'train': 2344}`
- training data promoted: `False`

## Split Summary

- train records: `2344` positives=`25` signed_MAE=`0.08557802089410532` progress_acc=`1.0`
- heldout records: `400` positives=`1` signed_MAE=`6074.740799146891` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 257 | 0 | 1 | 70.9702 | 0.000142589 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 15574.1 | 2.32949e-07 |
| control_label:stasis_no_change | 50 | 0 | 1 | 24296.9 | 1.65777e-06 |
| control_label:dominant_group:time_phase | 16 | 0 | 1 | 823.769 | 2.31714e-05 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.0220021 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 87 | 1 | 1 | 0.465984 | 6.49962e-05 |
| action:ACTION6 | 80 | 0 | 1 | 30371 | 0 |
| action:ACTION3 | 65 | 0 | 1 | 1.17057 | 0.000142589 |
| action:ACTION2 | 61 | 0 | 1 | 0.431974 | 3.79519e-06 |
| action:ACTION5 | 55 | 0 | 1 | 0.9327 | 4.01286e-07 |
| action:ACTION1 | 52 | 0 | 1 | 0.405105 | 2.43926e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 193 | 0 | 1 | 6201.6 | 6.15183e-06 |
| movement:x_positive | 67 | 0 | 1 | 0.501076 | 1.0852e-05 |
| movement:none | 55 | 0 | 1 | 22088.1 | 4.11792e-05 |
| movement:y_positive | 43 | 0 | 1 | 420.823 | 0.000142589 |
| movement:y_negative | 42 | 1 | 1 | 0.304535 | 2.43926e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 6814.4 | 0.000142589 |
| time:post_progress_step | 130 | 0 | 1 | 4802.54 | 4.07146e-05 |
| time:progress_step | 10 | 1 | 1 | 3382.23 | 2.11702e-07 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- this remains one m0r0 replay family; V006 should add cross-task or cross-family holdout
