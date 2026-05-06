# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v017b_v015_support_v016_holdout_dominant_balance_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v017b_v015_support_v016_holdout_dominant_balance_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `279cbd82cb1b84d62cfb9e36fbd1c0a6c9aee6d7`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v017b_v015_support_v016_holdout_dominant_balance_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v017b_v015_support_v016_holdout_dominant_balance_cpu/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`0.007228070474964891` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.034029361935317866` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0.0362368 | 0.00922682 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0425566 | 0.000389806 |
| control_label:stasis_no_change | 65 | 0 | 1 | 5.60073e-05 | 6.0971e-05 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.0811672 | 0.000962257 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.0689185 | 0.00922682 |
| action:ACTION2 | 69 | 0 | 1 | 0.0127528 | 2.75914e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.0109453 | 8.7669e-05 |
| action:ACTION3 | 58 | 0 | 1 | 0.0131417 | 0.000205487 |
| action:ACTION5 | 58 | 0 | 1 | 0.0558758 | 0.00020464 |
| action:ACTION1 | 51 | 0 | 1 | 0.0188729 | 5.2997e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.0342164 | 0.00310487 |
| movement:none | 75 | 0 | 1 | 0.00108108 | 0.000205487 |
| movement:y_positive | 67 | 0 | 1 | 0.0771384 | 0.00906849 |
| movement:x_positive | 49 | 0 | 1 | 0.00906674 | 6.31744e-05 |
| movement:y_negative | 28 | 0 | 1 | 0.0616051 | 0.00922682 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0359479 | 0.00922682 |
| time:post_progress_step | 130 | 0 | 1 | 0.0303443 | 0.00713425 |
| time:progress_step | 10 | 0 | 1 | 0.0320526 | 0.00743341 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
