# ARC Dream Curriculum Eval V001 Results

Status: deterministic Dream Kernel proxy curriculum eval. No training data promoted.

This is not an ARC solve claim. It tests projected known-map simulation, ray/object integrity, branch ranking, and Nemo relay availability.

## Condition

- run label: `arc_dream_curriculum_eval_v001_v017_support_scout`
- run kind: `deterministic_arc_dream_curriculum_proxy_eval_no_training`
- git commit: `01e9095c6c3ac04622d27121bf8ef3a8ae995948`
- git dirty at run: `True`
- curriculum: `experiments/2026-05-06_arc_dream_curriculum_v001_v017_support_scout/curriculum_challenges.jsonl`
- challenges: `96`
- max steps: `16`
- training data promoted: `False`

## Overall

- proxy goal solved: `95/96`
- proxy goal solve rate: `0.989583`
- proxy goal reachable avoiding hazard: `95/96`
- planner integrity pass rate: `0.489583`
- invariant pass rate: `1.000000`
- object identity pass rate: `1.000000`
- branch-rank top-match rate: `0.489583`
- terminal branch rank counts: `{'1': 23, '3': 24, '5': 48, 'none': 1}`
- accepted step rate: `1.000000`
- Nemo callback policy required: `72`
- kernel Nemo relay required: `96`

## By Tier

| tier | count | reachable | solve rate | planner pass | branch top match | rejected steps | Nemo policy required |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| t1_local_translation | 24 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0 | 0 |
| t2_action_coordinate | 24 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0 | 24 |
| t3_object_relative_branching | 24 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0 | 24 |
| t4_nonlocal_goal_hazard | 24 | 0.958333 | 0.958333 | 0.958333 | 0.958333 | 0 | 24 |

## Failure Reasons

`{'branch_rank_top_mismatch': 48, 'passed_proxy_gate': 47, 'proxy_goal_unreachable_in_projection': 1}`

## Ray Networks

`{'adversarial': 47, 'beneficial': 214, 'neutral': 135, 'structural': 4652}`

## Interpretation

- `proxy_goal_solve_rate` means the Dream Kernel solved the projected map, not the source ARC task.
- `proxy_goal_reachable_avoiding_hazard` is a map-integrity preflight that treats walls, hazards, and objects as blockers.
- `planner_integrity_pass_rate` requires solve, invariant integrity, ubiquitous object IDs, and branch-rank top-match.
- Nemo remains a relay: callback needs are recorded, but the deterministic kernel action sequence is the evaluated driver.
