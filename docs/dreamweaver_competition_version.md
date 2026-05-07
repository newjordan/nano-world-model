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

Saved proof bundle:

- `packages/dreamweaver_scorecard_v001_ls20/`
- `packages/dreamweaver_scorecard_v001_ls20_proof_bundle.tar.gz`
- scorecard id: `2b9edcf3-69e6-48c0-9df2-4fb0428a19c5`
- result: `100.0`, `7 / 7` levels, `311` actions, final state `WIN`
- official ARC solve claim: `false` because this was `ONLINE`, not Kaggle
  `COMPETITION`

## Kaggle Prize Lane

This lane is for the designated ARC Prize 2026 Kaggle competition package.

- ARC mode: `COMPETITION`.
- Internet: not available during evaluation.
- Nemo backend: external APIs are not prize-eligible; confirmation must be
  local, bundled, or replaced by a deterministic/local confirmation module.
- Environments: the harness must handle all provided competition environments
  under the single-scorecard constraints.
- Hidden tasks: the agent must infer from observations; do not depend on local
  hidden environment source code.
- Reproducibility: all code and methods must be open sourced for prize
  eligibility.

Run the executable gate before treating any package as Kaggle-prize ready:

```bash
python scripts/build_dreamweaver_competition_manifest.py \
  --config path/to/dreamweaver_competition_config.json \
  --out path/to/dreamweaver_competition_manifest.json \
  --require-kaggle-eligible
```

The saved ONLINE proof can be classified without claiming prize eligibility:

```bash
python scripts/build_dreamweaver_competition_manifest.py \
  --from-online-scorecard-metrics packages/dreamweaver_scorecard_v001_ls20/metrics.json \
  --out packages/dreamweaver_scorecard_v001_ls20/competition_preflight_manifest.json
```

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

Executable guard now in place:

- `src/dreamweaver_competition.py`
- `scripts/build_dreamweaver_competition_manifest.py`
- `tests/test_dreamweaver_competition.py`

The guard fails closed for Kaggle if a config uses an external API backend,
requires internet, uses an offline mirror, uses the LS20 source-env solver, runs
only one game, opens more than one scorecard, calls `make` more than once per
environment, reads inflight scorecard state, depends on API-key secrets, lacks
requirements, or is not open-source ready.

## No-Submit Safety Rule

Do not submit, upload, or publish a Kaggle package unless:

- `kaggle_prize_eligible` is `true` in the manifest.
- `package_audit.secret_scan_clean` is `true`.
- `package_audit.secret_findings` is empty.
- `package_audit.external_network_markers` is empty.

The current saved LS20 scorecard proof remains local ONLINE/community evidence.
It is not a Kaggle prize submission.

## Prize Runner Mechanics

The no-internet mechanics runner is now split from the ONLINE scout:

- `src/dreamweaver_prize_runner.py`
- `scripts/run_dreamweaver_kaggle_prize_dryrun.py`
- `tests/test_dreamweaver_prize_runner.py`

It enforces:

- one scorecard;
- all available environments;
- one `make` per environment;
- no inflight `get_scorecard`;
- local confirmation only;
- no offline mirror;
- no source-env solver;
- fail-closed blocking for complex actions that lack required `data`.

Latest local mechanics dry-run:

- run dir:
  `experiments/2026-05-07_dreamweaver_kaggle_prize_offline_mechanics_dryrun_v004/`
- operation mode: `OFFLINE` mechanics dry-run, not official submission
- available games: `11`
- all environments attempted: `true`
- one `make` per environment: `true`
- scorecard reads during run: `false`
- external API used: `false`
- source-env solver used: `false`
- offline mirror used: `false`
- actions executed: `9`
- blocked before invalid action data on `ft09` and `tn36`

The corresponding preflight manifest against the whole `src/` tree is still
not prize eligible because that broad tree includes network-capable utilities
and is not a minimal Kaggle package:

- `experiments/2026-05-07_dreamweaver_kaggle_prize_offline_mechanics_dryrun_v004/prize_preflight_manifest_src_scan.json`
