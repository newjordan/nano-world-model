# Model Confirmation Backend Swap Note - 2026-05-06

## Candidate

- Repository: https://github.com/AEON-7/Gemma-4-26B-A4B-it-Uncensored-NVFP4
- Candidate backend name: `gemma4-aeon-uncensored` / `gemma4-fast` / `gemma4-deep`
- Reported shape: Gemma 4 MoE, 26B total parameters, about 4B active per token, top-8 of 128 experts.
- Reported serving target: DGX Spark / GB10, NVFP4 compressed-tensors, vLLM-compatible OpenAI-style serving path.
- Reported strengths relevant to our loop: native Gemma 4 tool calling, high JSON/extraction throughput, long context, and lower active-parameter cost than a dense 26B confirmation model.

## Why This Matters

The ARC loop must not hard-code Nemo as the only semantic confirmation backend. The model flow should require final confirmation, but the confirmation provider should be swappable:

`internal_world_model -> internal_forward_rollout -> branch_simulation -> internal_thinking_lock -> confirmation_backend -> ModelDecision -> actuator`

Nemo remains the current confirmation backend. Gemma 4 NVFP4 should be tested as an alternative backend for:

- Lower per-step latency in long action chains like the 311-step `ls20` live test.
- Higher reliability for compact JSON confirmations.
- Better cost/throughput under repeated short confirmation calls.
- Potential higher accuracy on ambiguous branch-review packets.

## Required Test Matrix

Run the same confirmation packet against Nemo and Gemma 4:

1. Reset-only ModelDecision confirmation.
2. 13-step live loop through the first level boundary.
3. Full 311-step live confirmation loop.
4. Ambiguous branch-selection packet requiring interim confirmation.
5. Malformed/hostile response robustness: fenced JSON, prose before JSON, missing `nemo_supplied_action`, wrong selected action, refusal text.

Track:

- p50/p95 confirmation latency.
- JSON parse success rate.
- selected-action agreement with internal lock.
- false rejection rate when source-world/Rust kernel proof is valid.
- false acceptance rate when selected action is intentionally perturbed.
- total wall-clock for 311 confirmations.

## Backend Abstraction Needed

Rename the implementation concept from `nemo3`-specific plumbing to a generic confirmation backend while preserving the artifact contract:

- Keep existing `nemo3_final_confirmation` schema for current compatibility until a schema migration is deliberate.
- Add configuration fields for `confirmation_backend_name`, `confirmation_backend_url`, `confirmation_backend_model`, and `confirmation_backend_kind`.
- The backend must never supply an action. It can only confirm or reject the internal locked action.
- The actuator gate should remain provider-agnostic: it should care that final confirmation is valid, not whether Nemo or Gemma produced it.

## Custom MoE Direction

A custom confirmation MoE may be appropriate after collecting Nemo-vs-Gemma traces. The useful routing split is not general chat; it is narrow ARC mental-loop work:

- Expert for strict JSON confirmation and schema repair.
- Expert for map/goal semantic consistency.
- Expert for action-sequence sanity checks.
- Expert for ambiguity review and open-question detection.
- Expert for refusal or uncertainty calibration.

The router should consume internal artifacts, not raw screenshots alone: source-world plan, Rust verifier summary, MLP priors, branch simulation, trust checks, and internal-thinking lock.

## Rule

The brain must be backend-flexible, but action ownership stays internal. Swapping Nemo for Gemma or a custom MoE must not weaken the rule that the internal world model solves and locks the decision before the actuator moves.
