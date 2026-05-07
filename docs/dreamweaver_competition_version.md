# Dreamweaver Competition Version

Dreamweaver has two legal deployment lanes.

## Online / Community Lane

This lane is for ARC-AGI-3 `ONLINE` scorecards, shareable replays, and
community/unverified results.

- ARC mode: `ONLINE` or local `COMPETITION` scorecard runs.
- Nemo backend: OpenAI-compatible relay, NVIDIA-hosted endpoint, OpenRouter, or
  local vLLM.
- Secrets: loaded from environment or ignored local env files; never committed
  or written into proof bundles.
- Evidence: scorecard JSON, metrics, replay, trace, frame log, and checksums.

This is the lane used by
`dreamweaver_arc_agi3_online_scorecard_v001_ls20`.

## Kaggle Prize Lane

This lane is for the designated ARC Prize 2026 Kaggle competition package.

- ARC mode: `COMPETITION`.
- Internet: not available during evaluation.
- Nemo backend: must be local, bundled, or replaced by a deterministic/local
  confirmation module.
- Environments: the harness must handle all provided competition environments
  under the single-scorecard constraints.
- Hidden tasks: the agent must infer from observations; do not depend on local
  hidden environment source code.
- Reproducibility: all code and methods must be open sourced for prize
  eligibility.

## Required Refactor

1. Split Dreamweaver into a standalone package/repo with a small CLI:
   `dreamweaver run --mode online|competition --backend local|openai-compatible`.
2. Keep the ModelDecision contract as the public action boundary.
3. Add a provider interface for final confirmation:
   `LocalNemoBackend`, `OpenAICompatibleBackend`, and
   `DeterministicConfirmationBackend`.
4. Add an all-environment competition runner that opens one scorecard and calls
   `make` at most once per environment.
5. Keep the offline mirror only as a development/debug aid unless the
   competition rules and available files make it legal for the target lane.
6. Emit a redacted proof bundle for every run.

## Current Readiness

Ready now:

- `ls20` ONLINE scorecard solve.
- provider-style live relay URL already exists in the harness.
- scorecard and replay proof bundle generation.

Not yet ready:

- Kaggle no-internet packaging.
- all-environment competition loop.
- non-`ls20` general policy coverage.
- removal/replacement of source-env-dependent LS20 mirror logic for hidden
  evaluation.
