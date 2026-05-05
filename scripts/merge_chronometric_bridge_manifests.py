#!/usr/bin/env python3
"""Merge already-conditioned chronometric bridge manifests."""

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

from chronometric_bridge import read_jsonl, validate_bridge_manifest, write_jsonl  # noqa: E402


DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_v006_cross_family"


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


def merge(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_paths = [path.resolve() for path in args.manifest]
    records: list[dict[str, Any]] = []
    source_manifests: list[dict[str, Any]] = []
    for path in manifest_paths:
        if not path.exists():
            raise FileNotFoundError(path)
        rows = read_jsonl(path)
        if not rows:
            raise ValueError(f"manifest had no rows: {path}")
        records.extend(rows)
        source_manifests.append(
            {
                "path": _rel(path),
                "sha256": _sha256(path),
                "records": len(rows),
                "source_condition_artifacts": sorted(
                    {str(row.get("source_condition_artifact", "")) for row in rows}
                ),
            }
        )

    manifest_path = out_dir / "arc_bridge_manifest.jsonl"
    write_jsonl(manifest_path, records)
    validation = validate_bridge_manifest(manifest_path)
    progress_records = sum(1 for record in records if record["progress_label"] == "progress_level_delta_positive")
    negative_records = sum(1 for record in records if record["signed_outcome_y"] < 0)
    positive_records = sum(1 for record in records if record["signed_outcome_y"] > 0)
    condition = {
        "run_label": args.run_label,
        "run_kind": "bridge_manifest_merge",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/merge_chronometric_bridge_manifests.py",
        "generator_repo": str(ROOT),
        "generator_commit": _git(["rev-parse", "HEAD"]),
        "generator_dirty": _git_dirty(ignored_paths=[out_dir]),
        "source_manifests": source_manifests,
        "quarantine_status": "control_source: arc_scaffold_non_chronometric",
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
        "source_condition_artifacts": _count(records, "source_condition_artifact"),
        "source_artifact_paths": _count(records, "source_artifact_path"),
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
    lines = [
        "# ARC Bridge Manifest Merge Results",
        "",
        "Status: already-conditioned bridge manifests merged without changing per-record provenance.",
        "",
        "This is not training data promotion. Source condition artifacts remain attached to each record.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- generator commit: `{condition['generator_commit']}`",
        f"- generator dirty at run: `{condition['generator_dirty']}`",
        f"- output manifest: `{condition['output_manifest']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Source Manifests",
        "",
    ]
    for manifest in condition["source_manifests"]:
        lines.append(
            f"- `{manifest['path']}` rows=`{manifest['records']}` conditions=`{manifest['source_condition_artifacts']}`"
        )
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
            "## Source Conditions",
            "",
            f"- source condition counts: `{summary['source_condition_artifacts']}`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_bridge_manifest_v006_cross_family")
    return parser.parse_args()


def main() -> int:
    summary = merge(parse_args())
    print(json.dumps({"records": summary["records"], "valid": summary["validation"]["valid"]}, indent=2))
    return 0 if summary["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
