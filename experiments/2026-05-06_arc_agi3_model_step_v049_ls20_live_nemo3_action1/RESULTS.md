# ARC-AGI-3 Standard Model Step Results

Status: one actuator step driven by a validated Nemo3/world-model ModelDecision artifact.

## Condition

- run label: `arc_agi3_model_step_v049_ls20_live_nemo3_action1`
- run kind: `arc_agi3_standard_model_flow_actuator_step`
- selected game: `ls20-9607627b`
- model decision: `experiments/2026-05-06_arc_agi3_model_decision_v048_ls20_live_nemo3_reset/model_decision.json`
- standard model flow: `['observation', 'world_state_3d', 'chronometric_game_knowledge', 'internal_branch_simulation', 'trust_checks', 'internal_thinking_lock', 'nemo3_final_confirmation', 'model_decision', 'actuator_step']`
- online submission: `False`
- ARC solve claim: `False`

## Metrics

- valid standard model-flow step: `True`
- decision id: `arc_agi3_model_decision_v048_ls20_live_nemo3_reset:187897f2c7f2b2bd`
- observation content match: `True`
- observation GUID match: `False`
- Nemo3 invoked: `True`
- action: `ACTION1:1`
- candidate action packets: `4`
- actuator steps executed: `1`
- levels completed: `0 -> 0`
- final state: `NOT_FINISHED`
