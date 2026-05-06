# Chronometric Planner Branch Score Results

Status: planner-facing branch scoring smoke for `chronometric_planner_branch_score_v030_dream_kernel_bridge`.

This is not a new training run and not ARC solve evidence. It checks that
train-built branch-library and fallback adjustments flow through the
NanoWM-compatible chronometric scoring surface.

## Condition

- run label: `chronometric_planner_branch_score_v030_dream_kernel_bridge`
- run kind: `deterministic_dream_kernel_planner_branch_scoring_smoke`
- git commit: `f7c19b0041516fccdf54234b4e58fa3298c9aef9`
- git dirty at run: `True`
- source mode: `dream_kernel_sequence_v003`
- manifest: `experiments/2026-05-06_chronometric_planner_branch_score_v030_dream_kernel_bridge/dream_kernel_bridge_manifest.jsonl`
- input predictions: `None`
- source condition artifact: `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/condition.json`
- scorer surface: `score_chronometric_branch_or_score_branch`
- scorer implementation: `ChronometricContortionLayer.score_branch`
- seed: `20260505`
- device: `cpu`
- hidden size: `32`
- frames: `4`
- library scope: `time_phase_translation_stasis_loop`
- fallback scope: `none`
- library entries: `0`
- heldout labels used: `False`
- training data promoted: `False`

## Metrics

- records scored: `6`
- planner-applied records: `0`
- planner-fallback records: `0`
- overall applied reference MAE: `None`
- overall applied reference max abs diff: `None`
- heldout records: `None`
- heldout planner-applied records: `None`
- heldout planner-fallback records: `None`
- heldout applied target signed-Y MAE: `None`
- heldout unapplied records: `None`
