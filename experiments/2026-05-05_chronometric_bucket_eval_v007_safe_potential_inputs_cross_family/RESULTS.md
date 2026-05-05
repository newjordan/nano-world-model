# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v007_safe_potential_inputs_cross_family`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v007_safe_potential_inputs_cross_family`
- run kind: `diagnostic_analysis_no_training`
- git commit: `f70bbc5e6f9407e5cf661a5c009a1648af6a9ddb`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/metrics.json`
- records: `2744`
- splits: `{'heldout': 400, 'train': 2344}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `2344` positives=`25` signed_MAE=`0.011312737735743244` progress_acc=`1.0`
- heldout records: `400` positives=`1` signed_MAE=`0.18368175233445072` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 257 | 0 | 1 | 0.064325 | 0.000129216 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.69665 | 2.02083e-07 |
| control_label:stasis_no_change | 50 | 0 | 1 | 0.000478867 | 2.23517e-05 |
| control_label:dominant_group:time_phase | 16 | 0 | 1 | 0.247933 | 1.66792e-05 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.00493729 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 87 | 1 | 1 | 0.120778 | 8.63469e-05 |
| action:ACTION6 | 80 | 0 | 1 | 0.0343842 | 0 |
| action:ACTION3 | 65 | 0 | 1 | 0.0473382 | 0.000129216 |
| action:ACTION2 | 61 | 0 | 1 | 0.0309594 | 3.70913e-05 |
| action:ACTION5 | 55 | 0 | 1 | 0.972137 | 4.2314e-06 |
| action:ACTION1 | 52 | 0 | 1 | 0.0342549 | 0.000111723 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 193 | 0 | 1 | 0.309909 | 3.32479e-05 |
| movement:x_positive | 67 | 0 | 1 | 0.148511 | 4.2897e-05 |
| movement:none | 55 | 0 | 1 | 0.00109085 | 3.843e-05 |
| movement:y_positive | 43 | 0 | 1 | 0.0580026 | 0.000129216 |
| movement:y_negative | 42 | 1 | 1 | 0.0275204 | 0.000111723 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.181065 | 0.000129216 |
| time:post_progress_step | 130 | 0 | 1 | 0.186258 | 0.00011326 |
| time:progress_step | 10 | 1 | 1 | 0.218224 | 2.3827e-05 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
