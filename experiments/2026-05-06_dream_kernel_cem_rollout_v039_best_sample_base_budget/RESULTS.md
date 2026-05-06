# Dream Kernel CEM Rollout V038 Results

Status: CEM rollout-complexity smoke over trusted Dream Kernel proxy maps. No training data promoted.

This is not an ARC solve claim and not a trained NanoWM checkpoint eval. It uses the real CEMPlanner loop with a deterministic map rollout adapter.

## Condition

- run label: `dream_kernel_cem_rollout_v039_best_sample_base_budget`
- run kind: `dream_kernel_cem_rollout_complexity_smoke`
- git commit: `e9d72629452c38ed99bfc5847b11cd05c75eb678`
- git dirty at run: `True`
- source eval rows: `experiments/2026-05-06_arc_dream_curriculum_eval_v003_safe_path_progress_regate/curriculum_eval_rows.jsonl`
- metric: `cem_goal_success_rate_and_mean_final_safe_distance`
- seed: `20260506`
- horizon: `16`
- num samples: `128`
- topk: `16`
- opt steps: `8`
- return policy: `best_sample`
- training data promoted: `False`

## Metrics

- source passed proxy gate: `96/96`
- source branch-rank mismatches: `0`
- source unreachable projections: `0`
- CEM solved: `96/96`
- CEM success rate: `1.0`
- mean final safe path steps: `0.0`
- mean steps to goal: `7.604166666666667`
- mean extra steps to goal: `2.1041666666666665`
- hazard hits: `0`
- blocked steps: `36`

## By Tier

| tier | rows | solved | success | mean final safe path | mean extra steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| t1_local_translation | 24 | 24 | 1.0 | 0.0 | 1.875 |
| t2_action_coordinate | 24 | 24 | 1.0 | 0.0 | 1.25 |
| t3_object_relative_branching | 24 | 24 | 1.0 | 0.0 | 0.5416666666666666 |
| t4_nonlocal_goal_hazard | 24 | 24 | 1.0 | 0.0 | 4.75 |
