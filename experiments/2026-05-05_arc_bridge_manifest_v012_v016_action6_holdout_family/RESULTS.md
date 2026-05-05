# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_v012_v016_action6_holdout_family`
- run kind: `bridge_manifest_generation`
- generator commit: `471382a23eb16832a8bd85fb7534d5d147c1b6a2`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v012_v016_action6_holdout_family/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_dc22_seed0.transitions.jsonl` rows=`40` sha256=`15a5db1cccb451ad47be9c22a290b4b1605150a51e6c2206d3dbaed1d0b912e8`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_ft09_seed0.transitions.jsonl` rows=`40` sha256=`76dc0c4cbfc22d2f774a4af04065011d263b2b4fef14eb50f5ad43713f3a896f`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_g50t_seed0.transitions.jsonl` rows=`40` sha256=`abf8ec5a79a86f4e150830fd9d96a2100389cd86bdbea3abf1b4f0848b954fb6`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_ka59_seed0.transitions.jsonl` rows=`40` sha256=`43ad624534332352167f52f4c1c4e5bb2461c3c7a81c5916c388424862680ec9`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_m0r0_seed0.transitions.jsonl` rows=`40` sha256=`ff75aef9710bd187d98d27b813cbc0a3048535722f9eca6a5f21134a1113df03`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_sb26_seed0.transitions.jsonl` rows=`40` sha256=`8a7308b2d7121f1d4a727c8c7d034c2ab72462846f9077c0b9b96b45162f00fe`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_sc25_seed0.transitions.jsonl` rows=`40` sha256=`1f30a61509fcfaa6db494d7e999597c2a0bfc66c75b449097e50610e026315ed`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_tn36_seed0.transitions.jsonl` rows=`40` sha256=`508d33a5b6cbe62bc0495eba706f0b737d61f5c47b286adacaae23b8910e5966`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_tr87_seed0.transitions.jsonl` rows=`40` sha256=`2bb06fd25d3228c159270d394baa9375aa95be8fad82440e1ac989306c7d6012`
- `experiments/2026-05-04_v016_controllability_movement_scout/grid/transition_events/v016_current_state_v016_controllability_tu93_seed0.transitions.jsonl` rows=`40` sha256=`ac151c0d534acd83b7beb232a003fe8b2c71def4fbfce8db4a7c4af5936b47b9`

## Validation

- valid: `True`
- records: `400`
- errors: `0`
- progress records: `0`
- positive signed-outcome records: `259`
- negative signed-outcome records: `141`

## Labels

- progress labels: `{'no_level_progress': 400}`
- control labels: `{'dominant_group:stasis_loop': 76, 'dominant_group:time_phase': 22, 'dominant_group:translation': 237, 'stasis_no_change': 65}`
