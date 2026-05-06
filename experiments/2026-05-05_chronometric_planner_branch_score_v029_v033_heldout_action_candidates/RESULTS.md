# Chronometric Planner Branch Score Results

Status: planner-facing branch scoring smoke for `chronometric_planner_branch_score_v029_v033_heldout_action_candidates`.

This is not a new training run and not ARC solve evidence. It checks that
train-built branch-library and fallback adjustments flow through the
NanoWM-compatible chronometric scoring surface.

## Condition

- run label: `chronometric_planner_branch_score_v029_v033_heldout_action_candidates`
- run kind: `planner_branch_scoring_smoke`
- git commit: `46fabd3529e2cd6bc1ba1bcdd783bc4554d9dd31`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu/predictions.jsonl`
- scorer surface: `score_chronometric_branch_or_score_branch`
- scorer implementation: `ChronometricContortionLayer.score_branch`
- seed: `20260505`
- device: `cpu`
- hidden size: `32`
- frames: `4`
- library scope: `time_phase_translation_stasis_loop`
- fallback scope: `time_phase_translation_potential`
- library entries: `515`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- records scored: `6932`
- planner-applied records: `6096`
- planner-fallback records: `0`
- overall applied reference MAE: `2.812720979429449e-09`
- overall applied reference max abs diff: `1.1920928955078125e-07`
- heldout records: `3112`
- heldout planner-applied records: `2937`
- heldout planner-fallback records: `0`
- heldout applied target signed-Y MAE: `1.1456821457561199e-09`
- heldout unapplied records: `175`
