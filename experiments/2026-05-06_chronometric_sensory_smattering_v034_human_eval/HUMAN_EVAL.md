# V034 Human Evaluation Sheet

Fill `human_label` with accept, reject, or unsure. Use notes for why.

## v034_case_001_direct_positive

- description: Direct move right advances self/object toward the objective.
- action: `ACTION_RIGHT`
- visual trusted: `True`
- geometry projection trusted: `True`
- temporal trusted: `True`
- imagined outcome: `0.8` (positive, confidence `0.9`)
- observed outcome: `0.75` (positive)
- outcome trusted: `True`
- combined trusted: `True`
- prompt: Does this look like a sensible positive imagined outcome before action?
- human_label:
- human_notes:

## v034_case_002_wall_block_negative

- description: A wall blocks direct rightward motion; no movement is expected.
- action: `ACTION_RIGHT`
- visual trusted: `True`
- geometry projection trusted: `True`
- temporal trusted: `True`
- imagined outcome: `-0.4` (negative, confidence `0.85`)
- observed outcome: `-0.35` (negative)
- outcome trusted: `True`
- combined trusted: `True`
- prompt: Does the wall-block case deserve negative or low utility?
- human_label:
- human_notes:

## v034_case_003_temporal_miss

- description: The visual map is correct but the imagined next-state misses actual movement.
- action: `ACTION_RIGHT`
- visual trusted: `True`
- geometry projection trusted: `True`
- temporal trusted: `False`
- imagined outcome: `-0.2` (negative, confidence `0.7`)
- observed outcome: `0.75` (positive)
- outcome trusted: `False`
- combined trusted: `False`
- prompt: Would you mark this as a temporal imagination failure?
- human_label:
- human_notes:

## v034_case_004_visual_misread

- description: The predicted map invents a wall where truth has open space.
- action: `ACTION_RIGHT`
- visual trusted: `False`
- geometry projection trusted: `True`
- temporal trusted: `True`
- imagined outcome: `-0.5` (negative, confidence `0.8`)
- observed outcome: `0.6` (positive)
- outcome trusted: `False`
- combined trusted: `False`
- prompt: Would you mark this as a visual map failure before judging planning?
- human_label:
- human_notes:

## v034_case_005_outcome_sign_miss

- description: The map and transition are correct, but imagined outcome polarity is wrong.
- action: `ACTION_RIGHT`
- visual trusted: `True`
- geometry projection trusted: `True`
- temporal trusted: `True`
- imagined outcome: `-0.6` (negative, confidence `0.9`)
- observed outcome: `0.75` (positive)
- outcome trusted: `False`
- combined trusted: `False`
- prompt: Would you mark this as an outcome imagination/sign failure?
- human_label:
- human_notes:
