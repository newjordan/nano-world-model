# ARC Bridge Manifest Merge Results

Status: already-conditioned bridge manifests merged without changing per-record provenance.

This is not training data promotion. Source condition artifacts remain attached to each record.

## Condition

- run label: `arc_bridge_manifest_v010_coordinate_action_coverage`
- run kind: `bridge_manifest_merge`
- generator commit: `a6b0763f8b1a224079ecdddc7305f527d6f64b30`
- generator dirty at run: `False`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl`
- training data promoted: `False`

## Source Manifests

- `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl` rows=`2744` conditions=`['experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md', 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v010_ft09_action6_affordance/arc_bridge_manifest.jsonl` rows=`322` conditions=`['experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v010_ft09_targeted_coordinate/arc_bridge_manifest.jsonl` rows=`32` conditions=`['experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v010_tn36_action6_heatmap/arc_bridge_manifest.jsonl` rows=`322` conditions=`['experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family/arc_bridge_manifest.jsonl` rows=`400` conditions=`['experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md']`

## Validation

- valid: `True`
- records: `3820`
- errors: `0`
- progress records: `27`
- positive signed-outcome records: `2645`
- negative signed-outcome records: `1175`

## Source Conditions

- source condition counts: `{'experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md': 322, 'experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md': 32, 'experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md': 322, 'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md': 400, 'experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md': 400, 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md': 2344}`
