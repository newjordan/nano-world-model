# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v017_v015_support_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v017_v015_support_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `bc205444773a04af3995c0d452d41160e0508893`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v017_v015_support_v016_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v017_v015_support_v016_holdout_cpu/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`0.005296235684179456` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.023165112086207956` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0.0242589 | 0.00256079 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0166512 | 0.000109682 |
| control_label:stasis_no_change | 65 | 0 | 1 | 0.000330726 | 2.99354e-05 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.10135 | 0.000297791 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.0382095 | 0.00256079 |
| action:ACTION2 | 69 | 0 | 1 | 0.0118662 | 3.64017e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.00674379 | 9.29754e-05 |
| action:ACTION3 | 58 | 0 | 1 | 0.0125694 | 0.000151498 |
| action:ACTION5 | 58 | 0 | 1 | 0.0463199 | 9.14747e-05 |
| action:ACTION1 | 51 | 0 | 1 | 0.0134265 | 7.60006e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.0240543 | 0.00069261 |
| movement:none | 75 | 0 | 1 | 0.00129722 | 0.000151498 |
| movement:y_positive | 67 | 0 | 1 | 0.0458153 | 0.00256079 |
| movement:x_positive | 49 | 0 | 1 | 0.0085161 | 3.6502e-05 |
| movement:y_negative | 28 | 0 | 1 | 0.047429 | 0.0020703 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.0264344 | 0.00247339 |
| time:post_progress_step | 130 | 0 | 1 | 0.0175076 | 0.00242259 |
| time:progress_step | 10 | 0 | 1 | 0.0117115 | 0.00256079 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
