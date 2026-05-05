# Chronometric Foundation Review V002

Status: design audit after the first NanoWM chronometric patch.

This document is intentionally stricter than `chronometric_contortion_foundation.md`.
The first patch installed a real differentiable layer. It did not finish the
foundation. Treat that patch as V0 anchor code, not as a validated world-model
architecture.

## Non-Negotiable Axioms

1. The 4D event state must be an explicit world-model state, not decorative
   hidden-token texture.
2. Time is a causal coordinate. It must enter `K(tau)` and branch scoring, not
   only act as a frame index.
3. The projector is a hard constraint. `u_mu F_cont^mu = 0` is enforced by
   construction and audited numerically.
4. `F_ext` must eventually come from observation/action context. A force head
   that reads only the same hidden token is a placeholder.
5. Branch direction `n^beta` must eventually be supplied or sampled as a
   planner branch object. A learned internal branch head is only a bootstrap.
6. Latent `y` is the signed outcome axis. It is separate from raw image/grid
   `y` and must be supervised by progress/loop/contradiction labels.
7. Potential families must become inspectable evidence channels. The learned
   family basis is not enough until it is tied to logged family activations.
8. Any promoted version needs controlled ablation against plain NanoWM under the
   same data, seed, horizon, hardware, and eval.

## What Is Installed Now

Commit `2eca55a` added:

- `src/models/chronometric_contortion.py`
- NanoWM temporal-token integration
- model-config knob `model.chronometric`
- hard time-like velocity normalization
- learned `K0`, `Kc`, `Ks` with log-time phase
- learned potential-family logits and basis
- signed outcome scalar `outcome_y`
- orthogonality/invariant metrics and test coverage

The current placement is:

```text
latent video tokens
  -> spatial transformer block
  -> temporal token stream
  -> chronometric residual update
  -> temporal transformer block
```

That is useful because it forces the model body to carry the chronometric
primitive. It is not yet enough to claim the model is reasoning in event space.

## Integration Status

The first integration pass adds the missing control surface:

- `model.chronometric.mode`
  - `audit`: compute chronometric state/metrics, no residual update
  - `residual_once`: apply one chronometric residual at the first temporal pass
  - `residual_each`: apply a residual before every temporal block
  - `branch_rollout`: compute branch geometry without changing tokens
- shifted NanoWM action embeddings are passed into the chronometric layer as
  `action_context`, so `F_ext` is no longer only a hidden-token projection
- supplied `branch_direction` tensors can override the learned branch head
- `score_branch(tokens, branch_direction, action_context=...)` exposes the
  event-geometry scorer without mutating the token stream
- audit mode returns identical NanoWM outputs to the same model with
  chronometric disabled while still recording metrics

The default model configs now use `mode: audit` so experiments must explicitly
opt into residual behavior.

## Current Gaps

### External Force

Earlier:

```text
F_ext = Linear(hidden_token)
```

Current integration:

```text
F_ext = Linear(hidden_token) + Linear(shifted_action_embedding)
```

Still needed:

```text
F_ext = f(observation_state, action, local_diff, history, optional branch context)
```

For ARC or any grid game, `F_ext` should be conditioned on action embeddings and
observed transition evidence. For video-only NanoWM, it should at least receive
the shifted action embedding already used by the temporal blocks.

### Branch Direction

Earlier:

```text
n = normalize(branch_head(hidden_token) + family_basis_mix)
```

Current integration:

```text
n = supplied_branch_direction if provided else learned_branch_head(...)
```

Still needed:

```text
n = branch candidate from planner / data source / sampled branch family
```

The learned `branch_head` is acceptable as a bootstrap, but MCTS and branch
rollouts require an interface where multiple candidate `n` values can be scored
from the same state.

### Signed Outcome Axis

Current:

```text
outcome_y = Linear(next_event)
```

Needed:

```text
event_mu.y supervised by signed potentials:
  positive: progress, unlocked possibility, contradiction reduction
  negative: stasis, loop, contradiction, hazard/dead branch
```

This needs labels from the harness data plane before it is meaningful. The
current scalar is only an instrumentation hook.

### Constraint Losses

