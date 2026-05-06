# ARC Bridge Manifest Merge Results

Status: already-conditioned bridge manifests merged without changing per-record provenance.

This is not training data promotion. Source condition artifacts remain attached to each record.

## Condition

- run label: `arc_bridge_manifest_v017_v015_support_v016_holdout`
- run kind: `bridge_manifest_merge`
- generator commit: `88f673ccfd40b793998809528a00b32e5b9aa905`
- generator dirty at run: `False`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- training data promoted: `False`

## Source Manifests

- `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/arc_bridge_manifest.jsonl` rows=`7332` conditions=`['experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md', 'experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md', 'experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md', 'experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md', 'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md', 'experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md', 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md', 'experiments/2026-05-05_v033_post_progress_nonlocal_replay/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v013_v015_action6_holdout_family/arc_bridge_manifest.jsonl` rows=`400` conditions=`['experiments/2026-05-04_v015_object_relative_movement_scout/CONDITION.md']`

## Validation

- valid: `True`
- records: `7732`
- errors: `0`
- progress records: `52`
- positive signed-outcome records: `6129`
- negative signed-outcome records: `1603`

## Source Conditions

- source condition counts: `{'experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md': 322, 'experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md': 32, 'experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md': 322, 'experiments/2026-05-04_v015_object_relative_movement_scout/CONDITION.md': 400, 'experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md': 400, 'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md': 400, 'experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md': 400, 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md': 2344, 'experiments/2026-05-05_v033_post_progress_nonlocal_replay/CONDITION.md': 3112}`
