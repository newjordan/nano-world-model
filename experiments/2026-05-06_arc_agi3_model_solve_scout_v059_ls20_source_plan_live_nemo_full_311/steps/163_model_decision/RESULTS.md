# ARC-AGI-3 ModelDecision Producer V047 Results

Status: reset-only ModelDecision artifact production. No ARC actuator step, no online submission, no score claim.

## Condition

- run label: `arc_agi3_model_solve_scout_v059_ls20_source_plan_live_nemo_full_311_step_163_decision`
- run kind: `arc_agi3_model_solve_scout_decision_step`
- source condition: `docs/arc-agi-3-env.md`
- environments dir: `environment_files`
- operation mode: `OFFLINE`
- selected game: `ls20-9607627b`
- Nemo mode: `live-relay`
- metric: `arc_agi3_valid_model_decision_artifact_and_zero_actuator_steps`
- ARC solve claim: `False`
- online submission: `False`

## Metrics

- valid standard ModelDecision: `True`
- model decision: `experiments/2026-05-06_arc_agi3_model_solve_scout_v059_ls20_source_plan_live_nemo_full_311/steps/163_model_decision/model_decision.json`
- action source: `world_model_internal_thinking`
- selected action: `ACTION3:3`
- candidate action packets: `4`
- world-state surface: `chronometric_frame_grid_to_3d_world_state_v047`
- object anchors: `4088`
- rays: `32704`
- chronometric score surface: `NanoWM.score_chronometric_branch`
- MLP consultation: `experiments/2026-05-06_arc_agi3_model_solve_scout_v059_ls20_source_plan_live_nemo_full_311/steps/163_model_decision/mlp_consultation.json`
- MLP candidate priors: `4`
- MLP post-action update context count: `163`
- internal forward rollout: `experiments/2026-05-06_arc_agi3_model_solve_scout_v059_ls20_source_plan_live_nemo_full_311/steps/163_model_decision/internal_forward_rollout.json`
- dream kernel supported: `True`
- solved before first step: `True`
- Nemo3 invoked: `True`
- Nemo3 confirmation mode: `live-relay`
- external Nemo3 model invoked: `True`
- interim Nemo confirmations: `0`
- actuator steps executed: `0`
