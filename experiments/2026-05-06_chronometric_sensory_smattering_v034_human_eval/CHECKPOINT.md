# Dream Kernel Checkpoint 2026-05-06

Status: checkpointed foundation state for Dream Kernel V001/V003 review harness.

This checkpoint freezes the first working internal imagination surface:

- deterministic known-map Dream Kernel rollout
- stable object IDs and open categorical IDs
- ray contact identifiers and ray-network polarity
- lifted Chronometric Y-space potentials
- branch potentials and object-link hypotheses
- local Nemo relay confirmations
- human review/promote sidecar target
- Three.js harness served over Tailscale

No training data is promoted by this checkpoint.

## Source State

- checkpoint commit: `17fee93696d77a3b6ef9c39ad5e63e212dc18d53`
- harness URL: `https://dgx-spark.tail2d8af4.ts.net:19030/`
- sequence artifact: `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json`
- sequence schema: `dream_kernel.sequence.v003`
- sequence hash: `a8427cc307f07ffe`
- frames: `7`
- objects: `19`
- branches: `6`
- branch potentials: `73`
- object-link hypotheses: `144`
- Nemo open questions: `38`
- Nemo confirmations: `6/6 relay_ok=true`
- Nemo reviews: `0`

## Checkpoint Files

- `dream_kernel/`
- `scripts/launch_human_eval_harness.py`
- `scripts/run_dream_kernel_ablations.py`
- `docs/dream_kernel_v001.md`
- `tests/test_human_eval_harness.py`
- `tests/test_dream_kernel_ablations.py`
- `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json`
- `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/nemo_relay_confirmations.json`
- `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/nemo_relay_reviews.json`

## Ablation Data

Post-checkpoint ablation output:

- `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/condition.json`
- `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/metrics.json`
- `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/layer_value_rows.jsonl`
- `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/ablation_rows.jsonl`
- `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/object_value_rows.jsonl`
- `experiments/2026-05-06_dream_kernel_ablation_v001_value_layers/RESULTS.md`

Clean ablation condition:

- source commit: `17fee93696d77a3b6ef9c39ad5e63e212dc18d53`
- git dirty at run: `false`
- metric: `proxy_rank_preservation_and_value_density`
- run kind: `deterministic_dream_kernel_value_ablation_no_training`

## Ablation Readout

Highest value-density layer:

- `branch_matrix`

High-value layers:

- `branch_matrix`
- `nemo_confirmations`
- `rays`
- `object_registry_categories`
- `chrono_datapoints`
- `branch_potentials`

Low-density layers to target with sparse/gated attention first:

- `branch_potentials`
- `object_links`

Current low-value structural objects that can be skipped until stuck/uncertain:

- `wall:0:3:0`
- `wall:5:3:0`

## Compression Policy

Do not delete data just because it is dense. The safe first compression pass is:

1. Keep deterministic anchors always available:
   `branch_matrix`, `object_registry`, object IDs, and integrity hashes.
2. Gate branch potentials and object-link hypotheses behind uncertainty, stuck
   branches, or human/Nemo review demand.
3. Skip low-value structural walls only when they are not ray contacts,
   branch-risk/support objects, or terminal blockers for the current branch.
4. Rehydrate skipped low-value data immediately if the branch becomes stuck,
   uncertain, or contradictory.
5. Use human review labels before turning Nemo semantic confirmations into
   fine-tuning targets.

## Verification

```bash
python -m pytest tests/test_chronometric_sensory_smattering.py \
  tests/test_human_eval_harness.py \
  tests/test_chronometric_ab_overlay.py \
  tests/test_dream_kernel_ablations.py

cargo test --manifest-path dream_kernel/Cargo.toml

python scripts/run_dream_kernel_ablations.py
```
