# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_smoke`
- run kind: `bridge_manifest_generation`
- generator commit: `b76ee5c27a1e4ccf1eb004f928efb33893eaad04`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_smoke/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl` rows=`40` sha256=`47d0680c6a5f81d651dfe1d1ef4de8db5fe385d35fd49263750d6fc7145839e1`

## Validation

- valid: `True`
- records: `40`
- errors: `0`
- progress records: `1`
- positive signed-outcome records: `36`
- negative signed-outcome records: `4`

## Labels

- progress labels: `{'no_level_progress': 39, 'progress_level_delta_positive': 1}`
- control labels: `{'dominant_group:goal_progress': 1, 'dominant_group:time_phase': 1, 'dominant_group:translation': 34, 'stasis_no_change': 4}`
