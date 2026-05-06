#!/usr/bin/env python3
"""Run a CEM rollout-complexity smoke over Dream Kernel proxy maps.

This uses the repository's real CEMPlanner loop with a deterministic
Dream-Kernel-compatible map world model. It is a local planning integration
smoke, not a trained NanoWM checkpoint eval and not ARC solve evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

DEFAULT_SOURCE_EVAL = ROOT / "experiments" / "2026-05-06_arc_dream_curriculum_eval_v003_safe_path_progress_regate"
DEFAULT_SOURCE_ROWS = DEFAULT_SOURCE_EVAL / "curriculum_eval_rows.jsonl"
DEFAULT_SOURCE_METRICS = DEFAULT_SOURCE_EVAL / "metrics.json"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_dream_kernel_cem_rollout_v038_complexity_smoke"
SCHEMA = "dream_kernel.cem_rollout_smoke.v001"
ROW_SCHEMA = "dream_kernel.cem_rollout_row.v001"
ACTION_DIM = 2
FEATURE_DIM = 6


class DecodedAction(NamedTuple):
    action_id: str
    dx: int
    dy: int


def load_cem_planner():
    path = SRC / "planning" / "cem_planner.py"
    spec = importlib.util.spec_from_file_location("cem_planner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.CEMPlanner


CEMPlanner = load_cem_planner()


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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{_rel(path)}:{line_no} is not valid JSON: {error}") from error
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    _prepare_out_dir(out_dir)
    source_rows_path = args.source_rows.resolve()
    source_metrics_path = args.source_metrics.resolve()
    source_rows = _read_jsonl(source_rows_path)
    if args.max_maps is not None:
        source_rows = source_rows[: args.max_maps]
    if not source_rows:
        raise ValueError(f"no source rows loaded from {_rel(source_rows_path)}")

    torch.manual_seed(args.seed)
    result_rows = [
        run_cem_case(source_row, args, index=index)
        for index, source_row in enumerate(source_rows)
    ]
    condition = condition_payload(args, out_dir, source_rows_path, source_metrics_path)
    metrics = {
        "schema": SCHEMA,
        "condition": condition,
        "row_count": len(result_rows),
        "overall": summarize_rows(result_rows),
        "by_tier": {
            tier: summarize_rows(rows)
            for tier, rows in sorted(group_rows(result_rows, "tier_label").items())
        },
        "source_gate_summary": summarize_source_rows(source_rows),
    }
    _write_jsonl(out_dir / "cem_rollout_rows.jsonl", result_rows)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def _prepare_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty experiment directory: {_rel(out_dir)}")
    out_dir.mkdir(parents=True, exist_ok=True)


def run_cem_case(source_row: dict[str, Any], args: argparse.Namespace, *, index: int) -> dict[str, Any]:
    torch.manual_seed(args.seed + int(source_row["curriculum_index"]))
    map_path = ROOT / source_row["map_path"]
    world_model = DreamKernelMapWorldModel(read_map_rows(map_path), horizon=args.horizon, device=args.device)
    objective_fn = create_cem_objective()
    planner = CEMPlanner(
        world_model=world_model,
        objective_fn=objective_fn,
        action_dim=ACTION_DIM,
        horizon=args.horizon,
        num_samples=args.num_samples,
        topk=args.topk,
        opt_steps=args.opt_steps,
        var_scale=args.var_scale,
        eval_every=args.eval_every,
        sigma_min=args.sigma_min,
        action_low=-args.action_bound,
        action_high=args.action_bound,
        return_policy=args.return_policy,
        name=f"CEM:{int(source_row['curriculum_index']):04d}",
        device=args.device,
    )
    obs_0 = {"visual": world_model.start_obs()}
    obs_g = {"visual": world_model.goal_obs()}
    actions, info = planner.plan(obs_0, obs_g)
    rollout = world_model.evaluate_actions(actions[0])
    optimal_steps = world_model.shortest_safe_path_steps(world_model.start)
    return {
        "schema": ROW_SCHEMA,
        "challenge_id": source_row["challenge_id"],
        "curriculum_index": source_row["curriculum_index"],
        "tier_label": source_row["tier_label"],
        "map_path": source_row["map_path"],
        "source_failure_reason": source_row.get("failure_reason"),
        "source_proxy_goal_solved": bool(source_row.get("proxy_goal_solved")),
        "source_planner_integrity_passed": bool(source_row.get("planner_integrity_passed")),
        "horizon": args.horizon,
        "num_samples": args.num_samples,
        "topk": args.topk,
        "opt_steps": args.opt_steps,
        "return_policy": info.get("return_policy", args.return_policy),
        "cem_final_loss": info.get("final_loss"),
        "cem_best_loss": info.get("best_loss"),
        "cem_initial_loss": (info.get("losses") or [None])[0],
        "cem_loss_delta": ((info.get("losses") or [0.0])[0] - info.get("final_loss", 0.0)),
        "cem_losses": info.get("losses") or [],
        "solved": rollout["solved"],
        "terminal": rollout["terminal"],
        "final_reward": rollout["final_reward"],
        "hazard_hit": rollout["hazard_hit"],
        "blocked_steps": rollout["blocked_steps"],
        "steps_to_goal": rollout["steps_to_goal"],
        "optimal_safe_path_steps": optimal_steps,
        "extra_steps_to_goal": (
            None
            if rollout["steps_to_goal"] is None or optimal_steps is None
            else int(rollout["steps_to_goal"]) - int(optimal_steps)
        ),
        "final_safe_path_steps": rollout["final_safe_path_steps"],
        "planned_actions": rollout["planned_actions"],
        "final_position": coord_payload(rollout["final_position"]),
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "row_index": index,
    }


class DreamKernelMapWorldModel:
    def __init__(self, rows: list[str], *, horizon: int, device: str = "cpu"):
        self.rows = rows
        self.horizon = horizon
        self.device = torch.device(device)
        self.height = len(rows)
        self.width = len(rows[0])
        self.start = find_cell(rows, "A")
        self.goal = find_cell(rows, "G")
        self.blockers = {
            (x, y)
            for y, row in enumerate(rows)
            for x, cell in enumerate(row)
            if cell in {"#", "O"}
        }
        self.hazards = {
            (x, y)
            for y, row in enumerate(rows)
            for x, cell in enumerate(row)
            if cell == "H"
        }

    def start_obs(self) -> torch.Tensor:
        return torch.tensor([[self.features(self.start, False, False, 0)]], dtype=torch.float32, device=self.device)

    def goal_obs(self) -> torch.Tensor:
        return torch.tensor([[self.features(self.goal, True, False, 0)]], dtype=torch.float32, device=self.device)

    def encode_obs(self, obs: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        return {"visual": obs["visual"].float().to(self.device)}

    def rollout(self, *, obs_0: dict[str, torch.Tensor], act: torch.Tensor) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
        features = []
        for action_sequence in act.detach().cpu():
            result = self.evaluate_actions(action_sequence)
            features.append(result["features"])
        visual = torch.tensor(features, dtype=torch.float32, device=act.device)
        return {"visual": visual}, {}

    def evaluate_actions(self, action_sequence: torch.Tensor) -> dict[str, Any]:
        position = self.start
        terminal = False
        solved = False
        hazard_hit = False
        final_reward = 0.0
        blocked_steps = 0
        steps_to_goal = None
        planned_actions = []
        frame_features = []
        for step_index, action_vector in enumerate(action_sequence.detach().cpu()):
            decoded = decode_action_vector(action_vector)
            planned_actions.append(decoded.action_id)
            if terminal:
                frame_features.append(self.features(position, solved, hazard_hit, blocked_steps))
                continue
            target = (position[0] + decoded.dx, position[1] + decoded.dy)
            if decoded.action_id == "wait":
                pass
            elif not self.in_bounds(target) or target in self.blockers:
                blocked_steps += 1
            elif target in self.hazards:
                position = target
                terminal = True
                hazard_hit = True
                final_reward = -1.0
            else:
                position = target
                if position == self.goal:
                    terminal = True
                    solved = True
                    final_reward = 1.0
                    steps_to_goal = step_index + 1
            frame_features.append(self.features(position, solved, hazard_hit, blocked_steps))
        while len(frame_features) < self.horizon:
            frame_features.append(self.features(position, solved, hazard_hit, blocked_steps))
        return {
            "features": frame_features,
            "solved": solved,
            "terminal": terminal,
            "hazard_hit": hazard_hit,
            "final_reward": final_reward,
            "blocked_steps": blocked_steps,
            "steps_to_goal": steps_to_goal,
            "final_safe_path_steps": self.shortest_safe_path_steps(position),
            "planned_actions": planned_actions,
            "final_position": position,
        }

    def features(self, position: tuple[int, int], solved: bool, hazard_hit: bool, blocked_steps: int) -> list[float]:
        return [
            normalize_coord(position[0], self.width),
            normalize_coord(position[1], self.height),
            1.0 if solved else 0.0,
            1.0 if hazard_hit else 0.0,
            min(1.0, blocked_steps / max(1, self.horizon)),
            self.safe_distance_feature(position),
        ]

    def safe_distance_feature(self, position: tuple[int, int]) -> float:
        distance = self.shortest_safe_path_steps(position)
        if distance is None:
            return 1.0
        return min(1.0, distance / max(1, self.width + self.height))

    def shortest_safe_path_steps(self, start: tuple[int, int]) -> int | None:
        if not self.in_bounds(start) or start in self.blockers or start in self.hazards:
            return None
        queue: deque[tuple[tuple[int, int], int]] = deque([(start, 0)])
        seen = {start}
        while queue:
            position, distance = queue.popleft()
            if position == self.goal:
                return distance
            x, y = position
            for candidate in ((x + 1, y), (x, y + 1), (x, y - 1), (x - 1, y)):
                if candidate in seen:
                    continue
                if not self.in_bounds(candidate) or candidate in self.blockers or candidate in self.hazards:
                    continue
                seen.add(candidate)
                queue.append((candidate, distance + 1))
        return None

    def in_bounds(self, position: tuple[int, int]) -> bool:
        x, y = position
        return 0 <= y < self.height and 0 <= x < self.width


def create_cem_objective():
    def objective_fn(z_obs_pred: dict[str, torch.Tensor], z_obs_tgt: dict[str, torch.Tensor]) -> torch.Tensor:
        del z_obs_tgt
        final = z_obs_pred["visual"][:, -1, :]
        safe_distance = final[:, 5]
        solved = final[:, 2]
        hazard = final[:, 3]
        blocked = final[:, 4]
        return safe_distance + (1.0 - solved) + 5.0 * hazard + 0.05 * blocked

    return objective_fn


def decode_action_vector(action_vector: torch.Tensor | list[float] | tuple[float, float], *, wait_threshold: float = 0.15) -> DecodedAction:
    x = float(action_vector[0])
    y = float(action_vector[1])
    if max(abs(x), abs(y)) < wait_threshold:
        return DecodedAction("wait", 0, 0)
    if abs(x) >= abs(y):
        dx = 1 if x >= 0.0 else -1
        return DecodedAction(f"move_entity_0_dx{dx}_dy0_dz0", dx, 0)
    dy = 1 if y >= 0.0 else -1
    return DecodedAction(f"move_entity_0_dx0_dy{dy}_dz0", 0, dy)


def read_map_rows(path: Path) -> list[str]:
    rows = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"{_rel(path)} has no map rows")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"{_rel(path)} has ragged map rows")
    return rows


def find_cell(rows: list[str], marker: str) -> tuple[int, int]:
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell == marker:
                return (x, y)
    raise ValueError(f"map is missing {marker!r}")


def normalize_coord(value: int, span: int) -> float:
    if span <= 1:
        return 0.0
    return float(value) / float(span - 1)


def coord_payload(position: tuple[int, int]) -> dict[str, int]:
    return {"x": int(position[0]), "y": int(position[1]), "z": 0}


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    solved_rows = [row for row in rows if row["solved"]]
    return {
        "rows": count,
        "solved": len(solved_rows),
        "success_rate": len(solved_rows) / max(1, count),
        "terminal": sum(1 for row in rows if row["terminal"]),
        "hazard_hit": sum(1 for row in rows if row["hazard_hit"]),
        "blocked_steps": sum(int(row["blocked_steps"]) for row in rows),
        "mean_final_safe_path_steps": mean(
            row["final_safe_path_steps"] for row in rows if row["final_safe_path_steps"] is not None
        ),
        "mean_steps_to_goal": mean(row["steps_to_goal"] for row in solved_rows if row["steps_to_goal"] is not None),
        "mean_extra_steps_to_goal": mean(
            row["extra_steps_to_goal"] for row in solved_rows if row["extra_steps_to_goal"] is not None
        ),
        "mean_cem_final_loss": mean(row["cem_final_loss"] for row in rows if row["cem_final_loss"] is not None),
        "outcome_counts": dict(sorted(Counter("solved" if row["solved"] else "unsolved" for row in rows).items())),
    }


def summarize_source_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_rows": len(rows),
        "passed_proxy_gate": sum(1 for row in rows if row.get("failure_reason") == "passed_proxy_gate"),
        "branch_rank_top_mismatch": sum(1 for row in rows if row.get("failure_reason") == "branch_rank_top_mismatch"),
        "proxy_goal_unreachable_in_projection": sum(
            1 for row in rows if row.get("failure_reason") == "proxy_goal_unreachable_in_projection"
        ),
        "training_data_promoted": sum(1 for row in rows if row.get("training_data_promoted")),
    }


def group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row[key]), []).append(row)
    return groups


def mean(values: Any) -> float | None:
    values = list(values)
    if not values:
        return None
    return float(sum(float(value) for value in values) / len(values))


def condition_payload(
    args: argparse.Namespace,
    out_dir: Path,
    source_rows_path: Path,
    source_metrics_path: Path,
) -> dict[str, Any]:
    source_metrics = json.loads(source_metrics_path.read_text(encoding="utf-8"))
    source_condition = source_metrics.get("condition") or {}
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "run_label": args.run_label,
        "run_kind": "dream_kernel_cem_rollout_complexity_smoke",
        "run_label_semantics": "new_experiment_real_cem_planner_loop_over_proxy_maps",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "source_condition_artifact": _rel(source_metrics_path),
        "source_eval_rows": _rel(source_rows_path),
        "source_eval_rows_sha256": _sha256(source_rows_path),
        "source_eval_metrics": _rel(source_metrics_path),
        "source_eval_metrics_sha256": _sha256(source_metrics_path),
        "source_eval_run_label": source_condition.get("run_label"),
        "dataset_path": _rel(source_rows_path),
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": args.seed,
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": "not_applicable_posthoc_local_cem_smoke",
        "loader_mode": "jsonl_arc_dream_eval_rows_with_existing_proxy_maps",
        "loader_settings": {
            "planner": "src.planning.cem_planner.CEMPlanner",
            "world_model_adapter": "DreamKernelMapWorldModel",
            "action_space": "continuous_2d_decoded_to_cardinal_or_wait",
            "horizon": args.horizon,
            "num_samples": args.num_samples,
            "topk": args.topk,
            "opt_steps": args.opt_steps,
            "var_scale": args.var_scale,
            "sigma_min": args.sigma_min,
            "action_bound": args.action_bound,
            "return_policy": args.return_policy,
        },
        "quantization_policy": "none",
        "compile_kernel_policy": "not_applicable_python_map_adapter",
        "metric_to_compare": "cem_goal_success_rate_and_mean_final_safe_distance",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _rel(args.historical_comparator_artifact)
        ),
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    overall = metrics["overall"]
    source = metrics["source_gate_summary"]
    lines = [
        "# Dream Kernel CEM Rollout V038 Results",
        "",
        "Status: CEM rollout-complexity smoke over trusted Dream Kernel proxy maps. No training data promoted.",
        "",
        "This is not an ARC solve claim and not a trained NanoWM checkpoint eval. It uses the real CEMPlanner loop with a deterministic map rollout adapter.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- source eval rows: `{condition['source_eval_rows']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        f"- seed: `{condition['seed']}`",
        f"- horizon: `{condition['loader_settings']['horizon']}`",
        f"- num samples: `{condition['loader_settings']['num_samples']}`",
        f"- topk: `{condition['loader_settings']['topk']}`",
        f"- opt steps: `{condition['loader_settings']['opt_steps']}`",
        f"- return policy: `{condition['loader_settings']['return_policy']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        "",
        "## Metrics",
        "",
        f"- source passed proxy gate: `{source['passed_proxy_gate']}/{source['source_rows']}`",
        f"- source branch-rank mismatches: `{source['branch_rank_top_mismatch']}`",
        f"- source unreachable projections: `{source['proxy_goal_unreachable_in_projection']}`",
        f"- CEM solved: `{overall['solved']}/{overall['rows']}`",
        f"- CEM success rate: `{overall['success_rate']}`",
        f"- mean final safe path steps: `{overall['mean_final_safe_path_steps']}`",
        f"- mean steps to goal: `{overall['mean_steps_to_goal']}`",
        f"- mean extra steps to goal: `{overall['mean_extra_steps_to_goal']}`",
        f"- hazard hits: `{overall['hazard_hit']}`",
        f"- blocked steps: `{overall['blocked_steps']}`",
        "",
        "## By Tier",
        "",
        "| tier | rows | solved | success | mean final safe path | mean extra steps |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for tier, row in metrics["by_tier"].items():
        lines.append(
            f"| {tier} | {row['rows']} | {row['solved']} | {row['success_rate']} | {row['mean_final_safe_path_steps']} | {row['mean_extra_steps_to_goal']} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-rows", type=Path, default=DEFAULT_SOURCE_ROWS)
    parser.add_argument("--source-metrics", type=Path, default=DEFAULT_SOURCE_METRICS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="dream_kernel_cem_rollout_v038_complexity_smoke")
    parser.add_argument("--seed", type=int, default=20260506)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--horizon", type=int, default=16)
    parser.add_argument("--num-samples", type=int, default=128)
    parser.add_argument("--topk", type=int, default=16)
    parser.add_argument("--opt-steps", type=int, default=8)
    parser.add_argument("--var-scale", type=float, default=1.0)
    parser.add_argument("--sigma-min", type=float, default=0.05)
    parser.add_argument("--action-bound", type=float, default=1.0)
    parser.add_argument("--return-policy", choices=("mean", "best_sample"), default="best_sample")
    parser.add_argument("--historical-comparator", default="none_first_cem_rollout_complexity_smoke")
    parser.add_argument("--historical-comparator-artifact", type=Path, default=None)
    parser.add_argument("--eval-every", type=int, default=8)
    parser.add_argument("--max-maps", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "rows": metrics["row_count"],
                "success_rate": metrics["overall"]["success_rate"],
                "solved": metrics["overall"]["solved"],
                "mean_final_safe_path_steps": metrics["overall"]["mean_final_safe_path_steps"],
                "out_dir": _rel(args.out_dir.resolve()),
                "training_data_promoted": metrics["condition"]["training_data_promoted"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