The current invariant and orthogonality terms are hard-enforced by construction,
so their losses are mostly audit values rather than useful gradient drivers.
That is acceptable for a safety check, but the config should not pretend these
losses carry the main learning signal.

Future useful losses:

- raw/pre-projection orthogonality pressure
- next-event prediction loss
- signed outcome loss
- multi-step rollout stability loss
- sibling branch consistency loss
- family-flow supervision loss

### Application Frequency

Current NanoWM applies the same chronometric layer before every temporal block.
This is probably too blunt for ablation. We need modes:

- `audit`: compute event geometry and metrics, no residual update
- `residual_once`: apply once after first temporal setup
- `residual_each`: current behavior
- `branch_rollout`: expose event states for planner-side scoring

## Required Architecture Stages

### C0: Foundation Anchor

Goal: ensure the math exists in NanoWM and is testable.

Status: done in `2eca55a`.

Gate:

- algebra tests pass
- NanoWM forward path can enable the layer
- config path resolves chronometric settings

### C1: Audit Mode

Goal: separate instrumentation from behavior change.

Status: implemented.

Work:

- add `chronometric.mode: audit|residual_once|residual_each|branch_rollout`
- log event norms, phase, force RMS, family entropy, signed Y
- keep plain NanoWM output unchanged in audit mode

Gate:

- audit mode produces metrics with identical model output to disabled mode
- no training/eval claims yet

### C2: External Force Split

Goal: make `F_ext` actually mean observation/action force.

Status: partial. Shifted NanoWM action embeddings now feed `F_ext`; dataset
diff/local observation features are still absent.

Work:

- pass shifted action embedding into the chronometric layer
- optionally pass per-frame local diff/action features from datasets
- split heads into `F_ext(action/context)` and `F_cont(K,n)`

Gate:

- synthetic action-conditioned transition test shows `F_ext` changes with
  action while `F_cont` remains projector-constrained

First mechanics runner: `scripts/chronometric_mechanics_smoke.py`.

### C3: Branch Interface

Goal: make `n` a planner/search object.

Status: partial. The layer and NanoWM forward path now accept supplied branch
directions; no MCTS/grid caller is connected yet.

Work:

- support provided `branch_direction` tensors
- support multiple branches per state
- expose `score_branch(event_state, velocity, K, n)`
- keep learned `branch_head` only as fallback

Gate:

- same state can evaluate at least two distinct branch directions with
  distinct signed outcomes and shared constraints

First mechanics runner: `scripts/chronometric_mechanics_smoke.py`.

### C4: Signed Y And Family Supervision

Goal: bind the abstract potential families to evidence.

Work:

- train `family_logits` against logged potential-family activations
- train `outcome_y` against progress/loop/contradiction labels
- explicitly preserve raw grid `y` vs latent outcome `y`

Gate:

- held-out trajectories show better branch ranking than uniform family weights

### C5: Rollout Losses

Goal: make the system useful as a world model, not only a token modifier.

Work:

- next-latent/event prediction
- rollout-stability loss over multi-step future predictions
- branch-consistency loss across sibling futures
- compare exact frame/cell/change accuracy against baseline NanoWM

Gate:

- chronometric variant beats plain NanoWM or a simpler action-conditioned
  baseline on a registered metric, not just train loss

## Ablation Protocol

The minimum honest sequence is:

1. Plain NanoWM action-conditioned baseline.
2. Chronometric audit mode, residual disabled.
3. Chronometric residual once, no supervised families.
4. Chronometric residual once with `F_ext` action split.
5. Chronometric branch interface with provided `n`.
6. Chronometric signed-Y/family supervision.

Each run records:

- git commit
- full Hydra config
- dataset split and path
- seed
- step count
- hardware
- train loss
- validation prediction metric
- rollout stability
- branch-ranking metric when available
- throughput and memory

## Immediate Correction To Direction

Do not proceed to ARC ingestion as the next headline task.

Next NanoWM work should be:

1. Add dataset-side context channels for local diffs and signed potential labels.
2. Connect planner/MCTS candidates to `branch_direction`.
3. Train or evaluate signed-Y/family supervision against held-out branches.
4. Only then connect ARC/grid ingestion as a training surface.

This keeps the chronology correct: foundation first, data ingestion second,
planner/search third, ablations fourth.
