# ARC-AGI-3 Standard Model Step Results

Status: one actuator step driven by a validated Nemo3/world-model ModelDecision artifact.

## Condition

- run label: `arc_agi3_model_solve_scout_v055_ls20_live_nemo3_mlp_loop_40_step_033_actuator`
- run kind: `arc_agi3_model_solve_scout_actuator_step`
- selected game: `ls20-9607627b`
- model decision: `experiments/2026-05-06_arc_agi3_model_solve_scout_v055_ls20_live_nemo3_mlp_loop_40/steps/033_model_decision/model_decision.json`
- standard model flow: `['observation', 'world_state_3d', 'chronometric_game_knowledge', 'mlp_consultation', 'internal_branch_simulation', 'trust_checks', 'internal_thinking_lock', 'nemo3_final_confirmation', 'model_decision', 'actuator_step']`
- online submission: `False`
- ARC solve claim: `False`

## Metrics

- valid standard model-flow step: `True`
- decision id: `arc_agi3_model_solve_scout_v055_ls20_live_nemo3_mlp_loop_40_step_033_decision:f46c63637e8e3628`
- observation content match: `True`
- observation GUID match: `True`
- MLP consultation: `experiments/2026-05-06_arc_agi3_model_solve_scout_v055_ls20_live_nemo3_mlp_loop_40/steps/033_model_decision/mlp_consultation.json`
- post-action MLP update: `experiments/2026-05-06_arc_agi3_model_solve_scout_v055_ls20_live_nemo3_mlp_loop_40/steps/033_actuator_step/post_action_mlp_update.json`
- MLP weights updated: `False`
- Nemo3 invoked: `True`
- action: `ACTION2:2`
- candidate action packets: `4`
- actuator steps executed: `1`
- levels completed: `0 -> 0`
- final state: `NOT_FINISHED`
