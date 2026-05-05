# ARC Bridge Manifest Smoke Results

Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.

This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.

## Condition

- run label: `arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family`
- run kind: `bridge_manifest_generation`
- generator commit: `668a042ea927552f551cbc0dbce053e656a85d98`
- generator dirty at run: `False`
- source repo: `https://github.com/newjordan/arc-agi-3-worldmodel.git`
- source commit: `9c850edf476bc5363a3c7de43b6d73f28a2eb5a8`
- source dirty at run: `True`
- source condition: `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md`
- output manifest: `experiments/2026-05-05_arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family/arc_bridge_manifest.jsonl`

## Source Artifacts

- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_dc22_seed0.transitions.jsonl` rows=`40` sha256=`dde6a33a74ae174d640010fce93e73092240e82b8162a3809879e2a1a87772b2`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_ft09_seed0.transitions.jsonl` rows=`40` sha256=`4a3de6dabe314431f19df2e2f214799030f13536bff71daadbb5c4436a19dc96`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_g50t_seed0.transitions.jsonl` rows=`40` sha256=`94ca730343d7ec9b54883cfe424a1630707679ea5a0cc57ddbfaa439ac8069a5`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_ka59_seed0.transitions.jsonl` rows=`40` sha256=`fe40924c22a04a942044db6766a6afe8f9fce92bb58fcb02788358f15b00b2fb`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_m0r0_seed0.transitions.jsonl` rows=`40` sha256=`7c44a79b80a4127be553e7af6053dc518f4e65bd3310dfc139d9da0be3e788c9`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_sb26_seed0.transitions.jsonl` rows=`40` sha256=`0bd8eb2dbee1327852fd1a6f4299de0f39be4adb743c517470fa375dec7c16ff`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_sc25_seed0.transitions.jsonl` rows=`40` sha256=`8f1d882fea55d6a7735edaa456b5dedde464de9747dbd575b801c7fef8e91a29`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_tn36_seed0.transitions.jsonl` rows=`40` sha256=`2370709abbe7671dd34ebd625128f81861f05ffca63b38110ecaf7fe85a4a1a7`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_tr87_seed0.transitions.jsonl` rows=`40` sha256=`cdf59f6127073b557e09eae2df30e9ce22e76147a44fa382a937f475c4cbd6cb`
- `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/grid/transition_events/v023_current_state_v023_mirror_hazard_tu93_seed0.transitions.jsonl` rows=`40` sha256=`31e27b2c3b81d699731865d1954d4e306f5917590c3c420b5ae354011ec095ee`

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
