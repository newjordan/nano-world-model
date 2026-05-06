# Chronometric Branch Selection Results

Status: branch selection smoke for `chronometric_branch_selection_v029_v033_heldout_action_candidates`.

This is not a training run and not ARC solve evidence. Selection uses
chronometric scores only; target labels are used only for diagnostics.

## Condition

- run label: `chronometric_branch_selection_v029_v033_heldout_action_candidates`
- run kind: `branch_selection_smoke`
- git commit: `25d9aa80d24f59c2cf6c57b8b5f38581d4dfa24f`
- git dirty at run: `False`
- input planner scores: `experiments/2026-05-05_chronometric_planner_branch_score_v029_v033_heldout_action_candidates/planner_scores.jsonl`
- group fields: `['split', 'task_id', 'frame_hash', 't']`
- score policy: `library_or_calibration`
- min group size: `2`
- selection uses target labels: `False`
- metrics use target labels: `True`
- training data promoted: `False`

## Metrics

- candidate records: `6932`
- groups: `1608`
- selectable groups: `891`
- selected records: `891`
- skipped groups: `717`
- overall oracle signed-best match rate: `1.0`
- overall mean selected target signed-Y: `-0.1669730069795174`
- overall progress-positive selected: `2`
- heldout selected records: `179`
- heldout oracle signed-best match rate: `1.0`
- heldout mean selected target signed-Y: `-0.009034567039106146`
- heldout progress-positive selected: `1`
