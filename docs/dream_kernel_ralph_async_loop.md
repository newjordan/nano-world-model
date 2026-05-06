# Dream Kernel Ralph Async Loop

Status: async buildout runbook for Dream Kernel / chronometric world-model improvements.

This document is for an independent agent running focused improvement loops in
`/home/frosty40/nano-world-model`. Work from current repo state. Do not revert
other people's edits. Before changing code, run `git status --short` and treat
dirty files as owned by someone else unless the user explicitly assigns them.

## Grounded Surfaces

- Dream Kernel crate: `dream_kernel/Cargo.toml`, `dream_kernel/src/lib.rs`,
  `dream_kernel/src/main.rs`.
- Deterministic kernel commands:
  - `cargo test --manifest-path dream_kernel/Cargo.toml`
  - `cargo run --manifest-path dream_kernel/Cargo.toml -- demo`
  - `cargo run --manifest-path dream_kernel/Cargo.toml -- solve-suite --out-dir experiments/<run_id>`
- Lab wrappers:
  - `scripts/run_dream_kernel_small_solve.py`
  - `scripts/run_dream_kernel_ablations.py`
  - `scripts/run_chronometric_sensory_smattering.py`
  - `scripts/launch_human_eval_harness.py`
- Existing Dream Kernel artifacts:
  - `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json`
  - `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/`
  - `experiments/2026-05-06_dream_kernel_small_solve_v001/` if present after the small-solve wrapper.
- Contract docs:
  - `docs/dream_kernel_v001.md`
  - `docs/chronometric_outcome_imagination_v033.md`
  - `docs/chronometric_sensory_smattering_v034.md`
  - `docs/chronometric_testing.md`

## Global Rules

- Preserve data integrity. Every new experiment directory must contain
  `condition.json`, `metrics.json`, and `RESULTS.md`, plus hashes or source
  artifact paths where available.
- No training data promotion. Keep `training_data_promoted: false` unless the
  user gives a separate promotion condition.
- Do not smuggle observed outcome into pre-action imagination. Keep
  `imagined_*` and `observed_*` fields separated.
- Do not overwrite existing experiment directories. Use a dated run ID such as
  `experiments/2026-05-06_dream_kernel_<lane>_vXXX_<short_name>`.
- Stop before broad refactors. Touch only the files needed for the active lane.
- If `git status --short` shows files you did not touch in the lane, leave them
  alone and report them as pre-existing.

## Priority Order

1. Small-solve reliability and branch-rank correctness.
2. Sequence integrity and schema validation.
3. Chronometric value ablation signal quality.
4. Human/Nemo review loop hardening.
5. Known-map provenance and partial-observation intake.
6. Planner-facing chronometric bridge integration.
7. Performance and artifact size.

## Lane 1: Small-Solve Reliability

Objective: make the deterministic `solve-suite` a dependable regression gate
for internal planning, not just demo JSON export.

Primary files:

- `dream_kernel/src/main.rs`
- `dream_kernel/src/lib.rs`
- `scripts/run_dream_kernel_small_solve.py`
- add or update targeted tests under `tests/` only if this lane owns them.

Baseline commands:

```bash
git status --short
cargo test --manifest-path dream_kernel/Cargo.toml
python scripts/run_dream_kernel_small_solve.py \
  --run-label dream_kernel_small_solve_vXXX_<short_name> \
  --out-dir experiments/2026-05-06_dream_kernel_small_solve_vXXX_<short_name>
```

Gate:

- `cargo test` passes.
- Small-solve `metrics.json` reports `pass_rate == 1.0`.
- `invariant_pass_rate == 1.0`.
- No scenario solves by stepping through hazards or walls.
- `branch_rank_top_match_count` is explained in `RESULTS.md`; if it is not all
  scenarios, either fix ranking or record why stepwise choice and final sequence
  ranking legitimately differ.

Stop rules:

- Stop if solving requires loosening collision, terminal, object-ID, or
  invariant checks.
- Stop if the wrapper reports `git_dirty: true` from unrelated files and the
  result would be used as a clean comparator.

## Lane 2: Sequence Integrity And Schema Validation

Objective: make `dream_kernel.sequence.v003` self-checking enough that review,
ablation, and planner consumers can fail closed on malformed sequences.

Primary files:

- `dream_kernel/src/lib.rs`
- `scripts/run_dream_kernel_ablations.py`
- `tests/test_dream_kernel_ablations.py`
- `tests/test_human_eval_harness.py`

