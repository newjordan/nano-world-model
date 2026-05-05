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
    examples_to_negative_control_mask,
    examples_to_tensors,
    load_calibration_examples,
    split_examples_by_group,
)


DEFAULT_MANIFEST = ROOT / "experiments" / "2026-05-05_arc_bridge_manifest_smoke" / "arc_bridge_manifest.jsonl"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_calibration_smoke"


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _rel_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _git_dirty(*, ignored_paths: list[Path] | None = None) -> bool:
    status = _git(["status", "--short", "--untracked-files=all"])
    if status == "unknown":
        return True
    ignored = [_rel_to_root(path).rstrip("/") for path in ignored_paths or []]
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


def _standardize_with(x: torch.Tensor, mean: torch.Tensor, std: torch.Tensor) -> torch.Tensor:
    return (x - mean.view(1, -1)) / std.view(1, -1)


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
    negative_control_mask: torch.Tensor | None = None,
    negative_control_weight: float = 0.0,
    negative_control_margin: float = -0.5,
) -> tuple[torch.Tensor, dict[str, float]]:
    signed_loss = F.mse_loss(outputs["signed_y"], signed_y)
    progress_loss = F.binary_cross_entropy_with_logits(
        outputs["progress_logit"],
        progress,
        pos_weight=pos_weight,
    )
    family_loss = F.mse_loss(outputs["family_vector"], families)
    negative_control_loss = outputs["signed_y"].new_tensor(0.0)
    if negative_control_mask is not None and negative_control_weight > 0.0:
        selected = outputs["signed_y"][negative_control_mask > 0.5]
        if selected.numel() > 0:
            negative_control_loss = F.relu(selected - negative_control_margin).pow(2).mean()
    total = (
        signed_weight * signed_loss
        + progress_weight * progress_loss
        + family_weight * family_loss
        + negative_control_weight * negative_control_loss
    )
    return total, {
        "signed_mse": float(signed_loss.detach().cpu().item()),
        "progress_bce": float(progress_loss.detach().cpu().item()),
        "family_mse": float(family_loss.detach().cpu().item()),
        "negative_control_hinge": float(negative_control_loss.detach().cpu().item()),
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
    negative_control_mask: torch.Tensor | None = None,
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
            negative_control_mask=negative_control_mask,
            negative_control_weight=args.negative_control_weight,
            negative_control_margin=args.negative_control_margin,
        )
        progress_prob = torch.sigmoid(outputs["progress_logit"])
        progress_pred = (progress_prob >= 0.5).float()
        signed_mae = (outputs["signed_y"] - signed_y).abs().mean()
        progress_acc = (progress_pred == progress).float().mean()
        positive_indices = torch.nonzero(progress.squeeze(-1) > 0.5, as_tuple=False).flatten()
        positive_rank = None
        positive_ranks: list[int] = []
        if positive_indices.numel() > 0:
            sorted_indices = torch.argsort(progress_prob.squeeze(-1), descending=True)
            for positive_index in positive_indices:
                rank = int((sorted_indices == positive_index).nonzero(as_tuple=False)[0].item()) + 1
                positive_ranks.append(rank)
            positive_rank = positive_ranks[0]
        return {
            **losses,
            "signed_mae": float(signed_mae.detach().cpu().item()),
            "progress_accuracy": float(progress_acc.detach().cpu().item()),
            "positive_progress_rank": positive_rank,
            "positive_progress_count": int(positive_indices.numel()),
            "positive_progress_best_rank": min(positive_ranks) if positive_ranks else None,
            "positive_progress_mean_rank": (
                float(sum(positive_ranks) / len(positive_ranks)) if positive_ranks else None
            ),
        }


def _baseline_metrics(
    signed_y: torch.Tensor,
    progress: torch.Tensor,
    families: torch.Tensor,
    pos_weight: torch.Tensor,
    args: argparse.Namespace,
    negative_control_mask: torch.Tensor | None = None,
) -> dict[str, Any]:
    reference = _baseline_reference(signed_y, progress, families)
    return _baseline_metrics_from_reference(
        reference,
        signed_y,
        progress,
        families,
        pos_weight,
        args,
        negative_control_mask=negative_control_mask,
    )


def _baseline_reference(
    signed_y: torch.Tensor,
    progress: torch.Tensor,
    families: torch.Tensor,
) -> dict[str, torch.Tensor]:
    return {
        "signed_mean": signed_y.mean(),
        "progress_prior": progress.mean().clamp(1e-6, 1.0 - 1e-6),
        "family_mean": families.mean(dim=0, keepdim=True),
    }


