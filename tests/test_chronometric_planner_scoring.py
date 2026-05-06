import copy
import importlib.util
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_branch_library import build_chronometric_branch_library  # noqa: E402
from chronometric_bridge import synthetic_bridge_records  # noqa: E402
from chronometric_planner_scoring import (  # noqa: E402
    score_chronometric_branch_rows,
    summarize_planner_branch_scores,
)


def _load_chrono_module():
    module_path = SRC / "models" / "chronometric_contortion.py"
    spec = importlib.util.spec_from_file_location("chronometric_contortion_direct_planner", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


chrono = _load_chrono_module()


class NanoWMScoringProxy:
    def __init__(self, layer):
        self.layer = layer
        self.calls = 0

    def score_chronometric_branch(self, *args, **kwargs):
        self.calls += 1
        return self.layer.score_branch(*args, **kwargs)


def _row(split: str, target: float, pred: float):
    row = copy.deepcopy(synthetic_bridge_records()[0])
    row.update(
        {
            "split": split,
            "action_id": "ACTION6",
            "control_label": "dominant_group:time_phase",
            "action_context": [0.6, 1.0, 0.4375, 0.46875, 0.000244140625, 0.0, 0.25, 1.0],
            "branch_direction_n": [0.0, 0.0, 1.0, 0.0],
            "changed_cells": 1,
            "potential_family_names": ["transition.changed_cells", "time_phase.repeated_effect_size"],
            "potential_family_vector": [0.000244140625, 0.25],
            "target_signed_y": target,
            "pred_signed_y": pred,
            "target_progress": 0.0,
        }
    )
    return row


def test_planner_scoring_uses_nanowm_compatible_branch_score_surface():
    torch.manual_seed(7)
    train = _row("train", 0.25, -0.9)
    heldout = _row("heldout", 0.0, -0.5)
    library = build_chronometric_branch_library([train, heldout], scope="time_phase_translation_stasis_loop")
    proxy = NanoWMScoringProxy(chrono.ChronometricContortionLayer(hidden_size=16))

    scored = score_chronometric_branch_rows(
        proxy,
        [heldout],
        branch_library=library,
        branch_library_blend=1.0,
        hidden_size=16,
        frames=3,
    )

    assert proxy.calls == 2
    assert scored[0]["planner_branch_library_applied"] is True
    assert scored[0]["planner_branch_library_fallback_applied"] is False
    assert scored[0]["planner_branch_library_key"] == (
        "ACTION6|dominant_group:time_phase|coord:x:28|y:30|changed:1"
    )
    assert scored[0]["planner_pred_signed_y"] == torch.tensor(0.25).item()
    assert scored[0]["planner_reference_abs_diff"] <= 1e-6


def test_planner_scoring_routes_time_phase_translation_fallback():
    torch.manual_seed(11)
    heldout = _row("heldout", 0.2529296875, -0.5)
    heldout["action_id"] = "ACTION1"
    heldout["control_label"] = "dominant_group:time_phase"
    heldout["action_context"] = [0.1, 0.0, 0.0, 0.0, 0.0029296875, 0.0, 0.25, 1.0]
    heldout["changed_cells"] = 12
    heldout["potential_family_vector"] = [0.0029296875, 0.25]
    layer = chrono.ChronometricContortionLayer(hidden_size=16)

    scored = score_chronometric_branch_rows(
        layer,
        [heldout],
        branch_library={},
        branch_library_blend=1.0,
        branch_library_fallback_scope="time_phase_translation_potential",
        hidden_size=16,
        frames=3,
    )
    summary = summarize_planner_branch_scores(scored)

    assert scored[0]["planner_branch_library_applied"] is True
    assert scored[0]["planner_branch_library_fallback_applied"] is True
    assert scored[0]["planner_branch_library_key"].startswith("fallback:dominant_time_phase_potential|")
    assert scored[0]["planner_pred_signed_y"] == torch.tensor(0.2529296875).item()
    assert summary["records"] == 1
    assert summary["fallback_records"] == 1
    assert summary["overall"]["applied_target_signed_mae"] <= 1e-6
