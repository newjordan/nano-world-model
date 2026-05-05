# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_v010_ft09_targeted_coordinate`
- run kind: `bridge_manifest_generation`
- generator commit: `8bcbcebdaa7ce3b23bb8758285401395bcb3fb1d`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_ft09_targeted_coordinate/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v010_ft09_targeted_coordinate_scout/grid/transition_events/v010_ft09_targeted_coordinate_v009prior_seed0.transitions.jsonl` rows=`32` sha256=`42f93d7a011b525769f6bf38d13c3f0752b1d670c9b7e5bd37e816aca727f9f1`

## Validation

- valid: `True`
- records: `32`
- errors: `0`
- progress records: `0`
- positive signed-outcome records: `2`
- negative signed-outcome records: `30`

## Labels

- progress labels: `{'no_level_progress': 32}`
- control labels: `{'dominant_group:stasis_loop': 29, 'dominant_group:time_phase': 1, 'dominant_group:translation': 1, 'terminal_or_failure': 1}`
