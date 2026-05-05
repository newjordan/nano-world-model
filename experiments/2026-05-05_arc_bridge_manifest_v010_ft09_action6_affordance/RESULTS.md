# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_v010_ft09_action6_affordance`
- run kind: `bridge_manifest_generation`
- generator commit: `917a033cf354f9b995fbb318d6c4931a84096aa9`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v009_ft09_action6_affordance_sweep/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_ft09_action6_affordance/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v009_ft09_action6_affordance_sweep/grid/transition_events/v009_action6_affordance_ft09_stride4_seed0.transitions.jsonl` rows=`322` sha256=`7c87e7f3ef04f7783e9e4d50d460b4df3612dad6e935e2b11c662833ed26ee2e`

## Validation

- valid: `True`
- records: `322`
- errors: `0`
- progress records: `0`
- positive signed-outcome records: `0`
- negative signed-outcome records: `322`

## Labels

- progress labels: `{'no_level_progress': 322}`
- control labels: `{'dominant_group:stasis_loop': 32, 'stasis_no_change': 290}`
