# ARC-AGI-3 Standard Model Step Results

Status: one actuator step driven by a validated Nemo3/world-model ModelDecision artifact.

## Condition

- run label: `arc_agi3_model_step_v051_ls20_live_nemo3_mlp_action`
- run kind: `arc_agi3_standard_model_flow_actuator_step`
- selected game: `ls20-9607627b`
- model decision: `experiments/2026-05-06_arc_agi3_model_decision_v050_ls20_live_nemo3_mlp_reset/model_decision.json`
- standard model flow: `['observation', 'world_state_3d', 'chronometric_game_knowledge', 'mlp_consultation', 'internal_branch_simulation', 'trust_checks', 'internal_thinking_lock', 'nemo3_final_confirmation', 'model_decision', 'actuator_step']`
- online submission: `False`
- ARC solve claim: `False`

## Metrics

- valid standard model-flow step: `True`
- decision id: `arc_agi3_model_decision_v050_ls20_live_nemo3_mlp_reset:e7bef13fe9fdc728`
- observation content match: `True`
- observation GUID match: `False`
- MLP consultation: `experiments/2026-05-06_arc_agi3_model_decision_v050_ls20_live_nemo3_mlp_reset/mlp_consultation.json`
- post-action MLP update: `experiments/2026-05-06_arc_agi3_model_step_v051_ls20_live_nemo3_mlp_action/post_action_mlp_update.json`
- MLP weights updated: `False`
- Nemo3 invoked: `True`
- action: `ACTION3:3`
- candidate action packets: `4`
- actuator steps executed: `1`
- levels completed: `0 -> 0`
- final state: `NOT_FINISHED`
