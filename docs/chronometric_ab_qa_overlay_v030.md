# Chronometric A/B Q/A Overlay V030

Status: architecture target for the next planner integration step.

This document replaces concept-enum planning with an open A/B question loop.
The model should not begin from named hazards, traps, mirrors, keys, or other
game-specific categories. Those names may emerge later as hypotheses, but they
are not the root ontology.

## Core Rule

Every game-state interpretation starts as:

- `A`: current self/state estimate.
- `B`: desired outcome/objective estimate.
- `D`: dimensional gridspace needed to describe A, B, and candidate motion.
- `I`: internal imagination frame, meaning a drawable 2D/3D/latent map of the
  world and candidate consequences.
- `Q`: unresolved questions whose answers may change how A reaches B.
- `C`: confidence distribution over the current interpretation.

The gameplay layer is the Q/A process that discovers objective modifiers. It
does not start with a fixed list of modifiers.

## Nemo Role

Nemo is the semantic thinking engine.

Nemo should:

- inspect the state visually or from state tokens.
- propose A and B in plain terms.
- draw or construct an internal representation before action selection.
- ask open questions about anything that may alter the A-to-B route.
- revise A, B, D, and candidate branches after each answer.
- attach confidence to every claim.

Nemo should not be forced into a small taxonomy like `trap`, `fuel`, `mirror`,
or `blocked`. Those are optional labels after the Q/A loop discovers them.

## Chronometric Role

NanoWM is the constrained branch scorer.

NanoWM should:

- receive candidate branches produced by the Q/A loop.
- map each branch into event-space features.
- score signed-Y utility.
- apply train-built branch-library prototypes when available.
- apply safe potential-family fallbacks when available.
- compare imagined contacts/rays against branch outcomes when probes are
  available.
- return branch rankings and uncertainty to Nemo.

The chronometric model is the scoring substrate. Nemo is the higher-level
question generator and concept reviser.

## V030 Overlay Packet

The planner interface should exchange packets shaped like this:

```json
{
  "state_id": "stable_state_or_frame_hash",
  "ab_hypothesis": {
    "a_self": {
      "description": "what appears controllable or self-relevant",
      "confidence": 0.0,
      "evidence": []
    },
    "b_objective": {
      "description": "what outcome appears desirable",
      "confidence": 0.0,
      "evidence": []
    },
    "gridspace": {
      "dimensions": [],
      "basis": "visual|grid|latent|semantic|mixed",
      "confidence": 0.0
    }
  },
  "imagination_frame": {
    "representation_basis": "grid2d|voxel3d|mesh3d|latent3d|semantic3d|mixed",
    "description": "internal map drawn or constructed before action selection",
    "artifact_ref": "optional pointer to an image, voxel map, mesh, or latent map",
    "confidence": 0.0,
    "raytrace_probes": [
      {
        "probe_id": "stable id",
        "question": "what consequence this ray/probe is testing",
        "origin": [],
        "direction": [],
        "expected_contact": null,
        "confidence": 0.0
      }
    ]
  },
  "open_questions": [
    {
      "question": "unrestricted question about what changes A-to-B success",
      "why_it_matters": "how the answer could alter branch selection",
      "answer": null,
      "confidence": 0.0
    }
  ],
  "objective_modifiers": [
    {
      "name": "emergent label, not predefined",
      "description": "what this modifier changes about A-to-B",
      "polarity": "helps|hurts|conditional|unknown",
      "confidence": 0.0,
      "evidence": []
    }
  ],
  "candidate_branches": [
    {
      "candidate_id": "stable id",
      "action": "ACTION_ID or action vector",
      "expected_ab_delta": "how A changes relative to B",
      "questions_resolved": [],
      "questions_open": [],
      "nemo_confidence": 0.0,
      "chronometric_score": null
    }
  ]
}
```

## Confidence Loop

The loop should continue until one of these happens:

- A and B are stable enough to score candidate branches.
- an unresolved question has high expected value and needs more observation.
- all candidate branches are low-confidence, requiring human input or a new
  probe.

Each iteration:

1. infer or revise A.
2. infer or revise B.
3. choose a gridspace dimensional basis.
4. construct an internal imagination frame.
5. run mental ray/probe checks against imagined consequences.
6. ask unrestricted questions about A-to-B modifiers.
7. answer from visual/state evidence when possible.
8. propose candidate branches.
9. score branches with NanoWM.
10. revise confidence and either act, probe, or ask for input.

## What Counts As A Modifier

A modifier is anything that changes the expected path from A to B.

It may be spatial, temporal, semantic, hidden-state, resource-like,
adversarial, stochastic, symmetric, rule-based, or entirely unknown. The system
does not need to know the class before asking whether the modifier exists.

Correct question shape:

```text
What relation in this state could make the direct A-to-B branch fail or become
suboptimal?
```

Incorrect question shape:

```text
Is there a trap, mirror, fuel, or wall lock?
```

The first question can discover any dimensional rule. The second forces the
model into a brittle category list.

## Gridspace Imagination For ARC-Style Games

For the current grid games, the first imagination producer is a height-map
ray system:

- playable cells remain height `0`.
- non-playable cells become raised blockers for rays.
- wall values block rays but are not treated as object anchors.
- non-wall raised objects become anchors.
- each anchor emits rays through the gridspace.
- ray hits become trust signals for whether imagined movement consequences are
  geometrically plausible.
- object assessments remain open: `beneficial`, `negative`, or any other label
  must be learned or inferred, not hardcoded.

This is the initial version of internal drawing. The map can later become a
voxel, mesh, latent 3D, or mixed representation, but the first target is simple:
draw the grid, raise blockers, attach rays, and measure consequences.

## V030 Implementation Target

V030 should add a small local packet builder and tests:

- create an A/B overlay packet schema.
- include an internal imagination frame with 2D/3D/latent map basis.
- include raytrace/probe questions as confidence-bearing trust signals.
- include a deterministic gridspace raymap producer for playable/non-playable
  cells and non-wall object anchors.
- validate confidence values and required fields.
- accept unrestricted question strings.
- keep modifier names unconstrained.
- attach candidate branches to chronometric branch-score rows.
- produce a deterministic fixture that Nemo or a local LLM can fill later.

The implementation should not call Nemo yet. The first step is to define the
interface so Nemo can become the thinking brain without contaminating the
chronometric scorer with hardcoded game concepts.
