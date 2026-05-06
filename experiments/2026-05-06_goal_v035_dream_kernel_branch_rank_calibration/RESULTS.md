# Dream Kernel Branch-Rank Calibration Goal V035

Status: goal artifact built from ARC-Dream proxy eval. No training data promoted.

This is not an ARC solve claim. It is a branch-value calibration target.

## Condition

- run label: `goal_v035_dream_kernel_branch_rank_calibration`
- git commit: `adbfe9e54957dda1c6f7de4d00ee381e14bd76ad`
- git dirty at run: `True`
- source eval rows: `experiments/2026-05-06_arc_dream_curriculum_eval_v001_v017_support_scout/curriculum_eval_rows.jsonl`
- training data promoted: `False`

## Goal

For every reachable solved ARC-Dream proxy map, the internal branch matrix must rank the terminal-positive branch first.

## Baseline

- proxy goal solve rate: `0.9895833333333334`
- planner integrity pass rate: `0.4895833333333333`
- branch-rank top-match rate: `0.4895833333333333`
- terminal branch rank counts: `{'1': 23, '3': 24, '5': 48, 'none': 1}`
- failure reasons: `{'branch_rank_top_mismatch': 48, 'passed_proxy_gate': 47, 'proxy_goal_unreachable_in_projection': 1}`

## Calibration Cases

- cases: `48`
- by tier: `{'t2_action_coordinate': 24, 't3_object_relative_branching': 24}`
- terminal rank before: `{'5': 48}`
- rank-gap stats: `{'min': 0.406575, 'max': 0.656575, 'mean': 0.531575}`

## Stop Rule

`branch_rank_top_mismatch_count == 0 and proxy_goal_unreachable_in_projection_count == 0`
