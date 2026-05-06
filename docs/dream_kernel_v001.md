# Dream Kernel V001

Status: foundation contract and executable micro-simulator seed.

Dream Kernel is the internal imagination environment. It is not a visual review
page and it is not the current V031/V032 ray accuracy gate. Its job is to hold a
known spatial map, step an internal action sequence through that map, cast
survival-relevant rays from the simulated state, and emit a renderable sequence
for humans or downstream audit.

The goal is not to guess. Unknown perception can feed Dream Kernel only after it
has been converted into explicit known-map cells with provenance. Once inside
the kernel, state transitions are deterministic and inspectable.

## Why This Exists

The current chronometric surfaces prove narrow trust conditions:

- V031 labels a map, builds simple 3D cell boxes, and compares ray contacts.
- V032 adds temporal and outcome confirmation for one state/action.
- V034 exposes those records for human review.

That is useful, but it is not enough. A hostile environment needs an internal
world that can be navigated before acting. The ray is not decoration; it is part
of the survival mechanism. The simulated map/action sequence is the thing the
planner should reason over.

## Kernel Contract

Dream Kernel owns these concepts:

- `KnownMap`: explicit spatial cells, dimensions, and labels.
- `SimState`: map plus entity positions at a tick.
- `Action`: a proposed internal movement or wait.
- `StepOutcome`: accepted/rejected move, reason, terminal status, and reward.
- `RayBundle`: rays cast from the current simulated state.
- `RayContact.object_id`: required stable identifier for the exact contacted
  map object or entity, not just a semantic class.
- `RayHit.network`: explicit ray-network polarity:
  `beneficial`, `adversarial`, `structural`, or `neutral`.
- `RayHit.signed_potential_y`: deterministic signed potential carried by the
  ray contact. Goals are positive, hazards are negative, blockers are structural
  negative pressure, and neutral entities do not invent a score.
- `ChronometricFrame`: per-frame deterministic event/potential overlay with
  `event_mu`, `branch_direction_n`, `phase_theta`, `signed_outcome_y`,
  `potential_family_vector`, and coordinate-addressed potential datapoints.
- `PotentialDatum.event_coord`: a lifted internal planning coordinate
  `(t, x, y_chrono, z)` tethered to the datapoint's real `position`. The
  `position` stays the known-map anchor; `y_chrono` is the signed outcome axis
  used for planning rays, value gradients, and branch ranking.
- `DreamFrame`: one tick of state plus rays and the previous transition result.
- `DreamSequence`: the full imagined internal rollout.
- `ObjectRegistry`: canonical object table for stable ID resolution. Rays and
  potentials reference this table instead of becoming their own object authority.
  Each object now has both a stable local `object_id` and an open
  `category_id`, with `open_tags` and `hypothesis_refs` so the same instance can
  survive changing game state without being trapped in a closed label band.
- `FrameIntegrity`: per-frame invariant report plus a deterministic hash chained
  to the previous frame hash.
- `BranchMatrix`: action/branch summary rows for ranking candidate futures in
  lifted Chronometric Y-space.
- `BranchPotential`: per-branch, per-object outcome probability/correlation
  rows derived from Chronometric Y. These are branch-scoring hypotheses, not
  forced labels.
- `ObjectLinkHypothesis`: open-ended object-object relation candidates for the
  current branch. The default relation kind is intentionally broad:
  `branch.coactivation.open_relation`.
- `NemoRelayPacket`: explicit semantic relay questions for Nemo/Nemotron. The
  deterministic kernel emits the packet; Nemo can review category revisions,
  relation candidates, and confirming evidence without contaminating the map
  math.

The first implementation is a 3D integer grid with top-down ASCII helpers. The
important boundary is that the grid is still a real coordinate map:
`x`, `y`, and `z` are explicit. A 2D review surface is only a projection.
Chronometric Y-space is not physical height. It is a lifted event-space axis
attached to map coordinates so latent outcome pressure can be debugged against
the exact object, ray, tick, and source that produced it.

## V001 Behavior

V001 is deliberately small:

- parses a known ASCII layer into a 3D map.
- tracks an agent entity.
- rejects moves into walls, bounds, or occupied cells.
- allows terminal success at goals.
- treats hazards as terminal hostile contacts.
- casts rays in integer 3D directions until they hit bounds, walls, hazards,
  goals, or entities.
