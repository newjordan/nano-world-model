# Dream Kernel CEM Rollout V038 Results

Status: CEM rollout-complexity smoke over trusted Dream Kernel proxy maps. No training data promoted.

This is not an ARC solve claim and not a trained NanoWM checkpoint eval. It uses the real CEMPlanner loop with a deterministic map rollout adapter.

## Condition

- run label: `dream_kernel_cem_rollout_v038_complexity_smoke`
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
- training data promoted: `False`

## Metrics

- source passed proxy gate: `96/96`
- source branch-rank mismatches: `0`
- source unreachable projections: `0`
- CEM solved: `94/96`
- CEM success rate: `0.9791666666666666`
- mean final safe path steps: `0.07291666666666667`
- mean steps to goal: `6.8936170212765955`
- mean extra steps to goal: `1.4680851063829787`
- hazard hits: `0`
- blocked steps: `118`

## By Tier

| tier | rows | solved | success | mean final safe path | mean extra steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| t1_local_translation | 24 | 24 | 1.0 | 0.0 | 0.0 |
| t2_action_coordinate | 24 | 24 | 1.0 | 0.0 | 0.5 |
| t3_object_relative_branching | 24 | 24 | 1.0 | 0.0 | 0.125 |
| t4_nonlocal_goal_hazard | 24 | 22 | 0.9166666666666666 | 0.2916666666666667 | 5.590909090909091 |
