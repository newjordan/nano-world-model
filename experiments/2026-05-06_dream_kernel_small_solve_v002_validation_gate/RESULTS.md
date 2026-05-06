# Dream Kernel Small Solve V001 Results

Status: deterministic small solve suite. No training data promoted.

## Condition

- run label: `dream_kernel_small_solve_v002_validation_gate`
- run kind: `deterministic_dream_kernel_small_solve_no_training`
- run label semantics: `new_experiment`
- git commit: `f7c19b0041516fccdf54234b4e58fa3298c9aef9`
- git dirty at run: `True`
- script: `scripts/run_dream_kernel_small_solve.py`
- kernel main: `dream_kernel/src/main.rs`
- kernel lib: `dream_kernel/src/lib.rs`
- metric: `terminal_goal_pass_rate`

## Summary

- scenarios: `4`
- solved: `4`
- failed: `0`
- pass rate: `1.000000`
- invariant pass rate: `1.000000`
- accepted step rate: `1.000000`
- branch-rank top-match count: `1`

## Scenarios

| scenario | solved | steps | reward | terminal | rejected | branch top match | actions | sequence |
| --- | --- | ---: | ---: | --- | ---: | --- | --- | --- |
| direct_goal_two_step | True | 2 | 1 | True | 0 | True | `move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0` | `direct_goal_two_step.dream_sequence.json` |
| hazard_detour_goal | True | 5 | 1 | True | 0 | False | `move_entity_0_dx0_dy1_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx0_dy-1_dz0` | `hazard_detour_goal.dream_sequence.json` |
| wall_detour_goal | True | 5 | 1 | True | 0 | False | `move_entity_0_dx0_dy1_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx0_dy-1_dz0` | `wall_detour_goal.dream_sequence.json` |
| object_detour_goal | True | 5 | 1 | True | 0 | False | `move_entity_0_dx0_dy1_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx1_dy0_dz0,move_entity_0_dx0_dy-1_dz0` | `object_detour_goal.dream_sequence.json` |

## Interpretation

- This is a small deterministic check of the internal simulator/planner loop, not a learned-model benchmark.
- Passing means the kernel can simulate candidate futures, select actions, preserve object/ray identities, and terminate at goals in these maps.
- Branch-rank top-match is tracked separately because final whole-sequence branch ranking is not yet the same thing as stepwise action selection.
