# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v026_v015_holdout_cross_family`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v026_v015_holdout_cross_family`
- run kind: `diagnostic_analysis_no_training`
- git commit: `daab917b6ff210a737dc4359bb80e86bffdc3fdc`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions/metrics.json`
- records: `7732`
- splits: `{'heldout': 400, 'train': 7332}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `7332` positives=`52` signed_MAE=`1.2584294833190051e-05` progress_acc=`1.0`
- heldout records: `400` positives=`0` signed_MAE=`9.222477674484252e-06` progress_acc=`1.0`
- heldout positive best rank: `None`
- heldout positive mean rank: `None`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 246 | 0 | 1 | 0 | 0.00349576 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0 | 0.00137825 |
| control_label:stasis_no_change | 61 | 0 | 1 | 6.04753e-05 | 4.00372e-05 |
| control_label:dominant_group:time_phase | 17 | 0 | 1 | 0 | 0.000662113 |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 99 | 0 | 1 | 1.1818e-05 | 0.00349576 |
| action:ACTION2 | 69 | 0 | 1 | 1.21464e-05 | 4.00372e-05 |
| action:ACTION4 | 66 | 0 | 1 | 4.46041e-06 | 8.05535e-05 |
| action:ACTION3 | 61 | 0 | 1 | 5.91943e-06 | 7.88651e-05 |
| action:ACTION1 | 57 | 0 | 1 | 9.38303e-06 | 7.30112e-05 |
| action:ACTION5 | 48 | 0 | 1 | 1.0221e-05 | 0.000137322 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 169 | 0 | 1 | 0 | 0.00181353 |
| movement:none | 71 | 0 | 1 | 5.19576e-05 | 8.05535e-05 |
| movement:y_positive | 68 | 0 | 1 | 0 | 0.00349576 |
| movement:x_positive | 58 | 0 | 1 | 0 | 3.26858e-05 |
| movement:y_negative | 34 | 0 | 1 | 0 | 7.30112e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 8.7103e-06 | 0.00349576 |
| time:post_progress_step | 130 | 0 | 1 | 1.04354e-05 | 0.00118778 |
| time:progress_step | 10 | 0 | 1 | 6.77109e-06 | 0.000549836 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
