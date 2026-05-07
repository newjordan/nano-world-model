# ARC-AGI-3 Standard Model Step Results

Status: one actuator step driven by a validated Nemo3/world-model ModelDecision artifact.

## Condition

- run label: `arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local_step_078_actuator`
- run kind: `arc_agi3_model_solve_scout_actuator_step`
- selected game: `ls20-9607627b`
- model decision: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/078_model_decision/model_decision.json`
- standard model flow: `['observation', 'world_state_3d', 'chronometric_game_knowledge', 'mlp_consultation', 'internal_forward_rollout', 'internal_branch_simulation', 'trust_checks', 'internal_thinking_lock', 'nemo3_final_confirmation', 'model_decision', 'actuator_step']`
- online submission: `False`
- ARC solve claim: `False`

## Metrics

- valid standard model-flow step: `True`
- decision id: `arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local_step_078_decision:01e02eb9c5c7eaff`
- observation content match: `True`
- observation GUID match: `True`
- MLP consultation: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/078_model_decision/mlp_consultation.json`
- internal forward rollout: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/078_model_decision/internal_forward_rollout.json`
- solved before first step: `True`
- post-action MLP update: `experiments/2026-05-06_arc_agi3_model_solve_scout_v057_ls20_source_plan_full_local/steps/078_actuator_step/post_action_mlp_update.json`
- MLP weights updated: `False`
- Nemo3 invoked: `True`
- action: `ACTION3:3`
- candidate action packets: `4`
- actuator steps executed: `1`
- levels completed: `2 -> 2`
- final state: `NOT_FINISHED`
