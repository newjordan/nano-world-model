# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_v006_v019b_ten_task_family`
- run kind: `bridge_manifest_generation`
- generator commit: `3339500445e2ec1fc23afb94fb4d2cc18927c016`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_v019b_ten_task_family/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_dc22_seed0.transitions.jsonl` rows=`40` sha256=`40875b0ac742993d825ab4eaa8c5d52d1407c3e2b1d68ef4fa75cd4de33f90e0`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_ft09_seed0.transitions.jsonl` rows=`40` sha256=`c99358729096b20ca90eec68d887958d4408a18e5542dcc0c304e59b63d8147d`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_g50t_seed0.transitions.jsonl` rows=`40` sha256=`5278120de09e8e87c98b57520398313b9a7970cdcc56e393755f08552e0972d0`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_ka59_seed0.transitions.jsonl` rows=`40` sha256=`b16eaedf555a16c421823bd1a9da7ab0a15457a00d98570264623c11bdf1df66`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl` rows=`40` sha256=`47d0680c6a5f81d651dfe1d1ef4de8db5fe385d35fd49263750d6fc7145839e1`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_sb26_seed0.transitions.jsonl` rows=`40` sha256=`5661db2751689fb58ae39aea01f3dfab875932a49fbf07220788dce708186c2d`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_sc25_seed0.transitions.jsonl` rows=`40` sha256=`e6e8624bfa16eb6f81b2d57173ca60d744bab8da855e09a0b739c5deb45d0ea5`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_tn36_seed0.transitions.jsonl` rows=`40` sha256=`61c0f1fb21512bf64d048d0b8042201515dad6e2660f940be016a5ef6f225f79`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_tr87_seed0.transitions.jsonl` rows=`40` sha256=`4af65a74e95c97a9700da5e9dfc5928dcf35daaf714d1d3c1ee5f9ac44cc702f`
- `experiments/2026-05-04_v019b_target_discriminated_scorer_scout/grid/transition_events/v019b_current_state_v019b_target_discriminated_tu93_seed0.transitions.jsonl` rows=`40` sha256=`718705c433a2b5d40b48f40f2758e606b769e49572f020923a6e1d714b5a88e1`

## Validation

- valid: `True`
- records: `400`
- errors: `0`
- progress records: `1`
- positive signed-outcome records: `274`
- negative signed-outcome records: `126`

## Labels

- progress labels: `{'no_level_progress': 399, 'progress_level_delta_positive': 1}`
- control labels: `{'dominant_group:goal_progress': 1, 'dominant_group:stasis_loop': 76, 'dominant_group:time_phase': 16, 'dominant_group:translation': 257, 'stasis_no_change': 50}`
