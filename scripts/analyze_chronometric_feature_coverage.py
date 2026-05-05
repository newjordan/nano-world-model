#!/usr/bin/env python3
"""Analyze train/heldout feature coverage for chronometric calibration runs."""

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

from chronometric_bridge import read_jsonl  # noqa: E402
from chronometric_bucket_eval import join_predictions_to_manifest  # noqa: E402
from chronometric_calibration import FEATURE_NAMES, records_with_temporal_context  # noqa: E402
from chronometric_feature_coverage import (  # noqa: E402
    nearest_train_groups,
    summarize_feature_groups,
    top_heldout_error_groups,
)


DEFAULT_MANIFEST = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_v006_cross_family" / "arc_bridge_manifest.jsonl"
DEFAULT_PREDICTIONS = (
    ROOT
    / "experiments"
    / "2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout"
    / "predictions.jsonl"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_feature_coverage_v007b"


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


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest.resolve()
    predictions_path = args.predictions.resolve()

    manifest_records = records_with_temporal_context(read_jsonl(manifest_path))
    prediction_records = read_jsonl(predictions_path)
    joined = join_predictions_to_manifest(manifest_records, prediction_records)
    groups = summarize_feature_groups(joined)
    nearest = nearest_train_groups(groups)
    top_errors = top_heldout_error_groups(groups)
    condition = {
        "run_label": args.run_label,
        "run_kind": "diagnostic_analysis_no_training",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/analyze_chronometric_feature_coverage.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "manifest": _rel(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "predictions": _rel(predictions_path),
        "predictions_sha256": _sha256(predictions_path),
        "records": len(joined),
        "feature_names": list(FEATURE_NAMES),
        "training_data_promoted": False,
    }
    summary = {
        "condition": condition,
        "groups": groups,
        "nearest_train_by_action_control": nearest,
        "top_heldout_action_control_errors": [
            {"label": label, **stats, "nearest_train": nearest.get(label)}
            for label, stats in top_errors
        ],
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "feature_coverage.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    rows = summary["top_heldout_action_control_errors"]
    lines = [
        "# Chronometric Feature Coverage Results",
        "",
        f"Status: posthoc feature-coverage diagnostic for `{condition['run_label']}`.",
        "",
        "This is not a new training run and not ARC solve evidence. It compares heldout feature buckets to train feature buckets.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- manifest: `{condition['manifest']}`",
        f"- predictions: `{condition['predictions']}`",
        f"- records: `{condition['records']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Top Heldout Action-Control Errors",
        "",
        "| bucket | rows | signed MAE | signed bias | nearest train bucket | distance | same-label train rows | same-label distance |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        nearest = row.get("nearest_train") or {}
        lines.append(
            "| {label} | {records} | {mae} | {bias} | {nearest_label} | {distance} | {same_rows} | {same_distance} |".format(
                label=row["label"],
                records=row["records"],
                mae=_fmt(row.get("signed_mae")),
                bias=_fmt(row.get("signed_bias")),
                nearest_label=nearest.get("nearest_train_label", ""),
                distance=_fmt(nearest.get("nearest_distance")),
                same_rows=_fmt(nearest.get("same_label_train_records")),
                same_distance=_fmt(nearest.get("same_label_distance")),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- high same-label distance means train contains the same action/control label but under different feature conditions",
            "- missing same-label train rows means the heldout bucket is outside the train action/control coverage",
            "- use this diagnostic to decide whether the next step is data coverage, feature engineering, or an objective change",
            "",
        ]
    )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return ""
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="chronometric_feature_coverage_v007b")
    return parser.parse_args()


def main() -> int:
    summary = analyze(parse_args())
    top_errors = summary["top_heldout_action_control_errors"]
    print(
        json.dumps(
            {
                "records": summary["condition"]["records"],
                "top_heldout_bucket": top_errors[0]["label"] if top_errors else None,
                "top_heldout_signed_mae": top_errors[0]["signed_mae"] if top_errors else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
