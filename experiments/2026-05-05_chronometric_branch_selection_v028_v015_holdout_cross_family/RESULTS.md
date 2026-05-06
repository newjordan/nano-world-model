# Chronometric Branch Selection Results

Status: branch selection smoke for `chronometric_branch_selection_v028_v015_holdout_cross_family`.

This is not a training run and not ARC solve evidence. Selection uses
chronometric scores only; target labels are used only for diagnostics.

## Condition

- run label: `chronometric_branch_selection_v028_v015_holdout_cross_family`
- run kind: `branch_selection_smoke`
- git commit: `37d666695e9273c41f8e0e9bf19a71034d9acc95`
- git dirty at run: `False`
- input planner scores: `experiments/2026-05-05_chronometric_planner_branch_score_v027_v015_holdout_cross_family/planner_scores.jsonl`
- group fields: `['split', 'task_id', 'frame_hash', 't']`
- score policy: `library_or_calibration`
- min group size: `2`
- selection uses target labels: `False`
- metrics use target labels: `True`
- training data promoted: `False`

## Metrics

- candidate records: `7732`
- groups: `2138`
- selectable groups: `774`
- selected records: `774`
- skipped groups: `1364`
- overall oracle signed-best match rate: `1.0`
- overall mean selected target signed-Y: `-0.1912128931484173`
- overall progress-positive selected: `1`
- heldout selected records: `0`
- heldout oracle signed-best match rate: `None`
- heldout mean selected target signed-Y: `None`
- heldout progress-positive selected: `0`
