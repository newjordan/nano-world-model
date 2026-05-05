# ARC Bridge Manifest Merge Results

Status: already-conditioned bridge manifests merged without changing per-record provenance.

This is not training data promotion. Source condition artifacts remain attached to each record.

## Condition

- run label: `arc_bridge_manifest_v011_nonlocal_second_family`
- run kind: `bridge_manifest_merge`
- generator commit: `d8b7f74431cf3aaafbcc1d4e4d58e981856f4af2`
- generator dirty at run: `False`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/arc_bridge_manifest.jsonl`
- training data promoted: `False`

## Source Manifests

- `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/arc_bridge_manifest.jsonl` rows=`3820` conditions=`['experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md', 'experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md', 'experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md', 'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md', 'experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md', 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v011_v033_nonlocal_holdout_family/arc_bridge_manifest.jsonl` rows=`3112` conditions=`['experiments/2026-05-05_v033_post_progress_nonlocal_replay/CONDITION.md']`

## Validation

- valid: `True`
- records: `6932`
- errors: `0`
- progress records: `52`
- positive signed-outcome records: `5607`
- negative signed-outcome records: `1325`

## Source Conditions

- source condition counts: `{'experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md': 322, 'experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md': 32, 'experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md': 322, 'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md': 400, 'experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md': 400, 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md': 2344, 'experiments/2026-05-05_v033_post_progress_nonlocal_replay/CONDITION.md': 3112}`
