import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "build_arc_dream_curriculum.py"
    spec = importlib.util.spec_from_file_location("build_arc_dream_curriculum", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_manifest(path: Path, rows: list[dict]):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_arc_dream_curriculum_preserves_quarantine_and_builds_tiers(tmp_path):
    module = _load_module()
    manifest = tmp_path / "arc_bridge_manifest.jsonl"
    out_dir = tmp_path / "curriculum"
    rows = [
        _bridge_row(
            transition_id="easy:000",
            split="arc_sprint0_easy",
            task_id="easy",
            control_label="stasis_no_change",
            action_id="ACTION1",
            signed_outcome_y=0.0,
            changed_cells=0,
        ),
        _bridge_row(
            transition_id="local:000",
            split="arc_sprint0_v010_ft09_targeted_coordinate",
            task_id="local",
            control_label="dominant_group:translation",
            action_id="ACTION2",
            signed_outcome_y=0.25,
            changed_cells=64,
        ),
        _bridge_row(
            transition_id="hard:000",
            split="arc_sprint0_v033_nonlocal_family_v011_heldout",
            task_id="hard",
            control_label="dominant_group:goal_progress",
            progress_label="progress_level_delta_positive",
            action_id="ACTION6",
            signed_outcome_y=1.0,
            changed_cells=400,
            level_delta=1,
        ),
    ]
    _write_manifest(manifest, rows)

    metrics = module.build_curriculum(
        argparse.Namespace(
            manifest=manifest,
            out_dir=out_dir,
            run_label="test_arc_dream_curriculum",
            max_per_tier=8,
            max_total=16,
        )
    )

    challenges = [json.loads(line) for line in (out_dir / "curriculum_challenges.jsonl").read_text().splitlines()]
    assert metrics["selected_challenges"] == 3
    assert metrics["quarantine_integrity"]["quarantine_preserved"] is True
    assert metrics["quarantine_integrity"]["training_data_promoted"] is False
    assert metrics["curriculum_ready_for_dream_kernel_proxy_eval"] is True
    assert {challenge["schema"] for challenge in challenges} == {"dream_kernel.arc_dream_challenge.v001"}
    assert all(challenge["training_data_promoted"] is False for challenge in challenges)
    assert all("control_source" in challenge["quarantine_status"] for challenge in challenges)
    assert all(challenge["dream_kernel_projection"]["known_map_ascii"][1].startswith("#A") for challenge in challenges)
    assert max(challenge["tier_index"] for challenge in challenges) > min(
        challenge["tier_index"] for challenge in challenges
    )
    assert (out_dir / "condition.json").exists()
    assert (out_dir / "metrics.json").exists()
    assert "not an ARC solve claim" in (out_dir / "RESULTS.md").read_text(encoding="utf-8")


def test_tier4_negative_projection_keeps_object_off_safe_goal_route():
    module = _load_module()
    projection = module.dream_projection(
        _bridge_row(
            transition_id="hard:negative",
            split="arc_sprint0_v033_nonlocal_family_v011_heldout",
            task_id="hard",
            control_label="terminal_or_failure",
            action_id="ACTION6",
            signed_outcome_y=-1.0,
            changed_cells=400,
        ),
        tier=4,
    )
    eval_module = _load_eval_module()
    reachability = eval_module.map_reachability(projection["known_map_ascii"])

    assert reachability["goal_reachable_avoiding_hazard"] is True
    assert projection["known_map_ascii"][4] == "#..O...#"
    assert "object_3_4_0" in projection["object_ids_expected"]


def _bridge_row(
    *,
    transition_id: str,
    split: str,
    task_id: str,
    control_label: str,
    action_id: str,
    signed_outcome_y: float,
    changed_cells: int,
    progress_label: str = "no_level_progress",
    level_delta: int = 0,
):
    return {
        "source_repo": "https://example.invalid/arc.git",
        "source_commit": "abc123",
        "source_artifact_path": "experiments/source/transitions.jsonl",
        "source_condition_artifact": "experiments/source/CONDITION.md",
        "quarantine_status": "control_source: arc_scaffold_non_chronometric",
        "split": split,
        "task_id": task_id,
        "attempt_id": f"{task_id}_attempt",
        "transition_id": transition_id,
        "t": 0,
        "observation_shape": [64, 64, 1],
        "action_id": action_id,
        "action_context": [0.1, 0.0, 0.0, 0.0, changed_cells / 4096.0, level_delta, signed_outcome_y, 1.0],
        "event_mu": [0.0, 0.0, signed_outcome_y, 0.0],
        "branch_direction_n": [0.0, 0.0, 1.0 if signed_outcome_y >= 0 else -1.0, 0.0],
        "potential_family_names": [
            "transition.changed_cells",
            "goal_progress.level_delta",
            "stasis.no_change",
        ],
        "potential_family_vector": [changed_cells / 4096.0, float(level_delta), 0.0],
        "signed_outcome_y": signed_outcome_y,
        "progress_label": progress_label,
        "control_label": control_label,
        "chronometric_transform_version": "arc_grid_transition_to_chronometric_bridge_v001",
        "changed_cells": changed_cells,
        "level_delta": level_delta,
        "dominant_family": "goal_progress.level_delta" if level_delta else "transition.changed_cells",
        "dominant_group": "goal_progress" if level_delta else "translation",
        "frame_hash": "before",
        "next_frame_hash": "after",
    }


def _load_eval_module():
    path = ROOT / "scripts" / "run_arc_dream_curriculum_eval.py"
    spec = importlib.util.spec_from_file_location("run_arc_dream_curriculum_eval", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
