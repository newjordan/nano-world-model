# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_v010_tn36_action6_heatmap`
- run kind: `bridge_manifest_generation`
- generator commit: `fbce52aad55ef67b800e22774c2749d92961a4bb`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_tn36_action6_heatmap/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v011_tn36_action6_coordinate_heatmap/grid/transition_events/v011_action6_heatmap_tn36_stride4_seed0.transitions.jsonl` rows=`322` sha256=`acbbdf68ca2cbea0bf62e219aa1dc5c4916f0bdcd53d3c0864223dec7d685b6d`

## Validation

- valid: `True`
- records: `322`
- errors: `0`
- progress records: `0`
- positive signed-outcome records: `2`
- negative signed-outcome records: `320`

## Labels

- progress labels: `{'no_level_progress': 322}`
- control labels: `{'dominant_group:stasis_loop': 320, 'dominant_group:time_phase': 1, 'dominant_group:translation': 1}`
