#!/usr/bin/env python3
"""Run the first chronometric mechanics smoke test.

This is a mechanics gate, not a quality benchmark. It uses synthetic tokens and
a synthetic bridge manifest so no quarantined ARC rows are imported by accident.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_bridge import (  # noqa: E402
    synthetic_bridge_records,
    validate_bridge_manifest,
    write_jsonl,
)
from models.chronometric_contortion import (  # noqa: E402
    LOG_PHASE_LAMBDA,
    ChronometricConfig,
    ChronometricContortionLayer,
    log_time_phase,
    minkowski_dot,
    normalize_timelike_velocity,
    project_orthogonal_to_velocity,
)


DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-05_chronometric_mechanics_smoke"


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _git_dirty_excluding(path: Path) -> bool:
    raw_status = _git(["status", "--short", "--untracked-files=all"])
    if raw_status == "unknown":
        return True
    try:
        excluded = path.resolve().relative_to(ROOT).as_posix().rstrip("/") + "/"
    except ValueError:
        excluded = ""
    for line in raw_status.splitlines():
        item = line[3:].strip()
        if item.startswith(excluded):
            continue
        return True
    return False


def _resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
    return device


def _is_cuda_oom(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "cuda" in text and "out of memory" in text


def _nvidia_smi_snapshot() -> str | None:
    try:
        return subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu,power.draw",
                "--format=csv,noheader",
            ],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _tensor_stats(value: torch.Tensor) -> dict[str, float]:
    value = value.detach().float().cpu()
    return {
        "mean": float(value.mean().item()),
        "abs_mean": float(value.abs().mean().item()),
        "max_abs": float(value.abs().max().item()),
        "std": float(value.std(unbiased=False).item()) if value.numel() > 1 else 0.0,
    }


def _gate(value: bool, **metrics: Any) -> dict[str, Any]:
    return {"pass": bool(value), **metrics}


def run_smoke(out_dir: Path, *, device_name: str, seed: int) -> dict[str, Any]:
    device = _resolve_device(device_name)
    try:
        return _run_smoke_on_device(
            out_dir,
            device=device,
            device_requested=device_name,
            seed=seed,
            fallback_reason=None,
        )
    except (RuntimeError, torch.AcceleratorError) as exc:
        if device_name == "auto" and device.type == "cuda" and _is_cuda_oom(exc):
            try:
                torch.cuda.empty_cache()
            except RuntimeError:
                pass
            return _run_smoke_on_device(
                out_dir,
                device=torch.device("cpu"),
                device_requested=device_name,
                seed=seed,
                fallback_reason=f"auto CUDA fallback after {exc.__class__.__name__}: {str(exc).splitlines()[0]}",
            )
        raise


def _run_smoke_on_device(
    out_dir: Path,
    *,
    device: torch.device,
    device_requested: str,
    seed: int,
    fallback_reason: str | None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)

    config = ChronometricConfig(
        mode="branch_rollout",
        residual_scale=0.05,
        potential_families=8,
        init_std=0.03,
    )
    layer = ChronometricContortionLayer(hidden_size=32, config=config).to(device)
    layer.eval()

    tokens = torch.randn(3, 6, 32, device=device)
    action_zero = torch.zeros_like(tokens)
    action_context = torch.randn_like(tokens)
    branch_dirs = torch.tensor(
        [
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, -1.0, 0.0],
        ],
        device=device,
    )

    theta = log_time_phase(torch.tensor([3.0], device=device), tau_c=0.0)
    theta_next = log_time_phase(torch.tensor([3.0 * LOG_PHASE_LAMBDA], device=device), tau_c=0.0)
    phase_delta_error = float((theta_next - theta - 2.0 * torch.pi).abs().item())

    velocity = normalize_timelike_velocity(torch.randn(12, 3, device=device), c=1.0)
    raw_response = torch.randn(12, 4, device=device)
    projected = project_orthogonal_to_velocity(velocity, raw_response, c=1.0)
    projector_orthogonality = minkowski_dot(velocity, projected)
    velocity_invariant = minkowski_dot(velocity, velocity) + 1.0

    with torch.no_grad():
        branch_outputs = [
            layer.score_branch(tokens, branch.unsqueeze(0).expand(tokens.shape[0], 4), action_context=action_context)
            for branch in branch_dirs
        ]
        no_action = layer.score_branch(tokens, branch_dirs[:1].expand(tokens.shape[0], 4), action_context=action_zero)
        with_action = layer.score_branch(tokens, branch_dirs[:1].expand(tokens.shape[0], 4), action_context=action_context)
        residual_disabled = layer(tokens, action_context=action_context, branch_direction=branch_dirs, apply_residual=False)
        residual_enabled = layer(tokens, action_context=action_context, branch_direction=branch_dirs, apply_residual=True)

    branch_outcome_means = torch.stack([output.outcome_y.mean() for output in branch_outputs])
    branch_force_means = torch.stack([output.contortion_force.mean(dim=(0, 1)) for output in branch_outputs])
    branch_force_pairwise = torch.pdist(branch_force_means.float()).max()
    action_force_delta = (with_action.external_force - no_action.external_force).abs().mean()
    residual_delta = (residual_enabled - residual_disabled).abs().mean()
    all_orthogonality = torch.cat([output.orthogonality.reshape(-1) for output in branch_outputs])
    all_invariants = torch.cat([output.invariant.reshape(-1) for output in branch_outputs])

    manifest_path = out_dir / "synthetic_bridge_manifest.jsonl"
    write_jsonl(manifest_path, synthetic_bridge_records())
    bridge_validation = validate_bridge_manifest(manifest_path)

    gates = {
        "phase_log_cycle": _gate(
            phase_delta_error < 1e-5,
            phase_delta_error=phase_delta_error,
            lambda_value=LOG_PHASE_LAMBDA,
        ),
        "projector_constraint": _gate(
            float(projector_orthogonality.abs().max().item()) < 1e-5
            and float(velocity_invariant.abs().max().item()) < 1e-5,
            orthogonality_max_abs=float(projector_orthogonality.abs().max().item()),
            invariant_max_abs=float(velocity_invariant.abs().max().item()),
        ),
        "layer_constraints": _gate(
            float(all_orthogonality.abs().max().item()) < 1e-5
            and float(all_invariants.abs().max().item()) < 1e-5,
            orthogonality=_tensor_stats(all_orthogonality),
            invariant=_tensor_stats(all_invariants),
        ),
        "branch_direction_distinction": _gate(
            float(branch_force_pairwise.item()) > 1e-8,
            branch_force_pairwise_max=float(branch_force_pairwise.item()),
            branch_outcome_means=[float(v.item()) for v in branch_outcome_means],
            branch_outcome_std=float(branch_outcome_means.std(unbiased=False).item()),
        ),
        "action_context_changes_external_force": _gate(
            float(action_force_delta.item()) > 1e-8,
            external_force_abs_mean_delta=float(action_force_delta.item()),
        ),
        "residual_update_nonzero": _gate(
            float(residual_delta.item()) > 1e-8,
            residual_abs_mean_delta=float(residual_delta.item()),
        ),
        "bridge_manifest_schema": _gate(
            bool(bridge_validation["valid"]),
            records=bridge_validation["records"],
            errors=bridge_validation["errors"],
            manifest_path=str(manifest_path.relative_to(ROOT)),
        ),
    }

    nanowm_gate = _run_nanowm_gate(device=device)
    gates["nanowm_audit_forward"] = nanowm_gate

    condition = {
        "run_label": "mechanics_smoke",
        "run_kind": "new_experiment",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/chronometric_mechanics_smoke.py",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git(["status", "--short"]) != "",
        "git_dirty_excluding_output_dir": _git_dirty_excluding(out_dir),
        "seed": seed,
        "device_requested": device_requested,
        "device_resolved": str(device),
        "device_fallback_reason": fallback_reason,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_device_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "nvidia_smi": _nvidia_smi_snapshot(),
        "synthetic_tokens": {"batch": 3, "frames": 6, "hidden_size": 32},
        "chronometric_config": {
            "mode": config.mode,
            "residual_scale": config.residual_scale,
            "potential_families": config.potential_families,
            "init_std": config.init_std,
        },
        "arc_data_used": False,
        "bridge_manifest": str(manifest_path.relative_to(ROOT)),
        "thresholds": {
            "phase_delta_error_lt": 1e-5,
            "constraint_max_abs_lt": 1e-5,
            "branch_force_pairwise_gt": 1e-8,
            "action_force_delta_gt": 1e-8,
            "residual_delta_gt": 1e-8,
        },
    }

    metrics = {
        "condition": condition,
        "gates": gates,
        "all_gates_pass": all(gate["pass"] for gate in gates.values()),
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(_format_results(metrics), encoding="utf-8")
    return metrics


def _run_nanowm_gate(*, device: torch.device) -> dict[str, Any]:
    try:
        from models.nanowm import NanoWM
    except ModuleNotFoundError as exc:
        return _gate(False, skipped=True, reason=f"NanoWM dependency missing: {exc.name}")

    torch.manual_seed(1234)
    model = NanoWM(
        input_size=8,
        patch_size=2,
        in_channels=4,
        hidden_size=64,
        depth=2,
        num_heads=4,
        num_frames=4,
        use_action=True,
        action_dim=7,
        causal=True,
        chronometric={
            "enabled": True,
            "mode": "audit",
            "residual_scale": 0.01,
            "potential_families": 8,
        },
    ).to(device)
    model.eval()
    x = torch.randn(1, 4, 4, 8, 8, device=device)
    t = torch.ones(1, 4, device=device)
    action = torch.zeros(1, 4, 7, device=device)
    branch_direction = torch.tensor([[[0.0, 0.0, 1.0, 0.0]]], device=device).expand(1, 4, 4)

    with torch.no_grad():
        out_audit = model(x, t, action=action, branch_direction=branch_direction)
        metrics = model.get_chronometric_metrics()
        losses = model.get_chronometric_losses()
        model.use_chronometric = False
        out_disabled = model(x, t, action=action)

    output_delta = float((out_audit - out_disabled).abs().max().item())
    return _gate(
        torch.isfinite(out_audit).all().item()
        and output_delta == 0.0
        and "chronometric_orthogonality_abs_mean" in metrics
        and losses == {},
        output_delta_max_abs=output_delta,
        metric_keys=sorted(metrics.keys()),
        losses=losses,
    )


def _format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# Chronometric Mechanics Smoke Results",
        "",
        "Status: recorded mechanics smoke for the chronometric NanoWM foundation.",
        "",
        "This is not a training run and not ARC model-quality evidence. It uses synthetic tokens and a synthetic bridge manifest.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- git dirty excluding output dir: `{condition['git_dirty_excluding_output_dir']}`",
        f"- seed: `{condition['seed']}`",
        f"- device: `{condition['device_resolved']}`",
        f"- ARC data used: `{condition['arc_data_used']}`",
        "",
        "## Gates",
        "",
        "| Gate | Pass | Key Metric |",
        "| --- | --- | --- |",
    ]
    for name, gate in metrics["gates"].items():
        key_metric = _gate_key_metric(gate)
        lines.append(f"| `{name}` | `{gate['pass']}` | {key_metric} |")
    lines.extend(
        [
            "",
            f"Overall pass: `{metrics['all_gates_pass']}`",
            "",
            "## Bridge Manifest",
            "",
            f"- synthetic manifest: `{condition['bridge_manifest']}`",
            "- quarantine/control status is preserved in every record",
            "- no quarantined ARC Sprint 0 data was ingested",
            "",
        ]
    )
    return "\n".join(lines)


def _gate_key_metric(gate: dict[str, Any]) -> str:
    for key in (
        "phase_delta_error",
        "orthogonality_max_abs",
        "branch_force_pairwise_max",
        "external_force_abs_mean_delta",
        "residual_abs_mean_delta",
        "records",
        "output_delta_max_abs",
    ):
        if key in gate:
            return f"`{key}={gate[key]}`"
    if "orthogonality" in gate:
        return f"`orthogonality_max_abs={gate['orthogonality']['max_abs']}`"
    return "`recorded`"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--seed", type=int, default=20260505)
    args = parser.parse_args()

    metrics = run_smoke(args.out_dir, device_name=args.device, seed=args.seed)
    print(json.dumps({"out_dir": str(args.out_dir), "all_gates_pass": metrics["all_gates_pass"]}, indent=2))
    return 0 if metrics["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
