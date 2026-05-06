# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v019b_transductive_branch_consistency_v016_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v019b_transductive_branch_consistency_v016_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `3f771872c3b2b7e1f7f4c8758b29dfe433267bdc`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v019b_transductive_branch_consistency_v016_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v019b_transductive_branch_consistency_v016_holdout_cpu/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`0.005321831390606768` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`0.017020190202165397` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 237 | 0 | 1 | 0.0187832 | 0.000430043 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.0170205 | 0.00133282 |
| control_label:stasis_no_change | 65 | 0 | 1 | 0.00051886 | 8.20615e-05 |
| control_label:dominant_group:time_phase | 22 | 0 | 1 | 0.0467803 | 9.62196e-05 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 103 | 0 | 1 | 0.0180064 | 0.00133282 |
| action:ACTION2 | 69 | 0 | 1 | 0.00966506 | 3.13378e-05 |
| action:ACTION4 | 61 | 0 | 1 | 0.00949663 | 9.62196e-05 |
| action:ACTION3 | 58 | 0 | 1 | 0.014111 | 5.59367e-05 |
| action:ACTION5 | 58 | 0 | 1 | 0.0358038 | 0.000386932 |
| action:ACTION1 | 51 | 0 | 1 | 0.015925 | 6.93131e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 181 | 0 | 1 | 0.016642 | 0.00133282 |
| movement:none | 75 | 0 | 1 | 0.00115448 | 8.20615e-05 |
| movement:y_positive | 67 | 0 | 1 | 0.0261354 | 0.000430043 |
| movement:x_positive | 49 | 0 | 1 | 0.00773236 | 9.62196e-05 |
| movement:y_negative | 28 | 0 | 1 | 0.0564044 | 0.000179701 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.018742 | 0.00133282 |
| time:post_progress_step | 130 | 0 | 1 | 0.01418 | 0.00030229 |
| time:progress_step | 10 | 0 | 1 | 0.00917697 | 0.000208547 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
