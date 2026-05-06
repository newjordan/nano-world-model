# ARC To Dream Curriculum V001 Results

Status: quarantined ARC bridge rows converted into tiered Dream Kernel proxy challenges.

This is not training data promotion and not an ARC solve claim.

## Condition

- run label: `arc_dream_curriculum_v001_v017_support_scout`
- run kind: `quarantined_arc_to_dream_curriculum_build`
- git commit: `f7c19b0041516fccdf54234b4e58fa3298c9aef9`
- git dirty at run: `True`
- source manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- source manifest records: `7732`
- selected challenges: `96`
- training data promoted: `False`

## Curriculum

- ready for Dream Kernel proxy eval: `True`
- quarantine preserved: `True`
- tier counts: `{'t1_local_translation': 24, 't2_action_coordinate': 24, 't3_object_relative_branching': 24, 't4_nonlocal_goal_hazard': 24}`
- task counts: `{'dc22-fdcac232': 59, 'ft09-0d8bbf25': 14, 'm0r0-492f87ba': 23}`
- control counts: `{'dominant_group:goal_progress': 23, 'dominant_group:stasis_loop': 13, 'dominant_group:translation': 48, 'stasis_no_change': 11, 'terminal_or_failure': 1}`

## Next Gate

Use `curriculum_challenges.jsonl` as a proxy curriculum. The next runner should execute
the projected maps through Dream Kernel and compare solve/rank behavior by tier. Only
human-reviewed successes may become LoRA trace candidates later.