def _baseline_metrics_from_reference(
    reference: dict[str, torch.Tensor],
    signed_y: torch.Tensor,
    progress: torch.Tensor,
    families: torch.Tensor,
    pos_weight: torch.Tensor,
    args: argparse.Namespace,
    negative_control_mask: torch.Tensor | None = None,
) -> dict[str, Any]:
    signed_mean = reference["signed_mean"].expand_as(signed_y)
    progress_logits = torch.logit(reference["progress_prior"]).expand_as(progress)
    family_mean = reference["family_mean"].expand_as(families)
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
        negative_control_mask=negative_control_mask,
        negative_control_weight=args.negative_control_weight,
        negative_control_margin=args.negative_control_margin,
    )
    signed_mae = (signed_mean - signed_y).abs().mean()
    progress_pred = (torch.sigmoid(progress_logits) >= 0.5).float()
    positive_count = int(torch.nonzero(progress.squeeze(-1) > 0.5, as_tuple=False).numel())
    return {
        **losses,
        "signed_mae": float(signed_mae.detach().cpu().item()),
        "progress_accuracy": float((progress_pred == progress).float().mean().detach().cpu().item()),
        "positive_progress_rank": None,
        "positive_progress_count": positive_count,
        "positive_progress_best_rank": None,
        "positive_progress_mean_rank": None,
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
    split = split_examples_by_group(
        examples,
        key=args.holdout_key,
        holdout_fraction=args.holdout_fraction,
        seed=args.holdout_seed,
        heldout_group_values=args.heldout_group_value,
    )
    train_x_raw, train_signed_y, train_progress, train_families = examples_to_tensors(split.train, device=device)
    train_negative_control_mask = examples_to_negative_control_mask(split.train, device=device)
    train_x, feature_mean, feature_std = _standardize(train_x_raw)
    heldout_tensors = None
    heldout_negative_control_mask = None
    if split.heldout:
        heldout_x_raw, heldout_signed_y, heldout_progress, heldout_families = examples_to_tensors(
            split.heldout,
            device=device,
        )
        heldout_negative_control_mask = examples_to_negative_control_mask(split.heldout, device=device)
        heldout_tensors = (
            _standardize_with(heldout_x_raw, feature_mean, feature_std),
            heldout_signed_y,
            heldout_progress,
            heldout_families,
        )
    pos_weight = _pos_weight(train_progress)

    model = ChronometricCalibrationMLP(
        input_dim=train_x.shape[1],
        family_dim=train_families.shape[1],
        hidden_size=args.hidden_size,
        bounded_outputs=not args.unbounded_outputs,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    baseline_reference = _baseline_reference(train_signed_y, train_progress, train_families)
    baseline = _baseline_metrics_from_reference(
        baseline_reference,
        train_signed_y,
        train_progress,
        train_families,
        pos_weight,
        args,
        negative_control_mask=train_negative_control_mask,
    )
    initial = _evaluate(
        model,
        train_x,
        train_signed_y,
        train_progress,
        train_families,
        pos_weight,
        args,
        negative_control_mask=train_negative_control_mask,
    )
    heldout_baseline = None
    heldout_initial = None
    if heldout_tensors is not None:
        heldout_x, heldout_signed_y, heldout_progress, heldout_families = heldout_tensors
        heldout_baseline = _baseline_metrics_from_reference(
            baseline_reference,
            heldout_signed_y,
            heldout_progress,
            heldout_families,
            pos_weight,
            args,
            negative_control_mask=heldout_negative_control_mask,
        )
        heldout_initial = _evaluate(
            model,
            heldout_x,
            heldout_signed_y,
            heldout_progress,
            heldout_families,
            pos_weight,
            args,
            negative_control_mask=heldout_negative_control_mask,
        )
    checkpoints: list[dict[str, float | int]] = []
    for step in range(1, args.steps + 1):
        optimizer.zero_grad(set_to_none=True)
        outputs = model(train_x)
        loss, parts = _loss(
            outputs,
            train_signed_y,
            train_progress,
            train_families,
            pos_weight,
            signed_weight=args.signed_weight,
            progress_weight=args.progress_weight,
            family_weight=args.family_weight,
            negative_control_mask=train_negative_control_mask,
            negative_control_weight=args.negative_control_weight,
            negative_control_margin=args.negative_control_margin,
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
        optimizer.step()
        if step in {1, args.steps} or step % args.log_every == 0:
            checkpoints.append({"step": step, **parts})

    final = _evaluate(
        model,
        train_x,
        train_signed_y,
        train_progress,
        train_families,
        pos_weight,
        args,
        negative_control_mask=train_negative_control_mask,
    )
    heldout_final = None
    predictions = _predictions(model, train_x, split.train, split_name="train")
    if heldout_tensors is not None:
        heldout_x, heldout_signed_y, heldout_progress, heldout_families = heldout_tensors
        heldout_final = _evaluate(
            model,
            heldout_x,
            heldout_signed_y,
            heldout_progress,
            heldout_families,
            pos_weight,
            args,
            negative_control_mask=heldout_negative_control_mask,
        )
        predictions.extend(_predictions(model, heldout_x, split.heldout, split_name="heldout"))
    eval_scope = "train_fit_only_all_records"
    run_kind = "fit_smoke_no_generalization_claim"
    if split.heldout:
        eval_scope = f"group_holdout_by_{args.holdout_key}"
        run_kind = "group_holdout_calibration_smoke"
    condition = {
        "run_label": args.run_label,
        "run_kind": run_kind,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/train_chronometric_calibrator.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "manifest": str(manifest.relative_to(ROOT)),
        "manifest_sha256": _sha256(manifest),
        "records": len(examples),
        "progress_positive_records": int(
            train_progress.sum().detach().cpu().item()
            + (heldout_tensors[2].sum().detach().cpu().item() if heldout_tensors is not None else 0)
        ),
        "train_records": len(split.train),
        "heldout_records": len(split.heldout),
        "train_positive_records": int(train_progress.sum().detach().cpu().item()),
        "heldout_positive_records": (
            int(heldout_tensors[2].sum().detach().cpu().item()) if heldout_tensors is not None else 0
        ),
        "split_strategy": {
            "key": split.key,
            "holdout_fraction": split.holdout_fraction,
            "seed": split.seed,
            "explicit_heldout_group_values": list(args.heldout_group_value or []),
            "train_groups": len(split.train_groups),
            "heldout_groups": len(split.heldout_groups),
            "heldout_group_values": split.heldout_groups,
        },
        "device_requested": getattr(args, "requested_device", args.device),
        "device_resolved": str(device),
        "device_fallback_reason": fallback_reason,
        "seed": args.seed,
        "steps": args.steps,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "hidden_size": args.hidden_size,
        "bounded_outputs": not args.unbounded_outputs,
        "loss_weights": {
            "signed": args.signed_weight,
            "progress": args.progress_weight,
            "family": args.family_weight,
            "negative_control": args.negative_control_weight,
        },
        "auxiliary_objectives": {
            "negative_control_labels": [
                "stasis_no_change",
                "dominant_group:stasis_loop",
            ],
            "negative_control_margin": args.negative_control_margin,
            "negative_control_weight": args.negative_control_weight,
            "train_negative_control_records": int(train_negative_control_mask.sum().detach().cpu().item()),
            "heldout_negative_control_records": (
                int(heldout_negative_control_mask.sum().detach().cpu().item())
                if heldout_negative_control_mask is not None
                else 0
            ),
        },
        "feature_names": list(FEATURE_NAMES),
        "leakage_excluded_fields": list(LEAKAGE_EXCLUDED_FIELDS),
        "quarantine_status_preserved": True,
        "training_data_promoted": False,
        "eval_scope": eval_scope,
    }
    summary = {
        "condition": condition,
        "baseline": baseline,
        "initial": initial,
        "final": final,
        "loss_reduction_vs_initial": initial["total"] - final["total"],
        "loss_reduction_vs_baseline": baseline["total"] - final["total"],
        "heldout_baseline": heldout_baseline,
        "heldout_initial": heldout_initial,
        "heldout_final": heldout_final,
        "heldout_loss_reduction_vs_baseline": (
            heldout_baseline["total"] - heldout_final["total"]
            if heldout_baseline is not None and heldout_final is not None
            else None
        ),
        "heldout_loss_reduction_vs_initial": (
            heldout_initial["total"] - heldout_final["total"]
            if heldout_initial is not None and heldout_final is not None
            else None
        ),
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
    *,
    split_name: str,
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
                "split": split_name,
                "task_id": record.get("task_id"),
                "attempt_id": record.get("attempt_id"),
                "source_artifact_path": record.get("source_artifact_path"),
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
    heldout_final = summary.get("heldout_final")
    heldout_baseline = summary.get("heldout_baseline")
    split_strategy = condition.get("split_strategy") or {}
    auxiliary = condition.get("auxiliary_objectives") or {}
    status = "supervised fit smoke for a small chronometric calibration head."
    claim = (
        "This is not a held-out quality claim. It verifies that bridge rows can drive a learned "
        "calibration objective without manual scorer knob changes."
    )
    if heldout_final is not None:
        status = "grouped held-out smoke for a small chronometric calibration head."
        claim = "This is a branch-group held-out signal check, not an ARC solve claim or training-data promotion."
    lines = [
        "# Chronometric Calibration Smoke Results",
        "",
        f"Status: {status}",
        "",
        claim,
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
        f"- train records: `{condition['train_records']}`",
        f"- heldout records: `{condition['heldout_records']}`",
        f"- train progress-positive records: `{condition['train_positive_records']}`",
        f"- heldout progress-positive records: `{condition['heldout_positive_records']}`",
        f"- eval scope: `{condition['eval_scope']}`",
        f"- device: `{condition['device_resolved']}`",
        f"- seed: `{condition['seed']}`",
        f"- steps: `{condition['steps']}`",
        f"- negative-control weight: `{auxiliary.get('negative_control_weight')}`",
        f"- negative-control margin: `{auxiliary.get('negative_control_margin')}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Metrics",
        "",
        f"- train baseline total loss: `{baseline['total']}`",
        f"- train final total loss: `{final['total']}`",
        f"- train loss reduction vs baseline: `{summary['loss_reduction_vs_baseline']}`",
        f"- train signed-Y MAE final: `{final['signed_mae']}`",
        f"- train progress accuracy final: `{final['progress_accuracy']}`",
        f"- train positive best rank final: `{final['positive_progress_best_rank']}`",
        f"- train family MSE final: `{final['family_mse']}`",
        "",
    ]
    if heldout_final is not None and heldout_baseline is not None:
        lines.extend(
            [
                "## Heldout Metrics",
                "",
                f"- heldout baseline total loss: `{heldout_baseline['total']}`",
                f"- heldout final total loss: `{heldout_final['total']}`",
                f"- heldout loss reduction vs baseline: `{summary['heldout_loss_reduction_vs_baseline']}`",
                f"- heldout signed-Y MAE final: `{heldout_final['signed_mae']}`",
                f"- heldout progress accuracy final: `{heldout_final['progress_accuracy']}`",
                f"- heldout positive best rank final: `{heldout_final['positive_progress_best_rank']}`",
                f"- heldout positive mean rank final: `{heldout_final['positive_progress_mean_rank']}`",
                f"- heldout family MSE final: `{heldout_final['family_mse']}`",
                "",
                "## Split",
                "",
                f"- key: `{split_strategy.get('key')}`",
                f"- holdout fraction: `{split_strategy.get('holdout_fraction')}`",
                f"- train groups: `{split_strategy.get('train_groups')}`",
                f"- heldout groups: `{split_strategy.get('heldout_groups')}`",
                "",
            ]
        )
    lines.extend(
        [
        "## Integrity",
        "",
        "- inputs exclude direct outcome labels and post-outcome fields",
        "- all records preserve quarantine/control provenance",
        "- heldout split is by group, not by random row, when heldout records are present",
        "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="chronometric_calibration_smoke")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--holdout-key", default="source_artifact_path")
    parser.add_argument("--holdout-fraction", type=float, default=0.0)
    parser.add_argument("--holdout-seed", type=int, default=20260505)
    parser.add_argument(
        "--heldout-group-value",
        action="append",
        default=None,
        help="Explicit group value for --holdout-key. Can be repeated.",
    )
    parser.add_argument("--steps", type=int, default=800)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument(
        "--unbounded-outputs",
        action="store_true",
        help="Disable tanh bounds on signed-Y and family heads. Kept only for reproducing older failure modes.",
    )
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--signed-weight", type=float, default=1.0)
    parser.add_argument("--progress-weight", type=float, default=1.0)
    parser.add_argument("--family-weight", type=float, default=0.25)
    parser.add_argument(
        "--negative-control-weight",
        type=float,
        default=0.0,
        help="Auxiliary hinge weight for stasis/no-change and stasis-loop rows.",
    )
    parser.add_argument(
        "--negative-control-margin",
        type=float,
        default=-0.5,
        help="Signed-Y upper margin for the negative-control hinge objective.",
    )
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
                "heldout_final_total": (
                    summary["heldout_final"]["total"] if summary.get("heldout_final") is not None else None
                ),
                "loss_reduction_vs_baseline": summary["loss_reduction_vs_baseline"],
                "heldout_loss_reduction_vs_baseline": summary.get("heldout_loss_reduction_vs_baseline"),
                "positive_progress_best_rank": summary["final"]["positive_progress_best_rank"],
                "heldout_positive_progress_best_rank": (
                    summary["heldout_final"]["positive_progress_best_rank"]
                    if summary.get("heldout_final") is not None
                    else None
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
