# ARC-AGI-3 Standard Model Step Results

Status: one actuator step driven by a validated Nemo3/world-model ModelDecision artifact.

## Condition

- run label: `arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local_step_053_actuator`
- run kind: `arc_agi3_model_solve_scout_actuator_step`
- selected game: `ls20-9607627b`
- model decision: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/053_model_decision/model_decision.json`
- standard model flow: `['observation', 'world_state_3d', 'chronometric_game_knowledge', 'mlp_consultation', 'internal_forward_rollout', 'internal_branch_simulation', 'trust_checks', 'internal_thinking_lock', 'nemo3_final_confirmation', 'model_decision', 'actuator_step']`
- online submission: `False`
- ARC solve claim: `False`

## Metrics

- valid standard model-flow step: `True`
- decision id: `arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local_step_053_decision:8fdd4522417c7e32`
- observation content match: `True`
- observation GUID match: `True`
- MLP consultation: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/053_model_decision/mlp_consultation.json`
- internal forward rollout: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/053_model_decision/internal_forward_rollout.json`
- solved before first step: `True`
- post-action MLP update: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/053_actuator_step/post_action_mlp_update.json`
- MLP weights updated: `False`
- Nemo3 invoked: `True`
- action: `ACTION2:2`
- candidate action packets: `4`
- actuator steps executed: `1`
- levels completed: `1 -> 1`
- final state: `NOT_FINISHED`
