#!/usr/bin/env python3
"""Score chronometric bridge branches through the planner-facing scorer."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_branch_library import (  # noqa: E402
    BRANCH_LIBRARY_FALLBACK_SCOPES,
    BRANCH_LIBRARY_SCOPES,
    build_chronometric_branch_library,
)
from chronometric_bridge import read_jsonl  # noqa: E402
from chronometric_bucket_eval import join_predictions_to_manifest  # noqa: E402
from chronometric_planner_scoring import (  # noqa: E402
    score_chronometric_branch_rows,
    summarize_planner_branch_scores,
)
from models.chronometric_contortion import ChronometricConfig, ChronometricContortionLayer  # noqa: E402


DEFAULT_MANIFEST = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout" / "arc_bridge_manifest.jsonl"
DEFAULT_PREDICTIONS = (
    ROOT
    / "experiments"
    / "2026-05-05_chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu"
    / "predictions.jsonl"
)
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_planner_branch_score_v027"


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


def score_planner_branches(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest.resolve()
    predictions_path = args.predictions.resolve()

    joined = join_predictions_to_manifest(read_jsonl(manifest_path), read_jsonl(predictions_path))
    library = build_chronometric_branch_library(
        joined,
        min_records=args.min_records,
        scope=args.library_scope,
    )

    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    layer = ChronometricContortionLayer(
        hidden_size=args.hidden_size,
        config=ChronometricConfig(
            mode="branch_rollout",
            potential_families=args.potential_families,
        ),
    ).to(device)
    layer.eval()

    scored = score_chronometric_branch_rows(
        layer,
        joined,
        branch_library=library,
        branch_library_blend=args.blend,
        branch_library_fallback_scope=args.fallback_scope,
        hidden_size=args.hidden_size,
        frames=args.frames,
        batch_size=args.batch_size,
        device=device,
    )
    score_summary = summarize_planner_branch_scores(scored)

    condition = {
        "run_label": args.run_label,
        "run_kind": "planner_branch_scoring_smoke",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/score_chronometric_planner_branches.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "manifest": _rel(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "input_predictions": _rel(predictions_path),
        "input_predictions_sha256": _sha256(predictions_path),
        "scorer_surface": "score_chronometric_branch_or_score_branch",
        "scorer_impl": "ChronometricContortionLayer.score_branch",
        "seed": args.seed,
        "device": args.device,
        "hidden_size": args.hidden_size,
        "frames": args.frames,
        "batch_size": args.batch_size,
        "potential_families": args.potential_families,
        "blend": args.blend,
        "min_records": args.min_records,
        "library_scope": args.library_scope,
        "fallback_scope": args.fallback_scope,
        "library_source_split": "train",
        "library_source_field": "target_signed_y",
        "heldout_labels_used": False,
        "training_data_promoted": False,
    }
    summary = {
        "condition": condition,
        "library_entries": len(library),
        **score_summary,
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_jsonl(out_dir / "planner_scores.jsonl", scored)
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    heldout = summary["by_split"].get("heldout", {})
    overall = summary["overall"]
    return "\n".join(
        [
            "# Chronometric Planner Branch Score Results",
            "",
            f"Status: planner-facing branch scoring smoke for `{condition['run_label']}`.",
            "",
            "This is not a new training run and not ARC solve evidence. It checks that",
            "train-built branch-library and fallback adjustments flow through the",
            "NanoWM-compatible chronometric scoring surface.",
            "",
            "## Condition",
            "",
            f"- run label: `{condition['run_label']}`",
            f"- run kind: `{condition['run_kind']}`",
            f"- git commit: `{condition['git_commit']}`",
            f"- git dirty at run: `{condition['git_dirty']}`",
            f"- manifest: `{condition['manifest']}`",
            f"- input predictions: `{condition['input_predictions']}`",
            f"- scorer surface: `{condition['scorer_surface']}`",
            f"- scorer implementation: `{condition['scorer_impl']}`",
            f"- seed: `{condition['seed']}`",
            f"- device: `{condition['device']}`",
            f"- hidden size: `{condition['hidden_size']}`",
            f"- frames: `{condition['frames']}`",
            f"- library scope: `{condition['library_scope']}`",
            f"- fallback scope: `{condition['fallback_scope']}`",
            f"- library entries: `{summary['library_entries']}`",
            f"- heldout labels used: `{condition['heldout_labels_used']}`",
            f"- training data promoted: `{condition['training_data_promoted']}`",
            "",
            "## Metrics",
            "",
            f"- records scored: `{summary['records']}`",
            f"- planner-applied records: `{summary['applied_records']}`",
            f"- planner-fallback records: `{summary['fallback_records']}`",
            f"- overall applied reference MAE: `{overall.get('applied_reference_mae')}`",
            f"- overall applied reference max abs diff: `{overall.get('applied_reference_max_abs_diff')}`",
            f"- heldout records: `{heldout.get('records')}`",
            f"- heldout planner-applied records: `{heldout.get('applied_records')}`",
            f"- heldout planner-fallback records: `{heldout.get('fallback_records')}`",
            f"- heldout applied target signed-Y MAE: `{heldout.get('applied_target_signed_mae')}`",
            f"- heldout unapplied records: `{heldout.get('unapplied_records')}`",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="chronometric_planner_branch_score_v027")
    parser.add_argument("--blend", type=float, default=1.0)
    parser.add_argument("--min-records", type=int, default=1)
    parser.add_argument("--library-scope", choices=BRANCH_LIBRARY_SCOPES, default="time_phase_translation_stasis_loop")
    parser.add_argument("--fallback-scope", choices=BRANCH_LIBRARY_FALLBACK_SCOPES, default="time_phase_translation_potential")
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--hidden-size", type=int, default=32)
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--potential-families", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    summary = score_planner_branches(parse_args())
    heldout = summary["by_split"].get("heldout", {})
    print(
        json.dumps(
            {
                "library_entries": summary["library_entries"],
                "records": summary["records"],
                "planner_applied_records": summary["applied_records"],
                "planner_fallback_records": summary["fallback_records"],
                "heldout_applied_records": heldout.get("applied_records"),
                "heldout_applied_target_signed_mae": heldout.get("applied_target_signed_mae"),
                "heldout_unapplied_records": heldout.get("unapplied_records"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
