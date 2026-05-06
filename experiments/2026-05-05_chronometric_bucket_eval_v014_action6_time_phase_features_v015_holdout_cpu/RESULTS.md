# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v014_action6_time_phase_features_v015_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v014_action6_time_phase_features_v015_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `8d56cbdbf2359da3d0a04f65b6da1f16cad6db2e`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v014_action6_time_phase_features_v015_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v014_action6_time_phase_features_v015_holdout_cpu/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`0.005223083747097219` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.016086837843758986` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 246 | 0 | 1 | 0.0122062 | 0.00170848 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.016054 | 0.000138995 |
| control_label:stasis_no_change | 61 | 0 | 1 | 0.00023933 | 2.84796e-05 |
| control_label:dominant_group:time_phase | 17 | 0 | 1 | 0.129254 | 0.000240984 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 99 | 0 | 1 | 0.0322682 | 0.00170848 |
| action:ACTION2 | 69 | 0 | 1 | 0.0146552 | 3.62608e-05 |
| action:ACTION4 | 66 | 0 | 1 | 0.0085238 | 0.00012278 |
| action:ACTION3 | 61 | 0 | 1 | 0.0129316 | 8.48522e-05 |
| action:ACTION1 | 57 | 0 | 1 | 0.00470364 | 6.29632e-05 |
| action:ACTION5 | 48 | 0 | 1 | 0.0126972 | 6.40379e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 169 | 0 | 1 | 0.0262792 | 0.00103781 |
| movement:none | 71 | 0 | 1 | 0.000693529 | 8.48522e-05 |
| movement:y_positive | 68 | 0 | 1 | 0.0161881 | 0.00170848 |
| movement:x_positive | 58 | 0 | 1 | 0.00693682 | 3.99875e-05 |
| movement:y_negative | 34 | 0 | 1 | 0.0129759 | 6.29632e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0188129 | 0.00170848 |
| time:post_progress_step | 130 | 0 | 1 | 0.011066 | 0.00101941 |
| time:progress_step | 10 | 0 | 1 | 0.0104789 | 5.49778e-05 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