Baseline commands:

```bash
cargo test --manifest-path dream_kernel/Cargo.toml
mkdir -p experiments/2026-05-06_dream_kernel_schema_vXXX_<short_name>
cargo run --manifest-path dream_kernel/Cargo.toml -- demo \
  --out experiments/2026-05-06_dream_kernel_schema_vXXX_<short_name>/dream_sequence.json
python scripts/run_dream_kernel_ablations.py \
  --sequence experiments/2026-05-06_dream_kernel_schema_vXXX_<short_name>/dream_sequence.json \
  --out-dir experiments/2026-05-06_dream_kernel_ablation_vXXX_<short_name>
python -m pytest tests/test_dream_kernel_ablations.py tests/test_human_eval_harness.py
```

Gate:

- Sequence `integrity.invariant_passed` is true.
- Every ray contact, potential datum, branch potential, object-link hypothesis,
  and Nemo relay question references an existing stable object, branch, or
  hypothesis ID.
- Frame hashes chain deterministically and `sequence_hash` changes when
  material rollout content changes.
- Consumers reject missing `frames`, missing `object_registry`, unknown branch
  IDs, and out-of-range probabilities.

Stop rules:

- Stop if validation requires accepting unknown object IDs silently.
- Stop if schema changes are not backwards-readable by current
  `scripts/launch_human_eval_harness.py` and `scripts/run_dream_kernel_ablations.py`.

## Lane 3: Chronometric Value Ablation Signal

Objective: turn `scripts/run_dream_kernel_ablations.py` into a useful value
density diagnostic for deciding which Dream Kernel layers matter.

Primary files:

- `scripts/run_dream_kernel_ablations.py`
- `tests/test_dream_kernel_ablations.py`
- optional follow-up docs only after metrics are stable.

Baseline commands:

```bash
python scripts/run_dream_kernel_ablations.py \
  --sequence experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json \
  --confirmations experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/nemo_relay_confirmations.json \
  --reviews experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/nemo_relay_reviews.json \
  --run-label dream_kernel_ablation_vXXX_<short_name> \
  --out-dir experiments/2026-05-06_dream_kernel_ablation_vXXX_<short_name>
python -m pytest tests/test_dream_kernel_ablations.py
```

Gate:

- `condition.json` includes hashes for the script, sequence, confirmations, and
  reviews when those files exist.
- `metrics.json` reports source counts, layer rows, ablation rows, object value
  rows, and compression summary.
- High-value layer claims are tied to rank preservation, branch-score delta, or
  object-criticality evidence, not just payload byte counts.
- `RESULTS.md` states whether the run is a posthoc analysis and keeps
  `training_data_promoted: false`.

Stop rules:

- Stop if the ablation has to infer missing confirmations or reviews as
  positive evidence.
- Stop if a layer-removal result changes branch ranking but the report does not
  identify the affected branch IDs.

## Lane 4: Human/Nemo Review Loop

Objective: harden the review surface that loads `dream_sequence.json`, sends
branch-local Nemo packets, and saves human/Nemo sidecars without contaminating
deterministic kernel artifacts.

Primary files:

- `scripts/launch_human_eval_harness.py`
- `tests/test_human_eval_harness.py`
- `experiments/<run_id>/human_labels.json`
- `experiments/<run_id>/nemo_relay_confirmations.json`
- `experiments/<run_id>/nemo_relay_reviews.json`

Baseline commands:

```bash
python scripts/run_chronometric_sensory_smattering.py \
  --run-label chronometric_sensory_smattering_vXXX_<short_name> \
  --out-dir experiments/2026-05-06_chronometric_sensory_smattering_vXXX_<short_name>
mkdir -p experiments/2026-05-06_chronometric_sensory_smattering_vXXX_<short_name>
cargo run --manifest-path dream_kernel/Cargo.toml -- demo \
  --out experiments/2026-05-06_chronometric_sensory_smattering_vXXX_<short_name>/dream_sequence.json
python -m pytest tests/test_human_eval_harness.py
python scripts/launch_human_eval_harness.py \
  --experiment experiments/2026-05-06_chronometric_sensory_smattering_vXXX_<short_name> \
  --host 127.0.0.1 --port 8765
```

Gate:

