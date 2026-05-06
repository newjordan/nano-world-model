# ARC-AGI-3 Closed-Loop V042 Results

Status: local/offline ARC-AGI-3 closed-loop smoke. No online submission, no score claim, no training data promoted.

## Condition

- run label: `arc_agi3_closed_loop_v042_ls20_repeat_capped_cycle`
- run kind: `arc_agi3_closed_loop_offline_policy_smoke`
- source condition: `docs/arc-agi-3-env.md`
- environments dir: `environment_files`
- operation mode: `OFFLINE`
- selected game: `ls20-9607627b`
- policy: `repeat_capped_cycle`
- max steps: `40`
- max repeat: `2`
- metric: `arc_agi3_offline_closed_loop_level_progress_and_trace_validity`
- historical comparator: `arc_agi3_io_v041_offline_smoke`
- training data promoted: `False`
- ARC solve claim: `False`
- online submission: `False`

## Metrics

- valid closed-loop smoke: `True`
- available games: `11`
- trace rows: `40`
- candidate action packets: `160`
- steps executed: `40`
- frame shapes: `[[64, 64]]`
- unique frame hashes: `41`
- changed/no-change steps: `40/0`
- action count range: `4..4`
- action counts: `{'ACTION1:1': 10, 'ACTION2:2': 10, 'ACTION3:3': 10, 'ACTION4:4': 10}`
- states observed: `['NOT_FINISHED']`
- levels completed: `0 -> 0`
- max levels completed: `0`
- win levels: `7`
- final state: `NOT_FINISHED`
- local environment win: `False`
