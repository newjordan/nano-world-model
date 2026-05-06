#!/usr/bin/env python3
"""Apply a train-built chronometric branch library to calibration predictions."""

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

from chronometric_branch_library import (  # noqa: E402
    BRANCH_LIBRARY_FALLBACK_SCOPES,
    BRANCH_LIBRARY_SCOPES,
    blend_branch_library_signed_y,
    build_chronometric_branch_library,
)
from chronometric_bridge import read_jsonl  # noqa: E402
from chronometric_bucket_eval import join_predictions_to_manifest, summarize_rows  # noqa: E402


DEFAULT_MANIFEST = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout" / "arc_bridge_manifest.jsonl"
DEFAULT_PREDICTIONS = (
    ROOT
    / "experiments"
    / "2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu"
    / "predictions.jsonl"
)
DEFAULT_CALIBRATION_METRICS = (
    ROOT
    / "experiments"
    / "2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu"
    / "metrics.json"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_branch_library_v020"


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


def apply_library(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest.resolve()
    predictions_path = args.predictions.resolve()
    metrics_path = args.calibration_metrics.resolve()

    joined = join_predictions_to_manifest(read_jsonl(manifest_path), read_jsonl(predictions_path))
    library = build_chronometric_branch_library(
        joined,
        min_records=args.min_records,
        scope=args.library_scope,
    )
    adjusted = [
        _adjust_prediction(
            row,
            library,
            blend=args.blend,
            fallback_scope=args.fallback_scope,
        )
        for row in joined
    ]
    split_rows: dict[str, list[dict[str, Any]]] = {}
    for row in adjusted:
        split_rows.setdefault(str(row.get("split", "unknown")), []).append(row)

    condition = {
        "run_label": args.run_label,
        "run_kind": "branch_library_posthoc_inference",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/apply_chronometric_branch_library.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "manifest": _rel(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "input_predictions": _rel(predictions_path),
        "input_predictions_sha256": _sha256(predictions_path),
        "calibration_metrics": _rel(metrics_path),
        "calibration_metrics_sha256": _sha256(metrics_path),
        "blend": args.blend,
        "min_records": args.min_records,
        "library_scope": args.library_scope,
        "fallback_scope": args.fallback_scope,
        "fallback_source_field": _fallback_source_field(args.fallback_scope),
        "library_key_strategy": "action_control_grid_coordinate_or_changed_cells",
        "library_source_split": "train",
        "library_source_field": "target_signed_y",
        "heldout_labels_used": False,
        "training_data_promoted": False,
    }
    library_summary = {
        key: {"records": entry.records, "signed_y_mean": entry.signed_y_mean}
        for key, entry in sorted(library.items())
    }
    summary = {
        "condition": condition,
        "library": library_summary,
        "library_entries": len(library),
        "adjusted_records": sum(1 for row in adjusted if row.get("branch_library_applied")),
        "fallback_records": sum(1 for row in adjusted if row.get("branch_library_fallback_applied")),
        "adjusted_records_by_split": {
            split: sum(1 for row in rows if row.get("branch_library_applied"))
            for split, rows in sorted(split_rows.items())
        },
        "fallback_records_by_split": {
            split: sum(1 for row in rows if row.get("branch_library_fallback_applied"))
            for split, rows in sorted(split_rows.items())
        },
        "by_split": {split: summarize_rows(rows) for split, rows in sorted(split_rows.items())},
        "overall": summarize_rows(adjusted),
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_jsonl(out_dir / "predictions.jsonl", adjusted)
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _adjust_prediction(
    row: dict[str, Any],
    library: dict[str, Any],
    *,
    blend: float,
    fallback_scope: str,
) -> dict[str, Any]:
    adjusted_signed, entry = blend_branch_library_signed_y(
        row,
        library,
        blend=blend,
        fallback_scope=fallback_scope,
    )
    fallback_applied = entry is not None and entry.records == 0 and entry.key.startswith("fallback:")
    output = dict(row)
    output["pred_signed_y_raw"] = row.get("pred_signed_y")
    output["pred_signed_y"] = adjusted_signed
    output["branch_library_applied"] = entry is not None
    output["branch_library_fallback_applied"] = fallback_applied
    output["branch_library_key"] = entry.key if entry is not None else None
    output["branch_library_records"] = entry.records if entry is not None else 0
    output["branch_library_signed_y"] = entry.signed_y_mean if entry is not None else None
    output["branch_library_blend"] = blend if entry is not None else 0.0
    return output


def _fallback_source_field(fallback_scope: str) -> str | None:
    if fallback_scope == "dominant_translation_potential":
        return "potential_family_vector.transition.changed_cells"
    if fallback_scope == "dominant_time_phase_potential":
        return "potential_family_vector.time_phase.repeated_effect_size+transition.changed_cells"
    if fallback_scope == "time_phase_translation_potential":
        return (
            "potential_family_vector.time_phase.repeated_effect_size+"
            "transition.changed_cells;transition.changed_cells"
        )
    return None


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    heldout = summary["by_split"].get("heldout", {})
    train = summary["by_split"].get("train", {})
    return "\n".join(
        [
            "# Chronometric Branch Library Results",
            "",
            f"Status: posthoc branch-library inference for `{condition['run_label']}`.",
            "",
            "This is not a new training run and not training-data promotion. The library is built from train targets only.",
            "",
            "## Condition",
            "",
            f"- run label: `{condition['run_label']}`",
            f"- run kind: `{condition['run_kind']}`",
            f"- git commit: `{condition['git_commit']}`",
            f"- git dirty at run: `{condition['git_dirty']}`",
            f"- manifest: `{condition['manifest']}`",
            f"- input predictions: `{condition['input_predictions']}`",
            f"- blend: `{condition['blend']}`",
            f"- min records: `{condition['min_records']}`",
            f"- library scope: `{condition['library_scope']}`",
            f"- fallback scope: `{condition['fallback_scope']}`",
            f"- fallback source field: `{condition['fallback_source_field']}`",
            f"- library key strategy: `{condition['library_key_strategy']}`",
            f"- library entries: `{summary['library_entries']}`",
            f"- adjusted records: `{summary['adjusted_records']}`",
            f"- fallback records: `{summary['fallback_records']}`",
            f"- heldout labels used: `{condition['heldout_labels_used']}`",
            f"- training data promoted: `{condition['training_data_promoted']}`",
            "",
            "## Metrics",
            "",
            f"- train signed-Y MAE: `{train.get('signed_mae')}`",
            f"- heldout signed-Y MAE: `{heldout.get('signed_mae')}`",
            f"- heldout progress accuracy: `{heldout.get('progress_accuracy')}`",
            f"- heldout adjusted records: `{summary['adjusted_records_by_split'].get('heldout')}`",
            f"- heldout fallback records: `{summary['fallback_records_by_split'].get('heldout')}`",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--calibration-metrics", type=Path, default=DEFAULT_CALIBRATION_METRICS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="chronometric_branch_library_v020")
    parser.add_argument("--blend", type=float, default=1.0)
    parser.add_argument("--min-records", type=int, default=1)
    parser.add_argument("--library-scope", choices=BRANCH_LIBRARY_SCOPES, default="action6_time_phase")
    parser.add_argument("--fallback-scope", choices=BRANCH_LIBRARY_FALLBACK_SCOPES, default="none")
    return parser.parse_args()


def main() -> int:
    summary = apply_library(parse_args())
    heldout = summary["by_split"].get("heldout", {})
    print(
        json.dumps(
            {
                "library_entries": summary["library_entries"],
                "adjusted_records": summary["adjusted_records"],
                "fallback_records": summary["fallback_records"],
                "heldout_signed_mae": heldout.get("signed_mae"),
                "heldout_progress_accuracy": heldout.get("progress_accuracy"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
