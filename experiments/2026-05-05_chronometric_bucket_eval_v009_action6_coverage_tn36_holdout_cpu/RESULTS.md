# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v009_action6_coverage_tn36_holdout_cpu`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v009_action6_coverage_tn36_holdout_cpu`
- run kind: `diagnostic_analysis_no_training`
- git commit: `2865cfff9204c83f443813a84950968723025e33`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/metrics.json`
- records: `2744`
- splits: `{'heldout': 80, 'train': 2664}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `2664` positives=`25` signed_MAE=`0.006062301016975874` progress_acc=`1.0`
- heldout records: `80` positives=`1` signed_MAE=`0.041599243340897374` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:stasis_loop | 38 | 0 | 1 | 0.0143605 | 0.00148635 |
| control_label:dominant_group:translation | 35 | 0 | 1 | 0.0432484 | 0.000111886 |
| control_label:stasis_no_change | 4 | 0 | 1 | 0.000812292 | 6.82799e-05 |
| control_label:dominant_group:time_phase | 2 | 0 | 1 | 0.628971 | 7.91035e-05 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.00735569 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION6 | 40 | 0 | 1 | 0.0698827 | 0.00148635 |
| action:ACTION4 | 17 | 1 | 1 | 0.025247 | 0.000111886 |
| action:ACTION1 | 12 | 0 | 1 | 0.00521356 | 5.66095e-05 |
| action:ACTION3 | 11 | 0 | 1 | 0.0037155 | 9.82568e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 41 | 0 | 1 | 0.0440894 | 0.00148635 |
| movement:y_positive | 16 | 0 | 1 | 0.0867457 | 9.82568e-05 |
| movement:y_negative | 12 | 1 | 1 | 0.00573809 | 5.66095e-05 |
| movement:none | 9 | 0 | 1 | 0.00535532 | 0.000111886 |
| movement:x_positive | 2 | 0 | 1 | 0.00764333 | 1.24936e-06 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 52 | 0 | 1 | 0.0552883 | 0.000310189 |
| time:post_progress_step | 26 | 0 | 1 | 0.0171105 | 0.00148635 |
| time:progress_step | 2 | 1 | 1 | 0.0040372 | 0.000414391 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
