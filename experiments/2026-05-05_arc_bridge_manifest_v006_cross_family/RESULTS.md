# ARC Bridge Manifest Merge Results

Status: already-conditioned bridge manifests merged without changing per-record provenance.

This is not training data promotion. Source condition artifacts remain attached to each record.

## Condition

- run label: `arc_bridge_manifest_v006_cross_family`
- run kind: `bridge_manifest_merge`
- generator commit: `c3c5257d7fdeadf24848de306cec42ef1f2ca175`
- generator dirty at run: `False`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- training data promoted: `False`

## Source Manifests

- `experiments/2026-05-05_arc_bridge_manifest_v004_controlled_batch/arc_bridge_manifest.jsonl` rows=`2344` conditions=`['experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md']`
- `experiments/2026-05-05_arc_bridge_manifest_v006_v019b_ten_task_family/arc_bridge_manifest.jsonl` rows=`400` conditions=`['experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md']`

## Validation

- valid: `True`
- records: `2744`
- errors: `0`
- progress records: `26`
- positive signed-outcome records: `2367`
- negative signed-outcome records: `377`

## Source Conditions

- source condition counts: `{'experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md': 400, 'experiments/2026-05-05_v031b_post_progress_avoidance_replay_retry/CONDITION.md': 2344}`
