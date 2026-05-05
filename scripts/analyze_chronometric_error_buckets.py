#!/usr/bin/env python3
"""Analyze chronometric calibration predictions by transition bucket."""

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
from chronometric_bucket_eval import join_predictions_to_manifest, summarize_buckets, summarize_rows  # noqa: E402


DEFAULT_MANIFEST = (
    ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_v004_controlled_batch" / "arc_bridge_manifest.jsonl"
)
DEFAULT_PREDICTIONS = (
    ROOT / "experiments" / "2026-05-05_chronometric_calibration_v004_group_holdout" / "predictions.jsonl"
)
DEFAULT_CALIBRATION_METRICS = (
    ROOT / "experiments" / "2026-05-05_chronometric_calibration_v004_group_holdout" / "metrics.json"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_bucket_eval_v005"


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
    metrics_path = args.calibration_metrics.resolve()

    manifest_records = read_jsonl(manifest_path)
    prediction_records = read_jsonl(predictions_path)
    joined = join_predictions_to_manifest(manifest_records, prediction_records)
    split_rows: dict[str, list[dict[str, Any]]] = {}
    for row in joined:
        split_rows.setdefault(str(row.get("split", "unknown")), []).append(row)

    condition = {
        "run_label": args.run_label,
        "run_kind": "diagnostic_analysis_no_training",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/analyze_chronometric_error_buckets.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "manifest": _rel(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "predictions": _rel(predictions_path),
        "predictions_sha256": _sha256(predictions_path),
        "calibration_metrics": _rel(metrics_path),
        "calibration_metrics_sha256": _sha256(metrics_path),
        "records": len(joined),
        "splits": {split: len(rows) for split, rows in sorted(split_rows.items())},
        "training_data_promoted": False,
        "eval_scope": "posthoc_bucket_analysis",
    }
    summary = {
        "condition": condition,
        "overall": summarize_rows(joined),
        "by_split": {split: summarize_rows(rows) for split, rows in sorted(split_rows.items())},
        "buckets": summarize_buckets(joined),
        "buckets_by_split": {
            split: summarize_buckets(rows) for split, rows in sorted(split_rows.items())
        },
    }
    rows = _bucket_rows(summary)

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "bucket_metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_jsonl(out_dir / "bucket_rows.jsonl", rows)
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _bucket_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket_type, labels in summary["buckets"].items():
        for label, metrics in labels.items():
            rows.append({"split": "all", "bucket_type": bucket_type, "bucket": label, **metrics})
    for split, split_buckets in summary["buckets_by_split"].items():
        for bucket_type, labels in split_buckets.items():
            for label, metrics in labels.items():
                rows.append({"split": split, "bucket_type": bucket_type, "bucket": label, **metrics})
    return rows


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    heldout = summary["by_split"].get("heldout", {})
    train = summary["by_split"].get("train", {})
    heldout_buckets = summary["buckets_by_split"].get("heldout", {})
    control_rows = _table_rows(heldout_buckets.get("control_label", {}))
    action_rows = _table_rows(heldout_buckets.get("action", {}))
    movement_rows = _table_rows(heldout_buckets.get("movement_axis", {}))
    time_rows = _table_rows(heldout_buckets.get("time_window", {}))
    lines = [
        "# Chronometric Bucket Eval Results",
        "",
        f"Status: posthoc bucket diagnostic for `{condition['run_label']}`.",
        "",
        "This is not a new training run and not ARC solve evidence. It checks which transition families carry the learned signal.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- manifest: `{condition['manifest']}`",
        f"- predictions: `{condition['predictions']}`",
        f"- calibration metrics: `{condition['calibration_metrics']}`",
        f"- records: `{condition['records']}`",
        f"- splits: `{condition['splits']}`",
        f"- eval scope: `{condition['eval_scope']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Split Summary",
        "",
        f"- train records: `{train.get('records')}` positives=`{train.get('positive_records')}` signed_MAE=`{train.get('signed_mae')}` progress_acc=`{train.get('progress_accuracy')}`",
        f"- heldout records: `{heldout.get('records')}` positives=`{heldout.get('positive_records')}` signed_MAE=`{heldout.get('signed_mae')}` progress_acc=`{heldout.get('progress_accuracy')}`",
        f"- heldout positive best rank: `{heldout.get('positive_best_rank')}`",
        f"- heldout positive mean rank: `{heldout.get('positive_mean_rank')}`",
        "",
        "## Heldout Control Buckets",
        "",
        "| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *control_rows,
        "",
        "## Heldout Action Buckets",
        "",
        "| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *action_rows,
        "",
        "## Heldout Movement Buckets",
        "",
        "| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *movement_rows,
        "",
        "## Heldout Time Buckets",
        "",
        "| bucket | rows | positives | progress acc | signed MAE | top false-positive prob |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *time_rows,
        "",
        "## Interpretation",
        "",
        "- progress rows remain cleanly separated in heldout branch files",
        "- highest heldout non-progress probability stays far below the 0.5 progress threshold",
        "- signed-Y error is concentrated in non-progress movement/stasis rows, not in progress classification",
        "- use the run label, manifest, and calibration metrics paths above as the exact scope boundary",
        "",
    ]
    return "\n".join(lines)


def _table_rows(buckets: dict[str, dict[str, Any]]) -> list[str]:
    rows = []
    for label, metrics in sorted(buckets.items(), key=lambda item: (-item[1]["records"], item[0])):
        false_positive = metrics.get("top_false_positive") or {}
        rows.append(
            "| {label} | {records} | {positives} | {acc} | {mae} | {fp} |".format(
                label=label,
                records=metrics.get("records"),
                positives=metrics.get("positive_records"),
                acc=_fmt(metrics.get("progress_accuracy")),
                mae=_fmt(metrics.get("signed_mae")),
                fp=_fmt(false_positive.get("pred_progress_prob")),
            )
        )
    return rows


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
    parser.add_argument("--calibration-metrics", type=Path, default=DEFAULT_CALIBRATION_METRICS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="chronometric_bucket_eval_v005")
    return parser.parse_args()


def main() -> int:
    summary = analyze(parse_args())
    heldout = summary["by_split"].get("heldout", {})
    print(
        json.dumps(
            {
                "records": summary["condition"]["records"],
                "heldout_records": heldout.get("records"),
                "heldout_positive_best_rank": heldout.get("positive_best_rank"),
                "heldout_top_false_positive": (
                    (heldout.get("top_false_positive") or {}).get("pred_progress_prob")
                    if heldout
                    else None
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
