# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v013_action6_support_v015_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v013_action6_support_v015_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `f16f24cb9b79a7a9973aa2883d2a7dcacfb025b5`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v013_action6_support_v015_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v013_action6_support_v015_holdout_cpu/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`0.01497474570712405` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.027918639009585605` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 246 | 0 | 1 | 0.0264449 | 0.000811663 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0256865 | 0.000145371 |
| control_label:stasis_no_change | 61 | 0 | 1 | 7.4069e-05 | 0.000104177 |
| control_label:dominant_group:time_phase | 17 | 0 | 1 | 0.159137 | 0.000302222 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 99 | 0 | 1 | 0.0513169 | 0.000811663 |
| action:ACTION2 | 69 | 0 | 1 | 0.026242 | 3.81712e-05 |
| action:ACTION4 | 66 | 0 | 1 | 0.0143214 | 0.000138862 |
| action:ACTION3 | 61 | 0 | 1 | 0.025861 | 9.61643e-05 |
| action:ACTION1 | 57 | 0 | 1 | 0.0210447 | 3.10595e-05 |
| action:ACTION5 | 48 | 0 | 1 | 0.0115439 | 0.000139549 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 169 | 0 | 1 | 0.0411416 | 0.000653521 |
| movement:none | 71 | 0 | 1 | 0.00135369 | 0.000104177 |
| movement:y_positive | 68 | 0 | 1 | 0.0326114 | 0.000811663 |
| movement:x_positive | 58 | 0 | 1 | 0.0144205 | 0.000117702 |
| movement:y_negative | 34 | 0 | 1 | 0.0313075 | 5.29793e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0306413 | 0.000811663 |
| time:post_progress_step | 130 | 0 | 1 | 0.0232829 | 0.000722241 |
| time:progress_step | 10 | 0 | 1 | 0.017393 | 5.71183e-05 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
