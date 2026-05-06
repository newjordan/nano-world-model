# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v025_stasis_loop_scope`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v025_stasis_loop_scope`
- run kind: `diagnostic_analysis_no_training`
- git commit: `199ce1110f7a908eb8d7e7248fab8e3107e5b1e4`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_branch_library_v025_stasis_loop_scope_v018_geometry_predictions/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION1|control_label:stasis_no_change | 8 | 0.00101436 | 0.00101436 | action:ACTION1|control_label:stasis_no_change | 0.0598119 | 98 | 0.0598119 |
| action:ACTION2|control_label:stasis_no_change | 3 | 0.000920475 | 0.000920475 | action:ACTION1|control_label:stasis_no_change | 0.0842986 | 66 | 0.15312 |
| action:ACTION3|control_label:stasis_no_change | 4 | 0.000861749 | 0.000861749 | action:ACTION5|control_label:stasis_no_change | 0.0540199 | 169 | 0.0654366 |
| action:ACTION5|control_label:stasis_no_change | 1 | 0.000797689 | 0.000797689 | action:ACTION3|control_label:stasis_no_change | 0.126743 | 84 | 0.172873 |
| action:ACTION4|control_label:stasis_no_change | 3 | 0.0006814 | 0.0006814 | action:ACTION5|control_label:stasis_no_change | 0.0750588 | 10 | 0.119656 |
| action:ACTION6|control_label:stasis_no_change | 46 | 0.000462965 | 0.000462965 | action:ACTION6|control_label:stasis_no_change | 0.0817008 | 417 | 0.0817008 |
| action:ACTION1|control_label:dominant_group:time_phase | 3 | 0 | 0 | action:ACTION1|control_label:dominant_group:stasis_loop | 0.1119 | 56 | 0.161167 |
| action:ACTION1|control_label:dominant_group:translation | 40 | 0 | 0 | action:ACTION1|control_label:dominant_group:translation | 0.0323953 | 698 | 0.0323953 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
