# Dream Kernel Branch-Rank Calibration Goal V035

Status: goal artifact built from ARC-Dream proxy eval. No training data promoted.

This is not an ARC solve claim. It is a branch-value calibration target.

## Condition

- run label: `goal_v036_dream_kernel_branch_rank_zero_gate`
- git commit: `e9d72629452c38ed99bfc5847b11cd05c75eb678`
- git dirty at run: `True`
- source eval rows: `experiments/2026-05-06_arc_dream_curriculum_eval_v002_branch_value_projection_repair/curriculum_eval_rows.jsonl`
- training data promoted: `False`

## Goal

For every reachable solved ARC-Dream proxy map, the internal branch matrix must rank the terminal-positive branch first.

## Baseline

- proxy goal solve rate: `1.0`
- planner integrity pass rate: `1.0`
- branch-rank top-match rate: `1.0`
- terminal branch rank counts: `{'1': 96}`
- failure reasons: `{'passed_proxy_gate': 96}`

## Calibration Cases

- cases: `0`
- by tier: `{}`
- terminal rank before: `{}`
- rank-gap stats: `{'min': None, 'max': None, 'mean': None}`

## Stop Rule

`branch_rank_top_mismatch_count == 0 and proxy_goal_unreachable_in_projection_count == 0`
