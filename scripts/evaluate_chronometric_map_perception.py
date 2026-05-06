#!/usr/bin/env python
"""Evaluate labeled map perception, geometry, and ray accuracy."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_map_perception import (  # noqa: E402
    ColorLabel,
    build_grid_geometry,
    evaluate_grid_perception,
    label_image_to_grid,
)


def main() -> int:
    args = _parse_args()
    labels = _load_labels(args.labels)
    truth_grid = _load_json(args.truth_grid)
    playable_values = _parse_values(args.playable_values)
    wall_values = _parse_values(args.wall_values)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    predicted_grid = label_image_to_grid(
        args.predicted_image,
        labels,
        cell_size=args.cell_size,
        tolerance=args.tolerance,
        unknown_label=args.unknown_label,
    )
    geometry = build_grid_geometry(
        predicted_grid,
        labels,
        playable_values=playable_values,
        wall_values=wall_values,
        cell_size=args.geometry_cell_size,
        blocker_height=args.blocker_height,
        object_height=args.object_height,
    )
    metrics = evaluate_grid_perception(
        predicted_grid,
        truth_grid,
        playable_values=playable_values,
        wall_values=wall_values,
        min_cell_accuracy=args.min_cell_accuracy,
        min_height_accuracy=args.min_height_accuracy,
        min_ray_exact_accuracy=args.min_ray_exact_accuracy,
    )
    condition = {
        "run_label": args.run_label,
        "run_type": "chronometric_map_perception_v031",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "predicted_image": str(args.predicted_image),
        "truth_grid": str(args.truth_grid),
        "labels": str(args.labels),
        "cell_size": args.cell_size,
        "tolerance": args.tolerance,
        "unknown_label": args.unknown_label,
        "playable_values": playable_values,
        "wall_values": wall_values,
        "geometry_cell_size": args.geometry_cell_size,
        "blocker_height": args.blocker_height,
        "object_height": args.object_height,
        "min_cell_accuracy": args.min_cell_accuracy,
        "min_height_accuracy": args.min_height_accuracy,
        "min_ray_exact_accuracy": args.min_ray_exact_accuracy,
        "training_data_promoted": False,
        **_git_condition(),
    }

    _write_json(out_dir / "condition.json", condition)
    _write_json(out_dir / "predicted_grid.json", predicted_grid)
    _write_json(out_dir / "geometry.json", asdict(geometry))
    _write_json(out_dir / "metrics.json", metrics)
    _write_results(out_dir / "RESULTS.md", condition, metrics)

    return 0 if metrics["trusted"] else 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--predicted-image", required=True, type=Path)
    parser.add_argument("--truth-grid", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--cell-size", type=int, default=1)
    parser.add_argument("--tolerance", type=int, default=0)
    parser.add_argument("--unknown-label", type=int, default=-1)
    parser.add_argument("--playable-values", default="0")
    parser.add_argument("--wall-values", default="")
    parser.add_argument("--geometry-cell-size", type=float, default=1.0)
    parser.add_argument("--blocker-height", type=float, default=1.0)
    parser.add_argument("--object-height", type=float, default=0.5)
    parser.add_argument("--min-cell-accuracy", type=float, default=1.0)
    parser.add_argument("--min-height-accuracy", type=float, default=1.0)
    parser.add_argument("--min-ray-exact-accuracy", type=float, default=1.0)
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


def _write_results(path: Path, condition: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines = [
        f"# {condition['run_label']}",
        "",
        f"Run type: `{condition['run_type']}`",
        f"Trusted: `{metrics['trusted']}`",
        "",
        "## Gate",
        "",
        f"- cell accuracy: `{metrics['cell_accuracy']}`",
        f"- height accuracy: `{metrics['height_accuracy']}`",
        f"- ray exact accuracy: `{metrics['ray']['ray_exact_accuracy']}`",
        f"- gate failures: `{metrics['gate_failures']}`",
        "",
        "## Condition",
        "",
        f"- predicted image: `{condition['predicted_image']}`",
        f"- truth grid: `{condition['truth_grid']}`",
        f"- labels: `{condition['labels']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty: `{condition['git_dirty']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
