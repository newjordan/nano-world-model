#!/usr/bin/env python3
"""Train a small chronometric calibration head on a bridge manifest smoke set."""

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
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_calibration import (  # noqa: E402
    FEATURE_NAMES,
    LEAKAGE_EXCLUDED_FIELDS,
    ChronometricCalibrationMLP,
    examples_to_tensors,
    load_calibration_examples,
)


DEFAULT_MANIFEST = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_smoke" / "arc_bridge_manifest.jsonl"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_calibration_smoke"


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    return device


def _is_cuda_oom(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "cuda" in text and "out of memory" in text


def _standardize(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    mean = x.mean(dim=0, keepdim=True)
    std = x.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
    return (x - mean) / std, mean.squeeze(0), std.squeeze(0)


def _pos_weight(progress: torch.Tensor) -> torch.Tensor:
    positives = progress.sum().clamp_min(1.0)
    negatives = (progress.numel() - progress.sum()).clamp_min(1.0)
    return negatives / positives


def _loss(
    outputs: dict[str, torch.Tensor],
    signed_y: torch.Tensor,
    progress: torch.Tensor,
    families: torch.Tensor,
    pos_weight: torch.Tensor,
    *,
    signed_weight: float,
    progress_weight: float,
    family_weight: float,
) -> tuple[torch.Tensor, dict[str, float]]:
    signed_loss = F.mse_loss(outputs["signed_y"], signed_y)
    progress_loss = F.binary_cross_entropy_with_logits(
        outputs["progress_logit"],
        progress,
        pos_weight=pos_weight,
    )
    family_loss = F.mse_loss(outputs["family_vector"], families)
    total = signed_weight * signed_loss + progress_weight * progress_loss + family_weight * family_loss
    return total, {
        "signed_mse": float(signed_loss.detach().cpu().item()),
        "progress_bce": float(progress_loss.detach().cpu().item()),
        "family_mse": float(family_loss.detach().cpu().item()),
        "total": float(total.detach().cpu().item()),
    }


def _evaluate(
    model: ChronometricCalibrationMLP,
    x: torch.Tensor,
    signed_y: torch.Tensor,
    progress: torch.Tensor,
    families: torch.Tensor,
    pos_weight: torch.Tensor,
    args: argparse.Namespace,
) -> dict[str, Any]:
    with torch.no_grad():
        outputs = model(x)
        _, losses = _loss(
            outputs,
            signed_y,
            progress,
            families,
            pos_weight,
            signed_weight=args.signed_weight,
            progress_weight=args.progress_weight,
            family_weight=args.family_weight,
        )
        progress_prob = torch.sigmoid(outputs["progress_logit"])
        progress_pred = (progress_prob >= 0.5).float()
        signed_mae = (outputs["signed_y"] - signed_y).abs().mean()
        progress_acc = (progress_pred == progress).float().mean()
        positive_indices = torch.nonzero(progress.squeeze(-1) > 0.5, as_tuple=False).flatten()
        positive_rank = None
        if positive_indices.numel() > 0:
            sorted_indices = torch.argsort(progress_prob.squeeze(-1), descending=True)
            positive_rank = int((sorted_indices == positive_indices[0]).nonzero(as_tuple=False)[0].item()) + 1
        return {
            **losses,
            "signed_mae": float(signed_mae.detach().cpu().item()),
            "progress_accuracy": float(progress_acc.detach().cpu().item()),
            "positive_progress_rank": positive_rank,
        }


def _baseline_metrics(
    signed_y: torch.Tensor,
    progress: torch.Tensor,
    families: torch.Tensor,
    pos_weight: torch.Tensor,
    args: argparse.Namespace,
) -> dict[str, Any]:
    signed_mean = signed_y.mean().expand_as(signed_y)
    progress_prior = progress.mean().clamp(1e-6, 1.0 - 1e-6)
    progress_logits = torch.logit(progress_prior).expand_as(progress)
    family_mean = families.mean(dim=0, keepdim=True).expand_as(families)
    outputs = {
        "signed_y": signed_mean,
        "progress_logit": progress_logits,
        "family_vector": family_mean,
    }
    _, losses = _loss(
        outputs,
        signed_y,
        progress,
        families,
        pos_weight,
        signed_weight=args.signed_weight,
        progress_weight=args.progress_weight,
        family_weight=args.family_weight,
    )
    signed_mae = (signed_mean - signed_y).abs().mean()
    progress_pred = (torch.sigmoid(progress_logits) >= 0.5).float()
    return {
        **losses,
        "signed_mae": float(signed_mae.detach().cpu().item()),
        "progress_accuracy": float((progress_pred == progress).float().mean().detach().cpu().item()),
        "positive_progress_rank": None,
    }


def train(args: argparse.Namespace, *, fallback_reason: str | None = None) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.manifest.resolve()
    device = _resolve_device(args.device)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    examples = load_calibration_examples(manifest)
    x, signed_y, progress, families = examples_to_tensors(examples, device=device)
    x, feature_mean, feature_std = _standardize(x)
    pos_weight = _pos_weight(progress)

    model = ChronometricCalibrationMLP(
        input_dim=x.shape[1],
        family_dim=families.shape[1],
        hidden_size=args.hidden_size,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    baseline = _baseline_metrics(signed_y, progress, families, pos_weight, args)
    initial = _evaluate(model, x, signed_y, progress, families, pos_weight, args)
    checkpoints: list[dict[str, float | int]] = []
    for step in range(1, args.steps + 1):
        optimizer.zero_grad(set_to_none=True)
        outputs = model(x)
        loss, parts = _loss(
            outputs,
            signed_y,
            progress,
            families,
            pos_weight,
            signed_weight=args.signed_weight,
            progress_weight=args.progress_weight,
            family_weight=args.family_weight,
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
        optimizer.step()
        if step in {1, args.steps} or step % args.log_every == 0:
            checkpoints.append({"step": step, **parts})

    final = _evaluate(model, x, signed_y, progress, families, pos_weight, args)
    predictions = _predictions(model, x, examples)
    condition = {
        "run_label": "chronometric_calibration_smoke",
        "run_kind": "fit_smoke_no_generalization_claim",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/train_chronometric_calibrator.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git(["status", "--short", "--untracked-files=all"]) != "",
        "manifest": str(manifest.relative_to(ROOT)),
        "manifest_sha256": _sha256(manifest),
        "records": len(examples),
        "progress_positive_records": int(progress.sum().detach().cpu().item()),
        "device_requested": getattr(args, "requested_device", args.device),
        "device_resolved": str(device),
        "device_fallback_reason": fallback_reason,
        "seed": args.seed,
        "steps": args.steps,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "hidden_size": args.hidden_size,
        "loss_weights": {
            "signed": args.signed_weight,
            "progress": args.progress_weight,
            "family": args.family_weight,
        },
        "feature_names": list(FEATURE_NAMES),
        "leakage_excluded_fields": list(LEAKAGE_EXCLUDED_FIELDS),
        "quarantine_status_preserved": True,
        "training_data_promoted": False,
        "eval_scope": "train_fit_only_all_records",
    }
    summary = {
        "condition": condition,
        "baseline": baseline,
        "initial": initial,
        "final": final,
        "loss_reduction_vs_initial": initial["total"] - final["total"],
        "loss_reduction_vs_baseline": baseline["total"] - final["total"],
        "checkpoints": checkpoints,
        "feature_mean": [float(v) for v in feature_mean.detach().cpu().tolist()],
        "feature_std": [float(v) for v in feature_std.detach().cpu().tolist()],
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_jsonl(out_dir / "predictions.jsonl", predictions)
    (out_dir / "RESULTS.md").write_text(_format_results(summary), encoding="utf-8")
    return summary


def _predictions(
    model: ChronometricCalibrationMLP,
    x: torch.Tensor,
    examples: list[Any],
) -> list[dict[str, Any]]:
    with torch.no_grad():
        outputs = model(x)
        signed = outputs["signed_y"].squeeze(-1).detach().cpu().tolist()
        progress = torch.sigmoid(outputs["progress_logit"]).squeeze(-1).detach().cpu().tolist()
    rows = []
    for index, example in enumerate(examples):
        record = example.record
        rows.append(
            {
                "index": index,
                "task_id": record.get("task_id"),
                "attempt_id": record.get("attempt_id"),
                "t": record.get("t"),
                "action_id": record.get("action_id"),
                "target_signed_y": example.signed_y,
                "pred_signed_y": signed[index],
                "target_progress": example.progress,
                "pred_progress_prob": progress[index],
                "progress_label": record.get("progress_label"),
                "control_label": record.get("control_label"),
            }
        )
    rows.sort(key=lambda row: row["pred_progress_prob"], reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["pred_progress_rank"] = rank
    return rows


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _format_results(summary: dict[str, Any]) -> str:
    condition = summary["condition"]
    final = summary["final"]
    baseline = summary["baseline"]
    lines = [
        "# Chronometric Calibration Smoke Results",
        "",
        "Status: supervised fit smoke for a small chronometric calibration head.",
        "",
        "This is not a held-out quality claim. It verifies that bridge rows can drive a learned calibration objective without manual scorer knob changes.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- manifest: `{condition['manifest']}`",
        f"- records: `{condition['records']}`",
        f"- progress-positive records: `{condition['progress_positive_records']}`",
        f"- device: `{condition['device_resolved']}`",
        f"- seed: `{condition['seed']}`",
        f"- steps: `{condition['steps']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Metrics",
        "",
        f"- baseline total loss: `{baseline['total']}`",
        f"- final total loss: `{final['total']}`",
        f"- loss reduction vs baseline: `{summary['loss_reduction_vs_baseline']}`",
        f"- signed-Y MAE final: `{final['signed_mae']}`",
        f"- progress accuracy final: `{final['progress_accuracy']}`",
        f"- positive progress rank final: `{final['positive_progress_rank']}`",
        f"- family MSE final: `{final['family_mse']}`",
        "",
        "## Integrity",
        "",
        "- inputs exclude direct outcome labels and post-outcome fields",
        "- all records preserve quarantine/control provenance",
        "- eval scope is train-fit only; more bridge rows are required before held-out claims",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--steps", type=int, default=800)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--signed-weight", type=float, default=1.0)
    parser.add_argument("--progress-weight", type=float, default=1.0)
    parser.add_argument("--family-weight", type=float, default=0.25)
    parser.add_argument("--log-every", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        summary = train(args)
    except (RuntimeError, torch.AcceleratorError) as exc:
        if args.device == "auto" and _is_cuda_oom(exc):
            try:
                torch.cuda.empty_cache()
            except RuntimeError:
                pass
            fallback_args = argparse.Namespace(**vars(args))
            fallback_args.requested_device = args.device
            fallback_args.device = "cpu"
            summary = train(
                fallback_args,
                fallback_reason=f"auto CUDA fallback after {exc.__class__.__name__}: {str(exc).splitlines()[0]}",
            )
        else:
            raise
    print(
        json.dumps(
            {
                "final_total": summary["final"]["total"],
                "loss_reduction_vs_baseline": summary["loss_reduction_vs_baseline"],
                "positive_progress_rank": summary["final"]["positive_progress_rank"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
