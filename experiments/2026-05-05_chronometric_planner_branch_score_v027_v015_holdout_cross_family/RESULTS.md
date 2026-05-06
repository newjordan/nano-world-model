# Chronometric Planner Branch Score Results

Status: planner-facing branch scoring smoke for `chronometric_planner_branch_score_v027_v015_holdout_cross_family`.

This is not a new training run and not ARC solve evidence. It checks that
train-built branch-library and fallback adjustments flow through the
NanoWM-compatible chronometric scoring surface.

## Condition

- run label: `chronometric_planner_branch_score_v027_v015_holdout_cross_family`
- run kind: `planner_branch_scoring_smoke`
- git commit: `0bfb08d22716846057e8a76e9a9948576fd7f750`
- git dirty at run: `False`
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/arc_bridge_manifest.jsonl`
- input predictions: `experiments/2026-05-05_chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu/predictions.jsonl`
- scorer surface: `score_chronometric_branch_or_score_branch`
- scorer implementation: `ChronometricContortionLayer.score_branch`
- seed: `20260505`
- device: `cpu`
- hidden size: `32`
- frames: `4`
- library scope: `time_phase_translation_stasis_loop`
- fallback scope: `time_phase_translation_potential`
- library entries: `550`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- records scored: `7732`
- planner-applied records: `6770`
- planner-fallback records: `23`
- overall applied reference MAE: `2.8857415159572703e-09`
- overall applied reference max abs diff: `1.1920928955078125e-07`
- heldout records: `400`
- heldout planner-applied records: `339`
- heldout planner-fallback records: `23`
- heldout applied target signed-Y MAE: `3.4879953504312003e-09`
- heldout unapplied records: `61`
