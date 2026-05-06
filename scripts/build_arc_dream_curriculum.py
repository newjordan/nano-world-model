#!/usr/bin/env python3
"""Build a quarantined ARC-to-Dream Kernel curriculum manifest.

This adapter does not promote ARC rows to training data. It converts validated
ARC bridge rows into tiered Dream Kernel proxy challenges with explicit
provenance, so later solver/LoRA work can climb a controlled curriculum.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_bridge import read_jsonl, validate_bridge_manifest, validate_bridge_record  # noqa: E402


DEFAULT_MANIFEST = (
    ROOT
    / "experiments"
    / "2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout"
    / "arc_bridge_manifest.jsonl"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_dream_curriculum_v001"
CURRICULUM_SCHEMA = "dream_kernel.arc_dream_curriculum.v001"
CHALLENGE_SCHEMA = "dream_kernel.arc_dream_challenge.v001"
PROJECTION_VERSION = "arc_bridge_vector_to_dream_kernel_proxy_v001"
TIER_LABELS = {
    0: "t0_micro_stasis_or_small_change",
    1: "t1_local_translation",
    2: "t2_action_coordinate",
    3: "t3_object_relative_branching",
    4: "t4_nonlocal_goal_hazard",
}


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _git_dirty(*, ignored_paths: list[Path] | None = None) -> bool:
    status = _git(["status", "--short", "--untracked-files=all"])
    if status == "unknown":
        return True
    ignored = [_rel(path).rstrip("/") for path in ignored_paths or []]
    for line in status.splitlines():
        status_path = line[3:].strip()
        if " -> " in status_path:
            status_path = status_path.split(" -> ", 1)[1]
        if any(status_path == item or status_path.startswith(f"{item}/") for item in ignored):
            continue
        return True
    return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def build_curriculum(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = args.manifest.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    validation = validate_bridge_manifest(manifest_path)
    if not validation["valid"]:
        raise ValueError(f"invalid bridge manifest: {validation['errors'][:5]}")
    rows = read_jsonl(manifest_path)
    selected = select_rows(rows, max_per_tier=args.max_per_tier, max_total=args.max_total)
    challenges = [challenge_from_bridge_row(row, index) for index, row in enumerate(selected)]
    condition = make_condition(args, manifest_path, out_dir, validation, len(rows), len(challenges))
    metrics = summarize_curriculum(condition, validation, rows, challenges)

    _write_jsonl(out_dir / "curriculum_challenges.jsonl", challenges)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def make_condition(
    args: argparse.Namespace,
    manifest_path: Path,
    out_dir: Path,
    validation: dict[str, Any],
    source_rows: int,
    selected_rows: int,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "run_label": args.run_label,
        "run_kind": "quarantined_arc_to_dream_curriculum_build",
        "run_label_semantics": "scout_curriculum_adapter",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "source_manifest": _rel(manifest_path),
        "source_manifest_sha256": _sha256(manifest_path),
        "source_manifest_records": source_rows,
        "source_manifest_valid": validation["valid"],
        "selected_challenges": selected_rows,
        "max_per_tier": args.max_per_tier,
        "max_total": args.max_total,
        "curriculum_schema": CURRICULUM_SCHEMA,
        "challenge_schema": CHALLENGE_SCHEMA,
        "projection_version": PROJECTION_VERSION,
        "arc_data_used": True,
        "quarantine_status_required": "control_source: arc_scaffold_non_chronometric",
        "training_data_promoted": False,
        "metric_to_compare": "curriculum_tier_coverage_and_quarantine_integrity",
        "dataset_path": _rel(manifest_path),
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_deterministic_sort_select",
        "gpu_count": 0,
        "world_size": 1,
        "loader_mode": "jsonl_bridge_manifest_direct",
        "wallclock_budget": "not_applicable_posthoc_local_build",
        "quantization_policy": "none",
        "compile_kernel_policy": "none",
        "historical_comparator": "none_first_arc_dream_curriculum",
        "historical_comparator_artifact": None,
    }


def select_rows(
    rows: list[dict[str, Any]],
    *,
    max_per_tier: int,
    max_total: int,
) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = {tier: [] for tier in TIER_LABELS}
    for row in rows:
        errors = validate_bridge_record(row)
        if errors:
            continue
        tier = tier_for_row(row)
        buckets[tier].append(row)
    selected: list[dict[str, Any]] = []
    for tier in sorted(buckets):
        tier_rows = sorted(
            buckets[tier],
            key=lambda row: (
                str(row.get("task_id", "")),
                str(row.get("split", "")),
                str(row.get("attempt_id", "")),
                int(row.get("t", 0)),
                str(row.get("transition_id", "")),
            ),
        )
        selected.extend(tier_rows[:max_per_tier])
    selected = selected[:max_total]
    return sorted(selected, key=lambda row: (tier_for_row(row), challenge_source_key(row)))


def challenge_from_bridge_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    difficulty = difficulty_score(row)
    tier = tier_for_row(row)
    source_key = challenge_source_key(row)
    challenge_id = "arcdream:" + hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:20]
    projection = dream_projection(row, tier)
    return {
        "schema": CHALLENGE_SCHEMA,
        "challenge_id": challenge_id,
        "curriculum_id": CURRICULUM_SCHEMA,
        "curriculum_index": index,
        "tier_index": tier,
        "tier_label": TIER_LABELS[tier],
        "difficulty_score": round(difficulty, 6),
        "training_data_promoted": False,
        "quarantine_status": row["quarantine_status"],
        "source": {
            "source_repo": row["source_repo"],
            "source_commit": row["source_commit"],
            "source_artifact_path": row["source_artifact_path"],
            "source_condition_artifact": row["source_condition_artifact"],
            "split": row["split"],
            "task_id": row["task_id"],
            "attempt_id": row["attempt_id"],
            "transition_id": row.get("transition_id"),
            "t": row["t"],
            "frame_hash": row.get("frame_hash"),
            "next_frame_hash": row.get("next_frame_hash"),
        },
        "arc_bridge": {
            "observation_shape": row["observation_shape"],
            "action_id": row["action_id"],
            "action_context": row["action_context"],
            "event_mu": row["event_mu"],
            "branch_direction_n": row["branch_direction_n"],
            "potential_family_names": row.get("potential_family_names", []),
            "potential_family_vector": row["potential_family_vector"],
            "signed_outcome_y": row["signed_outcome_y"],
            "progress_label": row["progress_label"],
            "control_label": row["control_label"],
            "dominant_family": row.get("dominant_family"),
            "dominant_group": row.get("dominant_group"),
            "changed_cells": row.get("changed_cells"),
            "level_delta": row.get("level_delta"),
        },
        "dream_kernel_projection": projection,
        "nemo_callback_policy": nemo_callback_policy(row, tier),
    }


def challenge_source_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("source_commit", "")),
            str(row.get("source_artifact_path", "")),
            str(row.get("task_id", "")),
            str(row.get("attempt_id", "")),
            str(row.get("transition_id", "")),
            str(row.get("t", "")),
        ]
    )


def difficulty_score(row: dict[str, Any]) -> float:
    control = str(row.get("control_label", ""))
    split = str(row.get("split", ""))
    signed_y = abs(float(row.get("signed_outcome_y") or 0.0))
    changed_cells = float(row.get("changed_cells") or 0.0)
    action_context = row.get("action_context") or []
    nonzero_context = sum(1 for value in action_context if isinstance(value, (int, float)) and abs(value) > 1e-9)
    score = 0.5
    score += min(2.0, changed_cells / 128.0)
    score += min(2.0, signed_y * 2.0)
    score += min(1.0, nonzero_context / 4.0)
    if "translation" in control:
        score += 0.8
    if "time_phase" in control or "stasis_loop" in control:
        score += 1.5
    if "goal_progress" in control:
        score += 2.0
    if "terminal_or_failure" in control:
        score += 2.2
    if row.get("progress_label") == "progress_level_delta_positive":
        score += 1.5
    if "targeted_coordinate" in split or "affordance" in split:
        score += 0.7
    if "heatmap" in split:
        score += 1.0
    if "object_relative" in split or "controllability" in split or "support" in split:
        score += 1.7
    if "mirror_hazard" in split:
        score += 2.3
    if "nonlocal" in split:
        score += 2.8
    return score


def tier_for_row(row: dict[str, Any]) -> int:
    score = difficulty_score(row)
    if score < 1.5:
        return 0
    if score < 3.0:
        return 1
    if score < 4.7:
        return 2
    if score < 6.5:
        return 3
    return 4


def dream_projection(row: dict[str, Any], tier: int) -> dict[str, Any]:
    signed_y = float(row.get("signed_outcome_y") or 0.0)
    progress = row.get("progress_label") == "progress_level_delta_positive"
    control = str(row.get("control_label", ""))
    map_rows = map_for_tier(tier, progress=progress, negative=signed_y < 0.0, control=control)
    return {
        "projection_version": PROJECTION_VERSION,
        "projection_type": "proxy_challenge_not_raw_arc_grid",
        "known_map_ascii": map_rows,
        "agent_id": "agent",
        "expected_action_id": row["action_id"],
        "expected_signed_outcome_y": signed_y,
        "expected_outcome_class": outcome_class(row),
        "goal_object_id": first_object_id(map_rows, "G"),
        "hazard_object_id": first_object_id(map_rows, "H"),
        "object_ids_expected": object_ids_from_map(map_rows),
        "chronometric": {
            "event_mu": row["event_mu"],
            "branch_direction_n": row["branch_direction_n"],
            "potential_family_vector": row["potential_family_vector"],
            "signed_outcome_y": signed_y,
        },
        "notes": (
            "This map is a deterministic Dream Kernel proxy derived from ARC bridge "
            "features. It is not the raw ARC observation grid and is not training data."
        ),
    }


def map_for_tier(tier: int, *, progress: bool, negative: bool, control: str) -> list[str]:
    if tier == 0:
        return ["#####", "#A.G#", "#...#", "#####"]
    if tier == 1:
        return ["######", "#A..G#", "#....#", "######"]
    if tier == 2:
        return ["######", "#A#.G#", "#....#", "######"]
    if tier == 3:
        if "stasis" in control:
            return ["######", "#AO.G#", "#....#", "######"]
        return ["#######", "#A..H.#", "#.##..#", "#...G.#", "#######"]
    if progress and not negative:
        return ["########", "#A..H.G#", "#.####.#", "#......#", "########"]
    return ["########", "#A.H..G#", "#.####.#", "#......#", "#..O...#", "########"]


def outcome_class(row: dict[str, Any]) -> str:
    if row.get("progress_label") == "progress_level_delta_positive":
        return "positive_goal_progress"
    signed_y = float(row.get("signed_outcome_y") or 0.0)
    if signed_y < 0.0 or row.get("control_label") == "terminal_or_failure":
        return "negative_or_failure"
    if row.get("control_label") == "stasis_no_change":
        return "stasis"
    return "nonterminal_transition"


def first_object_id(rows: list[str], marker: str) -> str | None:
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == marker:
                kind = {"G": "goal", "H": "hazard", "#": "wall", "O": "object"}.get(marker, "object")
                return f"{kind}:{x}:{y}:0"
    return None


def object_ids_from_map(rows: list[str]) -> list[str]:
    objects: list[str] = ["agent"]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                objects.append(f"wall:{x}:{y}:0")
            elif ch == "G":
                objects.append(f"goal:{x}:{y}:0")
            elif ch == "H":
                objects.append(f"hazard:{x}:{y}:0")
            elif ch == "O":
                objects.append(f"object_{x}_{y}_0")
    return objects


def nemo_callback_policy(row: dict[str, Any], tier: int) -> dict[str, Any]:
    reasons = []
    control = str(row.get("control_label", ""))
    if tier >= 2:
        reasons.append("branch_relation_disambiguation")
    if "stasis" in control or "time_phase" in control:
        reasons.append("temporal_or_loop_semantics")
    if "goal_progress" in control or row.get("progress_label") == "progress_level_delta_positive":
        reasons.append("goal_progress_semantics")
    if "terminal" in control:
        reasons.append("failure_semantics")
    return {
        "nemo_is_driver": False,
        "chronometric_kernel_drives_action": True,
        "callback_required": bool(reasons),
        "callback_reasons": reasons,
        "allowed_outputs": ["category_revision_hypotheses", "object_relation_hypotheses", "evidence_needed"],
        "forbidden_outputs": ["direct_training_label_promotion", "dream_sequence_mutation"],
    }


def summarize_curriculum(
    condition: dict[str, Any],
    validation: dict[str, Any],
    source_rows: list[dict[str, Any]],
    challenges: list[dict[str, Any]],
) -> dict[str, Any]:
    tier_counts: dict[str, int] = {}
    task_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    control_counts: dict[str, int] = {}
    for challenge in challenges:
        tier_counts[challenge["tier_label"]] = tier_counts.get(challenge["tier_label"], 0) + 1
        source = challenge["source"]
        bridge = challenge["arc_bridge"]
        task_counts[source["task_id"]] = task_counts.get(source["task_id"], 0) + 1
        split_counts[source["split"]] = split_counts.get(source["split"], 0) + 1
        control_counts[bridge["control_label"]] = control_counts.get(bridge["control_label"], 0) + 1
    quarantine_ok = all("control_source" in challenge["quarantine_status"] for challenge in challenges)
    training_ok = all(challenge["training_data_promoted"] is False for challenge in challenges)
    return {
        "condition": condition,
        "source_validation": validation,
        "source_rows": len(source_rows),
        "selected_challenges": len(challenges),
        "tier_counts": dict(sorted(tier_counts.items())),
        "task_counts": dict(sorted(task_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "control_counts": dict(sorted(control_counts.items())),
        "quarantine_integrity": {
            "quarantine_preserved": quarantine_ok,
            "training_data_promoted": not training_ok,
            "projection_version": PROJECTION_VERSION,
        },
        "curriculum_ready_for_dream_kernel_proxy_eval": bool(challenges) and quarantine_ok and training_ok,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC To Dream Curriculum V001 Results",
        "",
        "Status: quarantined ARC bridge rows converted into tiered Dream Kernel proxy challenges.",
        "",
        "This is not training data promotion and not an ARC solve claim.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- source manifest: `{condition['source_manifest']}`",
        f"- source manifest records: `{condition['source_manifest_records']}`",
        f"- selected challenges: `{condition['selected_challenges']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Curriculum",
        "",
        f"- ready for Dream Kernel proxy eval: `{metrics['curriculum_ready_for_dream_kernel_proxy_eval']}`",
        f"- quarantine preserved: `{metrics['quarantine_integrity']['quarantine_preserved']}`",
        f"- tier counts: `{metrics['tier_counts']}`",
        f"- task counts: `{metrics['task_counts']}`",
        f"- control counts: `{metrics['control_counts']}`",
        "",
        "## Next Gate",
        "",
        "Use `curriculum_challenges.jsonl` as a proxy curriculum. The next runner should execute",
        "the projected maps through Dream Kernel and compare solve/rank behavior by tier. Only",
        "human-reviewed successes may become LoRA trace candidates later.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_dream_curriculum_v001")
    parser.add_argument("--max-per-tier", type=int, default=24)
    parser.add_argument("--max-total", type=int, default=160)
    return parser.parse_args()


def main() -> int:
    metrics = build_curriculum(parse_args())
    print(
        json.dumps(
            {
                "selected_challenges": metrics["selected_challenges"],
                "tier_counts": metrics["tier_counts"],
                "ready": metrics["curriculum_ready_for_dream_kernel_proxy_eval"],
                "training_data_promoted": metrics["quarantine_integrity"]["training_data_promoted"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