- emits a stable contact identifier on every ray hit. Static map contacts use
  coordinate IDs such as `hazard:3:1:0`; entity contacts use the entity ID such
  as `object_2_1_0`.
- classifies every ray into an explicit network and potential family:
  `hazard.env_failure`, `goal_progress.level_delta`, or
  `mirror.progress_blocker`.
- emits known-map and ray-contact potential datapoints with object IDs,
  coordinates, signed values, network class, and source labels.
- emits `event_coord = (t, x, y_chrono, z)` for each potential datapoint.
  Positive `y_chrono` is beneficial/progress pressure. Negative `y_chrono` is
  adverse/failure pressure. The `x` and `z` values are copied from the map
  anchor so the lifted event point remains tethered to the grid.
- emits a deterministic chronometric overlay from the documented event-space
  shape: `event_mu = [tick, x_norm, signed_outcome_y, y_norm]`, log-time
  `phase_theta`, ray-derived `branch_direction_n`, and the current potential
  family vector.
- emits provenance per potential datum: source type, tick, action/branch IDs
  when available, evidence kind, and confidence.
- emits imagined-vs-observed calibration slots:
  `imagined_chrono_y`, `observed_chrono_y`, `calibration_error`, and
  `calibrated_chrono_y`.
- emits an invariant-gated integrity layer. Current invariants check object IDs,
  registry agreement, map/event tethering, Chronometric Y sign consistency, and
  confidence bounds.
- emits open categorical identity fields:
  `category_id`, `category_confidence`, `open_tags`, and `hypothesis_refs`.
- emits branch potentials with `outcome_probability`, `positive_probability`,
  `negative_probability`, `chrono_y_correlation`, and evidence sources.
- emits object-link hypotheses with probability/correlation and open questions
  that can be relayed to Nemo for semantic confirmation.
- emits a Nemo relay packet with status `packet_ready_model_not_called`; the
  harness can send branch-local packets to the local
  `nemotron_3_nano_omni` endpoint and save confirmations as a sidecar artifact.
- emits a sequence that can be rendered for human review.

This is the first "micro simulator" surface, not the final physics engine. The
chronometric overlay is deterministic V001 simulator evidence, not learned
`F_cont`. The next versions should add velocity, object interaction, partial
observation provenance, learned-video alignment, and a learned projected
contortion head over the same sidecar fields.

## Rust Crate

Code:

- `dream_kernel/Cargo.toml`
- `dream_kernel/src/lib.rs`
- `dream_kernel/src/main.rs`

Verification:

```bash
cargo test --manifest-path dream_kernel/Cargo.toml
```

Demo:

```bash
cargo run --manifest-path dream_kernel/Cargo.toml -- demo
```

Export a review artifact:

```bash
cargo run --manifest-path dream_kernel/Cargo.toml -- demo \
  --out experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json
```

## Integration Direction

Dream Kernel should sit under the human-review harness and NanoWM planning
surfaces:

```text
observation/perception -> known map -> Dream Kernel rollout
Dream Kernel rollout -> renderable sequence for humans
Dream Kernel rollout -> labels, ray bundles, outcomes, planner features
```

The human-eval harness loads `dream_sequence.json` from the experiment
directory when present. It renders the same sequence in two views:

- a 2D top-down audit grid.
- a Three.js 3D canvas with geometry, adversarial/beneficial/structural ray
  networks, contact markers, and chronometric potential datapoints derived from
  the sequence coordinates. Potential datapoints render as lifted event-space
  points: green +Y points above the grid, red -Y points below the grid, each
  connected back to its map anchor by a tether line.
- branch-potential tables showing object/category IDs, probability, correlation,
  and relation candidate IDs.
- object-link hypothesis rows showing possible links between object X and object
  Y without forcing a closed relation label.
- a Nemo Relay panel that sends the selected branch packet through the local
  OpenAI-compatible Nemo endpoint and records the returned confirmation in
  `nemo_relay_confirmations.json`.
- per-frame tables for `event_mu`, `branch_direction_n`, `phase_theta`,
  `signed_outcome_y`, potential-family vector values, and object-ID-addressed
  potential points with both map coordinates and lifted event coordinates.

The agent eventually does not need human rendering. The render exists so we can
audit whether the internal sequence is coherent before trusting it.

## Promotion Rule

No training data is promoted from Dream Kernel V001. It is an executable
foundation. Promotion requires a later explicit condition that ties known-map
provenance, simulated action sequence, observed outcome, and human review.
