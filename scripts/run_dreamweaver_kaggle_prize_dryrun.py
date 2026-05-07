#!/usr/bin/env python3
"""Run Dreamweaver's no-internet ARC-AGI-3 competition mechanics locally.

Default mode is OFFLINE so this command does not touch official scorecards or
spend API-backed actions. Use COMPETITION only in the intended Kaggle/runtime
environment after the package preflight is green.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dreamweaver_prize_runner import DEFAULT_MODEL_NAME, PrizeRunnerConfig, run_prize_candidate  # noqa: E402
from scripts.run_arc_agi3_io_smoke import (  # noqa: E402
    DEFAULT_ARC_REPO,
    DEFAULT_ENVIRONMENTS_DIR,
    DEFAULT_SOURCE_CONDITION,
    _repo_rel,
    load_arcade,
)


DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-07_dreamweaver_kaggle_prize_offline_mechanics_dryrun"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--recordings-dir", type=Path, default=ROOT / "recordings")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="dreamweaver_arc_agi3_kaggle_prize_offline_mechanics_dryrun")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--operation-mode", choices=("OFFLINE", "COMPETITION"), default="OFFLINE")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-actions-per-environment", type=int, default=1)
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument("--branch-ambiguity-gap-threshold", type=float, default=0.0)
    parser.add_argument("--internal-rollout-max-steps", type=int, default=32)
    parser.add_argument("--internal-rollout-kernel-timeout", type=int, default=30)
    parser.add_argument("--arc-grid-agent-label", type=int, default=None)
    parser.add_argument("--arc-grid-goal-label", type=int, default=None)
    parser.add_argument("--arc-grid-wall-labels", default="")
    parser.add_argument("--arc-grid-hazard-labels", default="")
    parser.add_argument("--require-internal-solve", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    Arcade, OperationMode = load_arcade()
    operation_mode = getattr(OperationMode, args.operation_mode)
    arcade = Arcade(
        operation_mode=operation_mode,
        environments_dir=str(args.environments_dir.resolve()),
        recordings_dir=str(args.recordings_dir.resolve()),
    )
    config = PrizeRunnerConfig(
        out_dir=args.out_dir.resolve(),
        run_label=args.run_label,
        model_name=args.model_name,
        operation_mode=args.operation_mode,
        max_actions_per_environment=args.max_actions_per_environment,
        max_candidate_actions=args.max_candidate_actions,
        seed=args.seed,
        require_internal_solve=args.require_internal_solve,
        branch_ambiguity_gap_threshold=args.branch_ambiguity_gap_threshold,
        internal_rollout_max_steps=args.internal_rollout_max_steps,
        internal_rollout_kernel_timeout=args.internal_rollout_kernel_timeout,
        arc_grid_agent_label=args.arc_grid_agent_label,
        arc_grid_goal_label=args.arc_grid_goal_label,
        arc_grid_wall_labels=args.arc_grid_wall_labels,
        arc_grid_hazard_labels=args.arc_grid_hazard_labels,
        source_condition_artifact=args.source_condition_artifact.resolve(),
        arc_repo=args.arc_repo.resolve(),
        environments_dir=args.environments_dir.resolve(),
    )
    metrics = run_prize_candidate(arcade=arcade, config=config)
    print(
        json.dumps(
            {
                "run_label": metrics["run_label"],
                "operation_mode": args.operation_mode,
                "competition_mode": metrics["competition_mode"],
                "all_environment_runner": metrics["all_environment_runner"],
                "one_make_per_environment": metrics["one_make_per_environment"],
                "scorecard_reads_during_run": metrics["scorecard_reads_during_run"],
                "external_api_used": metrics["external_api_used"],
                "source_env_solver_used": metrics["source_env_solver_used"],
                "offline_mirror_used": metrics["offline_mirror_used"],
                "actions_executed": metrics["actions_executed"],
                "scorecard_id": metrics["scorecard_id"],
                "out_dir": _repo_rel(args.out_dir.resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
