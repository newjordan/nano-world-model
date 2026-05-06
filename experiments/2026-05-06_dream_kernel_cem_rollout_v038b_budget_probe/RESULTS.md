# Dream Kernel CEM Rollout V038 Results

Status: CEM rollout-complexity smoke over trusted Dream Kernel proxy maps. No training data promoted.

This is not an ARC solve claim and not a trained NanoWM checkpoint eval. It uses the real CEMPlanner loop with a deterministic map rollout adapter.

## Condition

- run label: `dream_kernel_cem_rollout_v038b_budget_probe`
- run kind: `dream_kernel_cem_rollout_complexity_smoke`
- git commit: `e9d72629452c38ed99bfc5847b11cd05c75eb678`
- git dirty at run: `True`
- source eval rows: `experiments/2026-05-06_arc_dream_curriculum_eval_v003_safe_path_progress_regate/curriculum_eval_rows.jsonl`
- metric: `cem_goal_success_rate_and_mean_final_safe_distance`
- seed: `20260506`
- horizon: `18`
- num samples: `512`
- topk: `64`
- opt steps: `12`
- training data promoted: `False`

## Metrics

- source passed proxy gate: `96/96`
- source branch-rank mismatches: `0`
- source unreachable projections: `0`
- CEM solved: `95/96`
- CEM success rate: `0.9895833333333334`
- mean final safe path steps: `0.11458333333333333`
- mean steps to goal: `6.663157894736842`
- mean extra steps to goal: `1.2`
- hazard hits: `0`
- blocked steps: `67`

## By Tier

| tier | rows | solved | success | mean final safe path | mean extra steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| t1_local_translation | 24 | 24 | 1.0 | 0.0 | 0.0 |
| t2_action_coordinate | 24 | 24 | 1.0 | 0.0 | 0.0 |
| t3_object_relative_branching | 24 | 24 | 1.0 | 0.0 | 0.0 |
| t4_nonlocal_goal_hazard | 24 | 23 | 0.9583333333333334 | 0.4583333333333333 | 4.956521739130435 |
