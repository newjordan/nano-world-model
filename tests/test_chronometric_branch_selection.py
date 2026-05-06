import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_branch_selection import (  # noqa: E402
    branch_selection_score,
    select_chronometric_branches,
    summarize_branch_selection,
)
from chronometric_bridge import synthetic_bridge_records  # noqa: E402


def _candidate(action_id: str, *, planner_score: float, calibration_score: float, target: float, applied: bool):
    row = copy.deepcopy(synthetic_bridge_records()[0])
    row.update(
        {
            "split": "heldout",
            "task_id": "task-a",
            "frame_hash": "frame-a",
            "t": 3,
            "action_id": action_id,
            "planner_pred_signed_y": planner_score,
            "pred_signed_y": calibration_score,
            "planner_branch_library_applied": applied,
            "planner_branch_library_fallback_applied": False,
            "target_signed_y": target,
            "target_progress": 1.0 if target >= 0.95 else 0.0,
        }
    )
    return row


def test_selection_score_uses_calibration_when_branch_score_unapplied():
    row = _candidate("ACTION4", planner_score=-0.2, calibration_score=1.0, target=1.0, applied=False)

    assert branch_selection_score(row, score_policy="planner") == -0.2
    assert branch_selection_score(row, score_policy="library_or_calibration") == 1.0


def test_selects_best_branch_without_reading_targets():
    rows = [
        _candidate("ACTION1", planner_score=0.25, calibration_score=-0.5, target=0.25, applied=True),
        _candidate("ACTION4", planner_score=-0.2, calibration_score=1.0, target=1.0, applied=False),
        _candidate("ACTION2", planner_score=-1.0, calibration_score=-1.0, target=-1.0, applied=True),
    ]

    selected = select_chronometric_branches(rows, score_policy="library_or_calibration")
    summary = summarize_branch_selection(selected, candidate_rows=rows)

    assert len(selected) == 1
    assert selected[0]["action_id"] == "ACTION4"
    assert selected[0]["selection_score"] == 1.0
    assert selected[0]["selection_matches_oracle_signed_best"] is True
    assert summary["selectable_groups"] == 1
    assert summary["overall"]["oracle_signed_best_match_rate"] == 1.0
    assert summary["overall"]["progress_positive_selected"] == 1


def test_ignores_singleton_groups_by_default():
    rows = [_candidate("ACTION1", planner_score=0.25, calibration_score=-0.5, target=0.25, applied=True)]

    selected = select_chronometric_branches(rows)
    summary = summarize_branch_selection(selected, candidate_rows=rows)

    assert selected == []
    assert summary["selectable_groups"] == 0
    assert summary["skipped_groups"] == 1
