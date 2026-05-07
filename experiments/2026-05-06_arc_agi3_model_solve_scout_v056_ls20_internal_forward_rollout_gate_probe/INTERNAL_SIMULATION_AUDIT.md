# Internal Simulation Audit: ls20 V056 Failure Probe

Run: `arc_agi3_model_solve_scout_v056_ls20_internal_forward_rollout_gate_probe`

## Verdict

This run did not build a real internal simulation.

It built a trusted 64x64 label-grid perception artifact, then failed closed before the actuator because the internal forward rollout could not bind an agent label, did zero rollout steps, and did not prove a full solution before the first action.

## What Exists

- `world_state_3d.json`
  - schema: `arc_agi3.world_state_3d.v001`
  - representation: `arc_frame_label_grid_3d_heightmap`
  - grid: 64x64, 4096 cells
  - grid sha256: `549403dc9a3e7d011a0ff9c5ebb9849956f85be627f428b9e0b098c217e0c65d`
  - labels: `0, 1, 3, 4, 5, 8, 9, 11, 12`
  - map perception gate: trusted, cell accuracy 1.0
  - ray gate: trusted, ray exact accuracy 1.0 over 32744 comparable rays

- `internal_forward_rollout_grid.txt`
  - a raw rendered label grid for the same perception surface.

- `internal_forward_rollout.json`
  - schema: `arc_agi3.internal_forward_rollout.v001`
  - candidate count: 4
  - actuator gate: failed
  - `kernel_supported`: false
  - `kernel_support_reason`: `missing_agent_label_mapping`
  - `solves_before_first_step`: false

- `dream_kernel_arc_grid_scout.json`
  - schema: `dream_kernel.arc_grid_scout.v001`
  - candidate count: 4
  - every candidate has:
    - `kernel_supported`: false
    - `prediction_supported`: false
    - `predicted_next_state`: `UNKNOWN`
    - `predicted_solved_by_plan`: false
    - `rollout_steps`: 0
    - `rollout_reason`: `missing_agent_label_mapping`

## What Is Missing

- `world_state_3d.json` has no entities.
  - entity count: 0
  - relations: 0
  - affordances: 0

- `branch_simulation.json` is empty.
  - candidate count: 0
  - selected candidate: null

- `nemo3_final_confirmation.json` is a placeholder.
  - confirmed: null
  - mode: null
  - verdict: null

- `mlp_consultation.json` is a placeholder.
  - action: null
  - decision source: null
  - selected candidate prediction: null

## Gate Block

`actuator_gate_block.json` blocked the run before any real ARC action:

`internal_forward_rollout.kernel_supported must be true before actuator step; internal_forward_rollout.solves_before_first_step must be true before actuator step; internal_forward_rollout.selected_candidate_prediction.prediction_supported must be true before actuator step; internal_forward_rollout.selected_candidate_prediction.predicted_solved_by_plan must be true before actuator step`

## Result

- valid model solve scout: false
- offline solve detected: false
- stop reason: `internal_solve_gate_blocked_before_actuator`
- selected actions: none
- actuator steps executed: 0
- MLP weights updated: false

## Bottom Line

The current gate prevented a fake action from being taken, which is good.

But the model did not produce the internal world-model simulation required for ARC. This was a perception/ray-grid artifact plus a fail-closed gate, not a solving internal model.
