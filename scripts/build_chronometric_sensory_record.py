#!/usr/bin/env python
"""Build one visual+temporal sensory confirmation record."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_map_perception import ColorLabel  # noqa: E402
from chronometric_sensory_alignment import build_sensory_confirmation_record  # noqa: E402


def main() -> int:
    args = _parse_args()
    labels = _load_labels(args.labels)
    playable_values = _parse_values(args.playable_values)
    wall_values = _parse_values(args.wall_values)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    record = build_sensory_confirmation_record(
        state_id=args.state_id,
        action=args.action,
        predicted_grid=_load_json(args.predicted_grid),
        truth_grid=_load_json(args.truth_grid),
        predicted_after_grid=_load_json(args.predicted_after_grid),
        actual_after_grid=_load_json(args.actual_after_grid),
        labels=labels,
        playable_values=playable_values,
        wall_values=wall_values,
        imagined_outcome_y=args.imagined_outcome_y,
        imagined_outcome_confidence=args.imagined_outcome_confidence,
        signed_outcome_y=args.signed_outcome_y,
    )
    condition = {
        "run_label": args.run_label,
        "run_type": "chronometric_sensory_alignment_v033",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state_id": args.state_id,
        "action": args.action,
        "predicted_grid": str(args.predicted_grid),
        "truth_grid": str(args.truth_grid),
        "predicted_after_grid": str(args.predicted_after_grid),
        "actual_after_grid": str(args.actual_after_grid),
        "labels": str(args.labels),
        "playable_values": playable_values,
        "wall_values": wall_values,
        "imagined_outcome_y": args.imagined_outcome_y,
        "imagined_outcome_confidence": args.imagined_outcome_confidence,
        "observed_signed_outcome_y_attached": args.signed_outcome_y is not None,
        "training_data_promoted": False,
        **_git_condition(),
    }

    _write_json(out_dir / "condition.json", condition)
    _write_json(out_dir / "sensory_record.json", record)
    _write_results(out_dir / "RESULTS.md", condition, record)
    return 0 if record["confirmation"]["trusted"] else 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--state-id", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--predicted-grid", required=True, type=Path)
    parser.add_argument("--truth-grid", required=True, type=Path)
    parser.add_argument("--predicted-after-grid", required=True, type=Path)
    parser.add_argument("--actual-after-grid", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--playable-values", default="0")
    parser.add_argument("--wall-values", default="")
    parser.add_argument("--imagined-outcome-y", required=True, type=float)
    parser.add_argument("--imagined-outcome-confidence", type=float, default=1.0)
    parser.add_argument("--signed-outcome-y", type=float, default=None)
    return parser.parse_args()


def _load_labels(path: Path) -> tuple[ColorLabel, ...]:
    raw = _load_json(path)
    labels = []
    for entry in raw:
        labels.append(
            ColorLabel(
                value=int(entry["value"]),
                rgb=tuple(int(channel) for channel in entry["rgb"]),
                name=str(entry["name"]),
            )
        )
    return tuple(labels)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_values(raw: str) -> tuple[int, ...]:
    if not raw.strip():
        return ()
    return tuple(int(part.strip()) for part in raw.split(",") if part.strip())


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


def _write_results(path: Path, condition: dict[str, Any], record: dict[str, Any]) -> None:
    visual = record["senses"]["visual"]
    temporal = record["senses"]["temporal"]
    outcome = record["outcome_imagination"]
    lines = [
        f"# {condition['run_label']}",
        "",
        f"Run type: `{condition['run_type']}`",
        f"Trusted: `{record['confirmation']['trusted']}`",
        "",
        "## Visual Sense",
        "",
        f"- map trusted: `{visual['map']['trusted']}`",
        f"- cell accuracy: `{visual['map']['cell_accuracy']}`",
        f"- ray exact accuracy: `{visual['map']['ray']['ray_exact_accuracy']}`",
        f"- geometry projection trusted: `{visual['geometry_projection']['trusted']}`",
        "",
        "## Temporal Sense",
        "",
        f"- temporal trusted: `{temporal['trusted']}`",
        f"- transition cell accuracy: `{temporal['transition_cell_accuracy']}`",
        f"- change recall: `{temporal['change_recall']}`",
        f"- actual change count: `{temporal['actual_change_count']}`",
        "",
        "## Outcome Imagination",
        "",
        f"- imagined signed_y: `{outcome['imagined']['signed_y']}`",
        f"- imagined polarity: `{outcome['imagined']['polarity']}`",
        f"- imagined confidence: `{outcome['imagined']['confidence']}`",
        f"- observed signed_y: `{outcome['observed']['signed_y']}`",
        f"- observed polarity: `{outcome['observed']['polarity']}`",
        f"- polarity match: `{outcome['comparison']['polarity_match']}`",
        f"- signed abs error: `{outcome['comparison']['signed_abs_error']}`",
        f"- outcome imagination trusted: `{outcome['trusted']}`",
        "",
        "## Condition",
        "",
        f"- state id: `{condition['state_id']}`",
        f"- action: `{condition['action']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty: `{condition['git_dirty']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
