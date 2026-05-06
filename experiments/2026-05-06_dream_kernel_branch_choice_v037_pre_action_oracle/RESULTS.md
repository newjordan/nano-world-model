# Dream Kernel Branch Choice V037 Results

Status: deterministic pre-action branch-choice scout. No training data promoted.

This is not an ARC solve claim. It checks whether the policy score emitted before each action matches a trusted-map shortest-safe-path oracle.

## Condition

- run label: `dream_kernel_branch_choice_v037_pre_action_oracle`
- run kind: `deterministic_dream_kernel_pre_action_branch_choice_smoke`
- git commit: `e9d72629452c38ed99bfc5847b11cd05c75eb678`
- git dirty at run: `True`
- source eval rows: `experiments/2026-05-06_arc_dream_curriculum_eval_v002_branch_value_projection_repair/curriculum_eval_rows.jsonl`
- source eval metrics: `experiments/2026-05-06_arc_dream_curriculum_eval_v002_branch_value_projection_repair/metrics.json`
- metric: `pre_action_policy_oracle_match_rate`
- selection uses oracle: `False`
- selection uses post-action labels: `False`
- training data promoted: `False`

## Metrics

- scenarios solved: `96/96`
- scenario invariants passed: `96/96`
- source passed proxy gate: `96/96`
- source branch-rank mismatches: `0`
- source unreachable projections: `0`
- decisions: `530`
- policy/oracle match rate: `0.9981132075471698`
- value/oracle match rate: `0.9943396226415094`

## By Tier

| tier | decisions | policy/oracle | value/oracle |
| --- | ---: | ---: | ---: |
| t1_local_translation | 72 | 1.0 | 1.0 |
| t2_action_coordinate | 120 | 1.0 | 1.0 |
| t3_object_relative_branching | 120 | 1.0 | 1.0 |
| t4_nonlocal_goal_hazard | 218 | 0.9954128440366973 | 0.9862385321100917 |
