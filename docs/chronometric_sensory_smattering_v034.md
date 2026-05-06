# Chronometric Sensory Smattering V034

Status: deterministic human-eval probe batch.

V034 creates a small spread of state/action cases for human review. It is not a
training run and not a solve claim. The purpose is to check whether the
visual, temporal, and pre-action outcome-imagination signals feel aligned with
human judgment before scaling to larger trace batches.

## Cases

The initial batch includes:

- direct positive movement toward an objective.
- wall-blocked movement with negative/low utility.
- temporal miss where the imagined next-state fails.
- visual map misread before planning is judged.
- outcome-sign miss where map and transition are correct but imagined utility
  has the wrong sign.

## Harness

```bash
python scripts/run_chronometric_sensory_smattering.py \
  --run-label chronometric_sensory_smattering_v034_human_eval \
  --out-dir experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval
```

The harness writes:

- `condition.json`
- `metrics.json`
- `sensory_records.jsonl`
- `HUMAN_EVAL.md`
- `RESULTS.md`

`HUMAN_EVAL.md` is the hand-review surface. Fill `human_label` with `accept`,
`reject`, or `unsure`, then add notes.

## Boundary

Run label: `new_experiment`.

No training data is promoted. Human labels from this batch should be treated as
review evidence until a later explicit promotion condition exists.
