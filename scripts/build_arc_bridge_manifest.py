#!/usr/bin/env python3
"""Build a quarantined ARC transition bridge manifest for NanoWM.

This script converts ARC grid transition rows into the chronometric bridge
schema. It does not train a model and it does not remove quarantine status.
"""

from __future__ import annotations

import argparse
import glob
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

from chronometric_bridge import (  # noqa: E402
    DEFAULT_POTENTIAL_FAMILY_ORDER,
    bridge_record_from_arc_transition,
    read_jsonl,
    validate_bridge_manifest,
    write_jsonl,
)


DEFAULT_ARC_REPO = Path("/home/frosty40/world_model_1")
DEFAULT_SOURCE_TRANSITIONS = (
    "experiments/2026-05-04_v019b_target_discriminated_scorer_scout/"
    "grid/transition_events/v019b_current_state_v019b_target_discriminated_m0r0_seed0.transitions.jsonl"
)
DEFAULT_SOURCE_CONDITION = "experiments/2026-05-04_v019b_target_discriminated_scorer_scout/CONDITION.md"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_smoke"


def _git(repo: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_in_repo(repo: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo / path


def _rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def _source_transition_event_args(arc_repo: Path, args: argparse.Namespace) -> list[str]:
    values = list(args.source_transition_events or [])
    for pattern in args.source_transition_globs or []:
        if Path(pattern).is_absolute():
            matches = [Path(item) for item in sorted(glob.glob(pattern))]
        else:
            matches = sorted(arc_repo.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"no transition-event files matched {pattern!r}")
        values.extend(_rel(arc_repo, path) for path in matches)
    if not values:
        values = [DEFAULT_SOURCE_TRANSITIONS]
    return values


def build_bridge(args: argparse.Namespace) -> dict[str, Any]:
    arc_repo = args.arc_repo.resolve()
    source_paths = [_resolve_in_repo(arc_repo, item) for item in _source_transition_event_args(arc_repo, args)]
    condition_path = _resolve_in_repo(arc_repo, args.source_condition_artifact)
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    source_repo = _git(arc_repo, ["config", "--get", "remote.origin.url"])
    if source_repo == "unknown" or not source_repo:
        source_repo = str(arc_repo)
    source_commit = _git(arc_repo, ["rev-parse", "HEAD"])
    source_dirty = _git(arc_repo, ["status", "--short", "--untracked-files=all"]) != ""
    generator_commit = _git(ROOT, ["rev-parse", "HEAD"])
    generator_dirty = _git(ROOT, ["status", "--short", "--untracked-files=all"]) != ""

    records: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    for source_path in source_paths:
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        source_rel = _rel(arc_repo, source_path)
        rows = read_jsonl(source_path)
        if args.max_records > 0:
            rows = rows[: args.max_records]
        source_artifacts.append(
            {
                "path": source_rel,
                "sha256": _sha256(source_path),
                "input_rows": len(rows),
            }
        )
        for row in rows:
            records.append(
                bridge_record_from_arc_transition(
                    row,
                    source_repo=source_repo,
                    source_commit=source_commit,
                    source_artifact_path=source_rel,
                    source_condition_artifact=_rel(arc_repo, condition_path),
                    split=args.split,
                    family_order=args.family_order,
                )
            )

    manifest_path = out_dir / "arc_bridge_manifest.jsonl"
    write_jsonl(manifest_path, records)
    validation = validate_bridge_manifest(manifest_path)

    progress_records = sum(1 for record in records if record["progress_label"] == "progress_level_delta_positive")
    negative_records = sum(1 for record in records if record["signed_outcome_y"] < 0)
    positive_records = sum(1 for record in records if record["signed_outcome_y"] > 0)

    condition = {
        "run_label": args.run_label,
        "run_kind": "bridge_manifest_generation",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/build_arc_bridge_manifest.py",
        "generator_repo": str(ROOT),
        "generator_commit": generator_commit,
        "generator_dirty": generator_dirty,
        "source_repo": source_repo,
        "source_repo_path": str(arc_repo),
        "source_commit": source_commit,
        "source_dirty": source_dirty,
        "source_condition_artifact": _rel(arc_repo, condition_path),
        "source_condition_sha256": _sha256(condition_path) if condition_path.exists() else None,
        "source_artifacts": source_artifacts,
        "quarantine_status": "control_source: arc_scaffold_non_chronometric",
        "split": args.split,
        "family_order": list(args.family_order),
        "max_records_per_source": args.max_records,
        "arc_data_used": True,
        "training_data_promoted": False,
        "output_manifest": str(manifest_path.relative_to(ROOT)),
    }
    summary = {
        "condition": condition,
        "validation": validation,
        "records": len(records),
        "positive_signed_outcome_records": positive_records,
        "negative_signed_outcome_records": negative_records,
        "progress_records": progress_records,
        "action_counts": _count(records, "action_id"),
        "progress_labels": _count(records, "progress_label"),
        "control_labels": _count(records, "control_label"),
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _count(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    validation = summary["validation"]
    source_artifacts = condition["source_artifacts"]
    lines = [
        "# ARC Bridge Manifest Smoke Results",
        "",
        "Status: quarantined ARC transition rows converted into the NanoWM chronometric bridge schema.",
        "",
        "This is not training data promotion. The output keeps `control_source: arc_scaffold_non_chronometric` in every record.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- generator commit: `{condition['generator_commit']}`",
        f"- generator dirty at run: `{condition['generator_dirty']}`",
        f"- source repo: `{condition['source_repo']}`",
        f"- source commit: `{condition['source_commit']}`",
        f"- source dirty at run: `{condition['source_dirty']}`",
        f"- source condition: `{condition['source_condition_artifact']}`",
        f"- output manifest: `{condition['output_manifest']}`",
        "",
        "## Source Artifacts",
        "",
    ]
    for artifact in source_artifacts:
        lines.append(f"- `{artifact['path']}` rows=`{artifact['input_rows']}` sha256=`{artifact['sha256']}`")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- valid: `{validation['valid']}`",
            f"- records: `{validation['records']}`",
            f"- errors: `{len(validation['errors'])}`",
            f"- progress records: `{summary['progress_records']}`",
            f"- positive signed-outcome records: `{summary['positive_signed_outcome_records']}`",
            f"- negative signed-outcome records: `{summary['negative_signed_outcome_records']}`",
            "",
            "## Labels",
            "",
            f"- progress labels: `{summary['progress_labels']}`",
            f"- control labels: `{summary['control_labels']}`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument(
        "--source-transition-events",
        action="append",
        default=None,
        help="Transition-events JSONL path relative to --arc-repo. Can be repeated.",
    )
    parser.add_argument(
        "--source-transition-glob",
        action="append",
        dest="source_transition_globs",
        default=None,
        help="Glob for transition-events JSONL paths relative to --arc-repo. Can be repeated.",
    )
    parser.add_argument("--source-condition-artifact", default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_bridge_manifest_smoke")
    parser.add_argument("--split", default="arc_sprint0_v019b_m0r0_progress_bridge_v001")
    parser.add_argument("--max-records", type=int, default=0, help="0 means all rows from each source.")
    parser.add_argument("--family-order", nargs="+", default=list(DEFAULT_POTENTIAL_FAMILY_ORDER))
    args = parser.parse_args()
    return args


def main() -> int:
    summary = build_bridge(parse_args())
    print(json.dumps({"records": summary["records"], "valid": summary["validation"]["valid"]}, indent=2))
    return 0 if summary["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
