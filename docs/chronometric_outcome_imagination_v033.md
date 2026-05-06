# Chronometric Outcome Imagination V033

Status: correction to V032 outcome handling.

V032 originally described outcome as only a post-action label for later
correlation. That was too narrow. The world model must imagine outcomes before
acting. V033 makes this explicit:

- `imagined_outcome` is pre-action simulation.
- `observed_outcome` is post-action truth.
- the planner may use `imagined_outcome` for branch choice.
- training/eval may compare `imagined_outcome` against `observed_outcome`.
- observed outcome must never be smuggled into visual or temporal perception as
  if it was known before action.

## Record Shape

The corrected record carries both sides:

```json
{
  "pre_action_simulation": {
    "imagined_outcome": {
      "signed_y": 0.5,
      "polarity": "positive",
      "confidence": 0.9,
      "source": "pre_action_simulation"
    }
  },
  "post_action_observation": {
    "observed_outcome": {
      "signed_y": 0.5,
      "polarity": "positive"
    }
  },
  "outcome_imagination": {
    "comparison": {
      "observed_available": true,
      "signed_abs_error": 0.0,
      "polarity_match": true
    },
    "trusted": true
  }
}
```

This means the model can ask, before action:

```text
If I take this branch through my current visual+temporal simulation, what
signed-Y outcome do I imagine?
```

Then, after action:

```text
Did the observed result confirm or reject that imagined outcome?
```

## Boundary

Run label: `new_experiment`.

No training data is promoted. No ARC solve claim is made. This only repairs the
evidence contract so outcome imagination is a first-class pre-action channel.
