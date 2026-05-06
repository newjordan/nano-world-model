# Chronometric Feature Coverage Results

Status: posthoc feature-coverage diagnostic for `chronometric_feature_coverage_v026_v015_holdout_cross_family`.

This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.

## Condition

- run label: `chronometric_feature_coverage_v026_v015_holdout_cross_family`
- run kind: `diagnostic_analysis_no_training`
- git commit: `3504daa537e6fbead27a10ad6550a7d714a9b993`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_branch_library_v026_v015_holdout_cross_family_v016_predictions/predictions.jsonl`
- records: `7732`
- training data promoted: `False`

## Top Heldout Action-Control Errors

| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| action:ACTION1|control_label:stasis_no_change | 2 | 0.000267416 | 0.000267416 | action:ACTION3|control_label:stasis_no_change | 0.123319 | 104 | 0.248735 |
| action:ACTION3|control_label:stasis_no_change | 2 | 0.000180542 | 0.000180542 | action:ACTION3|control_label:stasis_no_change | 0.142982 | 171 | 0.142982 |
| action:ACTION2|control_label:stasis_no_change | 5 | 0.00016762 | 0.00016762 | action:ACTION1|control_label:stasis_no_change | 0.0468224 | 64 | 0.110404 |
| action:ACTION5|control_label:stasis_no_change | 3 | 0.000163535 | 0.000163535 | action:ACTION4|control_label:stasis_no_change | 0.059652 | 82 | 0.0808697 |
| action:ACTION4|control_label:stasis_no_change | 2 | 0.000147194 | 0.000147194 | action:ACTION5|control_label:stasis_no_change | 0.050725 | 11 | 0.0878982 |
| action:ACTION6|control_label:stasis_no_change | 47 | 2.48932e-05 | 2.48932e-05 | action:ACTION6|control_label:stasis_no_change | 0.0866513 | 416 | 0.0866513 |
| action:ACTION1|control_label:dominant_group:time_phase | 2 | 0 | 0 | action:ACTION1|control_label:dominant_group:time_phase | 0.051513 | 57 | 0.051513 |
| action:ACTION1|control_label:dominant_group:translation | 53 | 0 | 0 | action:ACTION1|control_label:dominant_group:translation | 0.0256286 | 685 | 0.0256286 |

## Interpretation

- high same-label distance means train contains the same action/control label but under different feature conditions
- missing same-label train rows means the heldout bucket is outside the train action/control coverage
- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change
