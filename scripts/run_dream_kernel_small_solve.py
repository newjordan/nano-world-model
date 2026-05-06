#!/usr/bin/env python3
"""Run the Dream Kernel small deterministic solve suite and save lab artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_dream_kernel_small_solve_v001"
KERNEL_MANIFEST = ROOT / "dream_kernel" / "Cargo.toml"
KERNEL_MAIN = ROOT / "dream_kernel" / "src" / "main.rs"
KERNEL_LIB = ROOT / "dream_kernel" / "src" / "lib.rs"


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "cargo",
        "run",
        "--manifest-path",
        str(KERNEL_MANIFEST),
        "--",
        "solve-suite",
        "--out-dir",
        str(out_dir),
    ]
    subprocess.run(command, cwd=ROOT, text=True, check=True)
    summary_path = out_dir / "solver_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    condition = _condition(args, out_dir, command)
    metrics = {
        "condition": condition,
        "summary": summary,
        "scenario_metrics": _scenario_metrics(summary),
    }
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(_format_results(metrics), encoding="utf-8")
    return metrics


def _condition(args: argparse.Namespace, out_dir: Path, command: list[str]) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "run_label": args.run_label,
        "run_kind": "deterministic_dream_kernel_small_solve_no_training",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "kernel_manifest": _rel(KERNEL_MANIFEST),
        "kernel_manifest_sha256": _sha256(KERNEL_MANIFEST),
        "kernel_main": _rel(KERNEL_MAIN),
        "kernel_main_sha256": _sha256(KERNEL_MAIN),
        "kernel_lib": _rel(KERNEL_LIB),
        "kernel_lib_sha256": _sha256(KERNEL_LIB),
        "command": command,
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "dataset_path": "not_applicable_hardcoded_dream_kernel_scenarios",
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_deterministic_greedy_planner",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": "not_applicable_local_deterministic_suite",
        "loader_mode": "rust_hardcoded_scenario_suite",
        "loader_settings": {
            "scenario_count": 4,
            "candidate_actions": ["east", "south", "north", "west", "wait"],
            "max_ray_range": 16,
            "ray_directions": "compass_8",
        },
        "quantization_policy": "none",
        "compile_kernel_policy": "cargo_dev_profile",
        "metric_to_compare": "terminal_goal_pass_rate",
        "historical_comparator": "none_first_small_solve_suite",
        "historical_comparator_artifact": None,
        "run_label_semantics": "new_experiment",
        "training_data_promoted": False,
    }


def _scenario_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    scenarios = summary.get("scenarios") or []
    solved = [row for row in scenarios if row.get("solved")]
    invariants = [row for row in scenarios if row.get("invariant_passed")]
    rejected_steps = sum(int(row.get("rejected_steps") or 0) for row in scenarios)
    total_steps = sum(int(row.get("steps") or 0) for row in scenarios)
    return {
        "scenario_count": len(scenarios),
        "solved": len(solved),
        "failed": len(scenarios) - len(solved),
        "pass_rate": len(solved) / max(1, len(scenarios)),
        "invariant_pass_rate": len(invariants) / max(1, len(scenarios)),
        "total_steps": total_steps,
        "rejected_steps": rejected_steps,
        "accepted_step_rate": (total_steps - rejected_steps) / max(1, total_steps),
        "branch_rank_top_match_count": sum(1 for row in scenarios if row.get("branch_rank_top_match")),
    }


def _format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    summary = metrics["summary"]
    scenario_metrics = metrics["scenario_metrics"]
    lines = [
        "# Dream Kernel Small Solve V001 Results",
        "",
        "Status: deterministic small solve suite. No training data promoted.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- run label semantics: `{condition['run_label_semantics']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- script: `{condition['script']}`",
        f"- kernel main: `{condition['kernel_main']}`",
        f"- kernel lib: `{condition['kernel_lib']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        "",
        "## Summary",
        "",
        f"- scenarios: `{scenario_metrics['scenario_count']}`",
        f"- solved: `{scenario_metrics['solved']}`",
        f"- failed: `{scenario_metrics['failed']}`",
        f"- pass rate: `{scenario_metrics['pass_rate']:.6f}`",
        f"- invariant pass rate: `{scenario_metrics['invariant_pass_rate']:.6f}`",
        f"- accepted step rate: `{scenario_metrics['accepted_step_rate']:.6f}`",
        f"- branch-rank top-match count: `{scenario_metrics['branch_rank_top_match_count']}`",
        "",
        "## Scenarios",
        "",
        "| scenario | solved | steps | reward | terminal | rejected | branch top match | actions | sequence |",
        "| --- | --- | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    for row in summary.get("scenarios") or []:
        lines.append(
            "| {name} | {solved} | {steps} | {reward} | {terminal} | {rejected} | {top} | `{actions}` | `{sequence}` |".format(
                name=row.get("name"),
                solved=row.get("solved"),
                steps=row.get("steps"),
                reward=_fmt(row.get("final_reward")),
                terminal=row.get("terminal"),
                rejected=row.get("rejected_steps"),
                top=row.get("branch_rank_top_match"),
                actions=",".join(row.get("planned_actions") or []),
                sequence=row.get("sequence_file"),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a small deterministic check of the internal simulator/planner loop, not a learned-model benchmark.",
            "- Passing means the kernel can simulate candidate futures, select actions, preserve object/ray identities, and terminate at goals in these maps.",
            "- Branch-rank top-match is tracked separately because final whole-sequence branch ranking is not yet the same thing as stepwise action selection.",
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
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="dream_kernel_small_solve_v001")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "pass_rate": metrics["scenario_metrics"]["pass_rate"],
                "solved": metrics["scenario_metrics"]["solved"],
                "failed": metrics["scenario_metrics"]["failed"],
                "out_dir": _rel(args.out_dir.resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
