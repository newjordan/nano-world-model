# Chronometric Bucket Eval Results

Status: posthoc bucket diagnostic for `chronometric_bucket_eval_v008_temporal_loop_context_cross_family`.

This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.

## Condition

- run label: `chronometric_bucket_eval_v008_temporal_loop_context_cross_family`
- run kind: `diagnostic_analysis_no_training`
- git commit: `b80425b6f06873884dba9611b01bb6068046a29e`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v008_temporal_loop_context_cross_family_holdout/predictions.jsonl`
- calibration metrics: `experiments/2026-05-05_chronometric_calibration_v008_temporal_loop_context_cross_family_holdout/metrics.json`
- records: `2744`
- splits: `{'heldout': 400, 'train': 2344}`
- eval scope: `posthoc_bucket_analysis`
- training data promoted: `False`

## Split Summary

- train records: `2344` positives=`25` signed_MAE=`0.0029640839764912517` progress_acc=`1.0`
- heldout records: `400` positives=`1` signed_MAE=`0.42049968824787354` progress_acc=`1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `1.0`

## Heldout Control Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| control_label:dominant_group:translation | 257 | 0 | 1 | 0.038926 | 0.000210271 |
| control_label:dominant_group:stasis_loop | 76 | 0 | 1 | 0.998018 | 8.53239e-08 |
| control_label:stasis_no_change | 50 | 0 | 1 | 1.60077 | 0.000270973 |
| control_label:dominant_group:time_phase | 16 | 0 | 1 | 0.144002 | 0.000287324 |
| control_label:dominant_group:goal_progress | 1 | 1 | 1 | 0.00417608 |  |

## Heldout Action Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| action:ACTION4 | 87 | 1 | 1 | 0.0676191 | 0.000270973 |
| action:ACTION6 | 80 | 0 | 1 | 1.96562 | 0 |
| action:ACTION3 | 65 | 0 | 1 | 0.0425122 | 0.000118062 |
| action:ACTION2 | 61 | 0 | 1 | 0.0118329 | 4.51261e-05 |
| action:ACTION5 | 55 | 0 | 1 | 0.0199724 | 0.000287324 |
| action:ACTION1 | 52 | 0 | 1 | 0.00931076 | 6.19879e-05 |

## Heldout Movement Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| movement:x_negative | 193 | 0 | 1 | 0.418328 | 0.000287324 |
| movement:x_positive | 67 | 0 | 1 | 0.0852743 | 2.94005e-05 |
| movement:none | 55 | 0 | 1 | 1.45554 | 0.000270973 |
| movement:y_positive | 43 | 0 | 1 | 0.0287401 | 0.000210271 |
| movement:y_negative | 42 | 1 | 1 | 0.0109252 | 5.19941e-05 |

## Heldout Time Buckets

| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |
| --- | ---: | ---: | ---: | ---: | ---: |
| time:pre_progress_step | 260 | 0 | 1 | 0.413368 | 0.000287324 |
| time:post_progress_step | 130 | 0 | 1 | 0.432912 | 0.000270973 |
| time:progress_step | 10 | 1 | 1 | 0.444548 | 1.96866e-05 |

## Interpretation

- progress rows remain cleanly separated in heldout branch files
- highest heldout non-progress probability stays far below the 0.5 progress threshold
- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification
- use the run label, manifest, and calibration metrics paths above as the exact scope boundary
