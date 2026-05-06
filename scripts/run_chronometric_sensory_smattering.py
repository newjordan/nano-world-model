#!/usr/bin/env python
"""Run a small V034 sensory/outcome-imagination smattering."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_map_perception import ColorLabel  # noqa: E402
from chronometric_sensory_alignment import build_sensory_confirmation_record  # noqa: E402


Grid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SmatteringCase:
    case_id: str
    description: str
    action: str
    predicted_grid: Grid
    truth_grid: Grid
    predicted_after_grid: Grid
    actual_after_grid: Grid
    imagined_outcome_y: float
    imagined_outcome_confidence: float
    observed_outcome_y: float
    human_prompt: str


LABELS = (
    ColorLabel(value=0, rgb=(0, 0, 0), name="playable"),
    ColorLabel(value=2, rgb=(0, 255, 0), name="self_or_object"),
    ColorLabel(value=3, rgb=(0, 0, 255), name="objective"),
    ColorLabel(value=9, rgb=(255, 255, 255), name="wall"),
)


def main() -> int:
    args = _parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = _cases()
    records = []
    for case in cases:
        record = build_sensory_confirmation_record(
            state_id=case.case_id,
            action=case.action,
            predicted_grid=case.predicted_grid,
            truth_grid=case.truth_grid,
            predicted_after_grid=case.predicted_after_grid,
            actual_after_grid=case.actual_after_grid,
            labels=LABELS,
            playable_values=(0,),
            wall_values=(9,),
            imagined_outcome_y=case.imagined_outcome_y,
            imagined_outcome_confidence=case.imagined_outcome_confidence,
            signed_outcome_y=case.observed_outcome_y,
        )
        record["human_eval"] = {
            "prompt": case.human_prompt,
            "human_label": None,
            "human_notes": None,
        }
        record["case_description"] = case.description
        records.append(record)

    metrics = _summarize(records)
    condition = {
        "run_label": args.run_label,
        "run_type": "chronometric_sensory_smattering_v034",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(cases),
        "labels": tuple(asdict(label) for label in LABELS),
        "playable_values": (0,),
        "wall_values": (9,),
        "training_data_promoted": False,
        "human_eval_required": True,
        **_git_condition(),
    }

    _write_json(out_dir / "condition.json", condition)
    _write_json(out_dir / "metrics.json", metrics)
    _write_jsonl(out_dir / "sensory_records.jsonl", records)
    _write_human_eval(out_dir / "HUMAN_EVAL.md", records)
    _write_results(out_dir / "RESULTS.md", condition, metrics)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def _cases() -> tuple[SmatteringCase, ...]:
    boxed_start = (
        (9, 9, 9, 9, 9),
        (9, 2, 0, 3, 9),
        (9, 0, 0, 0, 9),
        (9, 9, 9, 9, 9),
    )
    move_right = (
        (9, 9, 9, 9, 9),
        (9, 0, 2, 3, 9),
        (9, 0, 0, 0, 9),
        (9, 9, 9, 9, 9),
    )
    blocked_start = (
        (9, 9, 9, 9),
        (9, 2, 9, 9),
        (9, 0, 3, 9),
        (9, 9, 9, 9),
    )
    visual_truth = (
        (9, 9, 9, 9),
        (9, 2, 0, 9),
        (9, 0, 3, 9),
        (9, 9, 9, 9),
    )
    visual_bad_prediction = (
        (9, 9, 9, 9),
        (9, 2, 9, 9),
        (9, 0, 3, 9),
        (9, 9, 9, 9),
    )
    visual_actual_after = (
        (9, 9, 9, 9),
        (9, 0, 2, 9),
        (9, 0, 3, 9),
        (9, 9, 9, 9),
    )

    return (
        SmatteringCase(
            case_id="v034_case_001_direct_positive",
            description="Direct move right advances self/object toward the objective.",
            action="ACTION_RIGHT",
            predicted_grid=boxed_start,
            truth_grid=boxed_start,
            predicted_after_grid=move_right,
            actual_after_grid=move_right,
            imagined_outcome_y=0.8,
            imagined_outcome_confidence=0.9,
            observed_outcome_y=0.75,
            human_prompt="Does this look like a sensible positive imagined outcome before action?",
        ),
        SmatteringCase(
            case_id="v034_case_002_wall_block_negative",
            description="A wall blocks direct rightward motion; no movement is expected.",
            action="ACTION_RIGHT",
            predicted_grid=blocked_start,
            truth_grid=blocked_start,
            predicted_after_grid=blocked_start,
            actual_after_grid=blocked_start,
            imagined_outcome_y=-0.4,
            imagined_outcome_confidence=0.85,
            observed_outcome_y=-0.35,
            human_prompt="Does the wall-block case deserve negative or low utility?",
        ),
        SmatteringCase(
            case_id="v034_case_003_temporal_miss",
            description="The visual map is correct but the imagined next-state misses actual movement.",
            action="ACTION_RIGHT",
            predicted_grid=boxed_start,
            truth_grid=boxed_start,
            predicted_after_grid=boxed_start,
            actual_after_grid=move_right,
            imagined_outcome_y=-0.2,
            imagined_outcome_confidence=0.7,
            observed_outcome_y=0.75,
            human_prompt="Would you mark this as a temporal imagination failure?",
        ),
        SmatteringCase(
            case_id="v034_case_004_visual_misread",
            description="The predicted map invents a wall where truth has open space.",
            action="ACTION_RIGHT",
            predicted_grid=visual_bad_prediction,
            truth_grid=visual_truth,
            predicted_after_grid=visual_actual_after,
            actual_after_grid=visual_actual_after,
            imagined_outcome_y=-0.5,
            imagined_outcome_confidence=0.8,
            observed_outcome_y=0.6,
            human_prompt="Would you mark this as a visual map failure before judging planning?",
        ),
        SmatteringCase(
            case_id="v034_case_005_outcome_sign_miss",
            description="The map and transition are correct, but imagined outcome polarity is wrong.",
            action="ACTION_RIGHT",
            predicted_grid=boxed_start,
            truth_grid=boxed_start,
            predicted_after_grid=move_right,
            actual_after_grid=move_right,
            imagined_outcome_y=-0.6,
            imagined_outcome_confidence=0.9,
            observed_outcome_y=0.75,
            human_prompt="Would you mark this as an outcome imagination/sign failure?",
        ),
    )


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = len(records)
    trusted = [record for record in records if record["confirmation"]["trusted"]]
    sensory_trusted = [record for record in records if record["confirmation"]["sensory_trusted"]]
    outcome_trusted = [record for record in records if record["confirmation"]["outcome_imagination_trusted"]]
    failed_by_reason: dict[str, int] = {}
    for record in records:
        for reason in record["confirmation"]["failed_senses"]:
            failed_by_reason[reason] = failed_by_reason.get(reason, 0) + 1
        for reason in record["confirmation"]["failed_outcome"]:
            failed_by_reason[f"outcome.{reason}"] = failed_by_reason.get(f"outcome.{reason}", 0) + 1
    return {
        "case_count": case_count,
        "trusted_count": len(trusted),
        "trusted_rate": len(trusted) / case_count if case_count else None,
        "sensory_trusted_count": len(sensory_trusted),
        "outcome_imagination_trusted_count": len(outcome_trusted),
        "failed_by_reason": failed_by_reason,
        "human_eval_required": True,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_human_eval(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [
        "# V034 Human Evaluation Sheet",
        "",
        "Fill `human_label` with accept, reject, or unsure. Use notes for why.",
        "",
    ]
    for record in records:
        outcome = record["outcome_imagination"]
        temporal = record["senses"]["temporal"]
        visual = record["senses"]["visual"]
        lines.extend(
            [
                f"## {record['state_id']}",
                "",
                f"- description: {record['case_description']}",
                f"- action: `{record['action']}`",
                f"- visual trusted: `{visual['map']['trusted']}`",
                f"- geometry projection trusted: `{visual['geometry_projection']['trusted']}`",
                f"- temporal trusted: `{temporal['trusted']}`",
                f"- imagined outcome: `{outcome['imagined']['signed_y']}` ({outcome['imagined']['polarity']}, confidence `{outcome['imagined']['confidence']}`)",
                f"- observed outcome: `{outcome['observed']['signed_y']}` ({outcome['observed']['polarity']})",
                f"- outcome trusted: `{outcome['trusted']}`",
                f"- combined trusted: `{record['confirmation']['trusted']}`",
                f"- prompt: {record['human_eval']['prompt']}",
                "- human_label:",
                "- human_notes:",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_results(path: Path, condition: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines = [
        f"# {condition['run_label']}",
        "",
        f"Run type: `{condition['run_type']}`",
        f"Cases: `{metrics['case_count']}`",
        f"Trusted count: `{metrics['trusted_count']}`",
        f"Sensory trusted count: `{metrics['sensory_trusted_count']}`",
        f"Outcome-imagination trusted count: `{metrics['outcome_imagination_trusted_count']}`",
        f"Failed by reason: `{metrics['failed_by_reason']}`",
        "",
        "Human eval file: `HUMAN_EVAL.md`",
        "",
        "No training data promoted. This is a deterministic smattering for human review.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _git_condition() -> dict[str, Any]:
    commit = _run_git("rev-parse", "HEAD")
    dirty = bool(_run_git("status", "--porcelain"))
    return {"git_commit": commit, "git_dirty": dirty}


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=False,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


if __name__ == "__main__":
    raise SystemExit(main())