- Harness loads a missing Nemo sidecar as an empty schema-valid object.
- Saved labels append JSONL events and update markdown summaries.
- Nemo review promotion flags only copy reviewed evidence into
  `promoted_evidence`; they do not mutate `dream_sequence.json`.
- Branch packets include only branch-local potentials, object links, and open
  questions for the selected branch.

Stop rules:

- Stop if a Nemo response is written directly into the Dream Kernel sequence.
- Stop if review labels are accepted for unknown `case_id` or `branch_id`.

## Lane 5: Known-Map Provenance And Partial Observation

Objective: prepare Dream Kernel for perception-fed maps while preserving the
contract that unknown perception must be converted into explicit known-map
cells with provenance before simulation.

Primary files:

- `dream_kernel/src/lib.rs`
- future ingest script under `scripts/` only after the condition schema is
  defined.
- tests that exercise explicit provenance and fail on missing provenance.

Baseline commands:

```bash
cargo test --manifest-path dream_kernel/Cargo.toml
cargo run --manifest-path dream_kernel/Cargo.toml -- demo
```

Gate:

- Every non-empty map cell and dynamic entity has a source, confidence,
  category, open tags, and stable `object_id`.
- Partial-observation cells remain separate from confirmed known-map cells.
- Ray contacts and potentials reference the registry rather than inventing a
  second object authority.
- Unknown categories use open labels such as `object.unknown.open`; they are
  never forced into closed labels for convenience.

Stop rules:

- Stop if provenance is optional for perception-fed cells.
- Stop if a partial-observation path can create terminal rewards without an
  explicit source artifact.

## Lane 6: Planner-Facing Chronometric Bridge

Objective: connect Dream Kernel branch outputs to existing chronometric planner
scoring without turning the deterministic simulator into a training claim.

Primary files:

- `src/chronometric_bridge.py`
- `src/chronometric_planner_scoring.py`
- `scripts/score_chronometric_planner_branches.py`
- `scripts/build_arc_bridge_manifest.py` only if the bridge schema requires it.

Baseline commands:

```bash
python scripts/chronometric_mechanics_smoke.py --device auto
python scripts/score_chronometric_planner_branches.py \
  --run-label chronometric_planner_branch_score_vXXX_<short_name> \
  --out-dir experiments/2026-05-06_chronometric_planner_branch_score_vXXX_<short_name>
```

Gate:

- Dream Kernel branch rows map cleanly to planner fields:
  `event_mu`, `branch_direction_n`, `potential_family_vector`,
  `signed_outcome_y`, `action_context`, and branch IDs.
- Bridge artifacts preserve `source_repo`, `source_commit`,
  `source_artifact_path`, `source_condition_artifact`, `split`, and
  quarantine/provenance status.
- Results are labeled as planner-branch scoring smoke or deterministic bridge
  diagnostics, not ARC solve claims.

Stop rules:

- Stop if ARC-derived rows are mixed with Dream Kernel rows without explicit
  source and split separation.
- Stop if any heldout labels are used in branch scoring as features.

## Lane 7: Performance And Artifact Size

Objective: keep Dream Kernel sequences cheap enough for repeated review and
ablation while preserving inspectability.

Primary files:

- `dream_kernel/src/lib.rs`
- `scripts/run_dream_kernel_ablations.py`
- `scripts/launch_human_eval_harness.py`

Baseline commands:

```bash
cargo test --manifest-path dream_kernel/Cargo.toml
cargo run --manifest-path dream_kernel/Cargo.toml -- solve-suite \
  --out-dir experiments/2026-05-06_dream_kernel_perf_vXXX_<short_name>
python scripts/run_dream_kernel_ablations.py \
  --sequence experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json \
  --out-dir experiments/2026-05-06_dream_kernel_perf_ablation_vXXX_<short_name>
```

Gate:

- Sequence size, frame count, ray count, potential count, branch potential
  count, and object-link count are reported.
- Compression or pruning keeps enough fields for integrity validation, human
  review, branch ranking, and Nemo packet reconstruction.
- Large object-link sets are bounded deterministically by value/correlation,
  with retained IDs stable across reruns.

Stop rules:

- Stop if size reduction removes provenance, object IDs, event coordinates, or
  hash-chain inputs.
- Stop if pruning changes branch ranking without an explicit ablation row.

## Final Report Template

Each async lane should finish with:

- files changed.
- pre-existing dirty files ignored.
- commands run and pass/fail status.
- new experiment directory and key metrics.
- unresolved risks and the exact next lane to run.
