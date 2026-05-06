#!/usr/bin/env python3
"""Select branches from chronometric planner score rows."""

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

from chronometric_branch_selection import (  # noqa: E402
    DEFAULT_GROUP_FIELDS,
    SCORE_POLICIES,
    select_chronometric_branches,
    summarize_branch_selection,
)
from chronometric_bridge import read_jsonl  # noqa: E402


DEFAULT_INPUT = (
    ROOT
    / "experiments"
    / "2026-05-05_chronometric_planner_branch_score_v027_v015_holdout_cross_family"
    / "planner_scores.jsonl"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_branch_selection_v028"


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


def run_selection(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.input.resolve()

    rows = read_jsonl(input_path)
    selected = select_chronometric_branches(
        rows,
        group_fields=args.group_fields,
        score_policy=args.score_policy,
        min_group_size=args.min_group_size,
    )
    selection_summary = summarize_branch_selection(
        selected,
        candidate_rows=rows,
        group_fields=args.group_fields,
        min_group_size=args.min_group_size,
    )
    condition = {
        "run_label": args.run_label,
        "run_kind": "branch_selection_smoke",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/select_chronometric_branches.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "input_planner_scores": _rel(input_path),
        "input_planner_scores_sha256": _sha256(input_path),
        "group_fields": list(args.group_fields),
        "score_policy": args.score_policy,
        "min_group_size": args.min_group_size,
        "selection_uses_target_labels": False,
        "metrics_use_target_labels": True,
        "training_data_promoted": False,
    }
    summary = {
        "condition": condition,
        **selection_summary,
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_jsonl(out_dir / "branch_selections.jsonl", selected)
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    overall = summary["overall"]
    heldout = summary["by_split"].get("heldout", {})
    return "\n".join(
        [
            "# Chronometric Branch Selection Results",
            "",
            f"Status: branch selection smoke for `{condition['run_label']}`.",
            "",
            "This is not a training run and not ARC solve evidence. Selection uses",
            "chronometric scores only; target labels are used only for diagnostics.",
            "",
            "## Condition",
            "",
            f"- run label: `{condition['run_label']}`",
            f"- run kind: `{condition['run_kind']}`",
            f"- git commit: `{condition['git_commit']}`",
            f"- git dirty at run: `{condition['git_dirty']}`",
            f"- input planner scores: `{condition['input_planner_scores']}`",
            f"- group fields: `{condition['group_fields']}`",
            f"- score policy: `{condition['score_policy']}`",
            f"- min group size: `{condition['min_group_size']}`",
            f"- selection uses target labels: `{condition['selection_uses_target_labels']}`",
            f"- metrics use target labels: `{condition['metrics_use_target_labels']}`",
            f"- training data promoted: `{condition['training_data_promoted']}`",
            "",
            "## Metrics",
            "",
            f"- candidate records: `{summary['candidate_records']}`",
            f"- groups: `{summary['groups']}`",
            f"- selectable groups: `{summary['selectable_groups']}`",
            f"- selected records: `{summary['selected_records']}`",
            f"- skipped groups: `{summary['skipped_groups']}`",
            f"- overall oracle signed-best match rate: `{overall.get('oracle_signed_best_match_rate')}`",
            f"- overall mean selected target signed-Y: `{overall.get('mean_target_signed_y')}`",
            f"- overall progress-positive selected: `{overall.get('progress_positive_selected')}`",
            f"- heldout selected records: `{heldout.get('selected_records')}`",
            f"- heldout oracle signed-best match rate: `{heldout.get('oracle_signed_best_match_rate')}`",
            f"- heldout mean selected target signed-Y: `{heldout.get('mean_target_signed_y')}`",
            f"- heldout progress-positive selected: `{heldout.get('progress_positive_selected')}`",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="chronometric_branch_selection_v028")
    parser.add_argument("--group-fields", nargs="+", default=list(DEFAULT_GROUP_FIELDS))
    parser.add_argument("--score-policy", choices=SCORE_POLICIES, default="library_or_calibration")
    parser.add_argument("--min-group-size", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    summary = run_selection(parse_args())
    heldout = summary["by_split"].get("heldout", {})
    print(
        json.dumps(
            {
                "candidate_records": summary["candidate_records"],
                "selectable_groups": summary["selectable_groups"],
                "selected_records": summary["selected_records"],
                "overall_oracle_signed_best_match_rate": summary["overall"].get("oracle_signed_best_match_rate"),
                "heldout_selected_records": heldout.get("selected_records"),
                "heldout_oracle_signed_best_match_rate": heldout.get("oracle_signed_best_match_rate"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
