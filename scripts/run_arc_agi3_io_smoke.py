#!/usr/bin/env python3
"""Run an ARC-AGI-3 environment I/O readiness smoke.

This is a local/offline challenge-interface smoke. It loads a real downloaded
ARC-AGI-3 environment through the official toolkit, records observation/action
metadata, emits candidate action packets, and optionally steps local state.
It is not a solver, not a score submission, and not an ARC solve claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARC_REPO = Path("/home/frosty40/world_model_1")
DEFAULT_ENVIRONMENTS_DIR = DEFAULT_ARC_REPO / "environment_files"
DEFAULT_SOURCE_CONDITION = DEFAULT_ARC_REPO / "docs" / "arc-agi-3-env.md"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_arc_agi3_io_v041_offline_smoke"
SCHEMA = "arc_agi3.io_smoke.v001"
ROW_SCHEMA = "arc_agi3.io_row.v001"
ACTION_SCHEMA = "arc_agi3.candidate_action_packet.v001"


def _git(repo: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _git_dirty(repo: Path, *, ignored_paths: list[Path] | None = None) -> bool:
    status = _git(repo, ["status", "--short", "--untracked-files=all"])
    if status == "unknown":
        return True
    ignored = [_rel(repo, path).rstrip("/") for path in ignored_paths or []]
    for line in status.splitlines():
        status_path = line[3:].strip()
        if " -> " in status_path:
            status_path = status_path.split(" -> ", 1)[1]
        if any(status_path == item or status_path.startswith(f"{item}/") for item in ignored):
            continue
        return True
    return False


def _rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def _repo_rel(path: Path) -> str:
    return _rel(ROOT, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_arcade():
    try:
        from arc_agi import Arcade, OperationMode
    except ImportError as error:
        raise RuntimeError(
            "arc_agi is not importable. Run this smoke with an interpreter that has arc-agi installed, "
            "for example /home/frosty40/world_model_1/.venv/bin/python."
        ) from error
    return Arcade, OperationMode


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir.resolve()
    prepare_out_dir(out_dir)
    arc_repo = args.arc_repo.resolve()
    environments_dir = args.environments_dir.resolve()
    source_condition = args.source_condition_artifact.resolve()
    if not source_condition.exists():
        raise FileNotFoundError(source_condition)
    if not environments_dir.exists():
        raise FileNotFoundError(environments_dir)

    Arcade, OperationMode = load_arcade()
    operation_mode = getattr(OperationMode, args.operation_mode)
    arcade = Arcade(operation_mode=operation_mode, environments_dir=str(environments_dir))
    games = normalize_games(arcade.get_environments())
    selected_game = select_game(games, args.game)
    env = arcade.make(selected_game["name"])
    reset_obs = env.reset()
    if reset_obs is None:
        raise RuntimeError(f"{selected_game['name']} reset returned None")

    observation_rows: list[dict[str, Any]] = [
        observation_row(
            reset_obs,
            env=env,
            game_name=selected_game["name"],
            phase="reset",
            step_index=0,
            executed_action=None,
        )
    ]
    candidate_packets = candidate_action_packets(
        env=env,
        game_name=selected_game["name"],
        observation_guid=str(getattr(reset_obs, "guid", "")),
        phase="reset",
        max_actions=args.max_candidate_actions,
    )

    executed_steps = 0
    for step_index in range(args.step_count):
        if not candidate_packets:
            break
        packet = candidate_packets[min(step_index, len(candidate_packets) - 1)]
        action = action_by_value(env.action_space, packet["action_value"])
        next_obs = env.step(
            action,
            reasoning={
                "run_label": args.run_label,
                "policy": "io_smoke_first_available_action",
                "arc_solve_claim": False,
            },
        )
        executed_steps += 1
        if next_obs is None:
            break
        observation_rows.append(
            observation_row(
                next_obs,
                env=env,
                game_name=selected_game["name"],
                phase="local_step",
                step_index=step_index + 1,
                executed_action=packet,
            )
        )
        candidate_packets.extend(
            candidate_action_packets(
                env=env,
                game_name=selected_game["name"],
                observation_guid=str(getattr(next_obs, "guid", "")),
                phase=f"local_step_{step_index + 1}",
                max_actions=args.max_candidate_actions,
                packet_offset=len(candidate_packets),
            )
        )

    condition = condition_payload(
        args,
        out_dir=out_dir,
        arc_repo=arc_repo,
        environments_dir=environments_dir,
        source_condition=source_condition,
        selected_game=selected_game,
        arcade=arcade,
    )
    metrics = summarize(
        condition=condition,
        games=games,
        observation_rows=observation_rows,
        candidate_packets=candidate_packets,
        executed_steps=executed_steps,
    )
    _write_jsonl(out_dir / "arc_agi3_io_rows.jsonl", observation_rows)
    _write_jsonl(out_dir / "candidate_action_packets.jsonl", candidate_packets)
    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "RESULTS.md").write_text(format_results(metrics), encoding="utf-8")
    return metrics


def prepare_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty experiment directory: {_repo_rel(out_dir)}")
    out_dir.mkdir(parents=True, exist_ok=True)


def normalize_games(games: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in games or []:
        game_id = str(getattr(item, "game_id", "") or getattr(item, "id", "") or item)
        title = str(getattr(item, "title", "") or "")
        name = game_id.split("-", 1)[0] if "-" in game_id else game_id
        normalized.append(
            {
                "game_id": game_id,
                "name": name,
                "title": title or name.upper(),
            }
        )
    return sorted(normalized, key=lambda row: row["game_id"])


def select_game(games: list[dict[str, Any]], requested: str) -> dict[str, Any]:
    if not games:
        raise RuntimeError("no ARC-AGI-3 environments are available in the selected operation mode")
    requested_lower = requested.lower()
    for game in games:
        if requested_lower in {game["name"].lower(), game["game_id"].lower(), game["title"].lower()}:
            return game
    available = ", ".join(game["name"] for game in games[:20])
    raise ValueError(f"requested game {requested!r} is not available; first available games: {available}")


def observation_row(
    obs: Any,
    *,
    env: Any,
    game_name: str,
    phase: str,
    step_index: int,
    executed_action: dict[str, Any] | None,
) -> dict[str, Any]:
    frame_summary = summarize_frame_stack(getattr(obs, "frame", None))
    return {
        "schema": ROW_SCHEMA,
        "game_name": game_name,
        "game_id": str(getattr(obs, "game_id", getattr(env.info, "game_id", ""))),
        "phase": phase,
        "step_index": step_index,
        "guid": str(getattr(obs, "guid", "")),
        "state": state_name(getattr(obs, "state", None)),
        "levels_completed": int(getattr(obs, "levels_completed", 0)),
        "win_levels": int(getattr(obs, "win_levels", 0)),
        "full_reset": bool(getattr(obs, "full_reset", False)),
        "available_action_values": action_values(getattr(env, "action_space", [])),
        "executed_action_value": None if executed_action is None else executed_action["action_value"],
        "frame_stack_len": frame_summary["frame_stack_len"],
        "latest_frame_shape": frame_summary["latest_frame_shape"],
        "latest_frame_min": frame_summary["latest_frame_min"],
        "latest_frame_max": frame_summary["latest_frame_max"],
        "latest_frame_sha256": frame_summary["latest_frame_sha256"],
        "training_data_promoted": False,
        "arc_solve_claim": False,
    }


def summarize_frame_stack(frame_stack: Any) -> dict[str, Any]:
    if not frame_stack:
        return {
            "frame_stack_len": 0,
            "latest_frame_shape": [],
            "latest_frame_min": None,
            "latest_frame_max": None,
            "latest_frame_sha256": None,
        }
    latest = frame_stack[-1]
    shape = list(getattr(latest, "shape", []))
    raw = latest.tobytes() if hasattr(latest, "tobytes") else json.dumps(latest, sort_keys=True).encode("utf-8")
    return {
        "frame_stack_len": len(frame_stack),
        "latest_frame_shape": [int(value) for value in shape],
        "latest_frame_min": int(latest.min()) if hasattr(latest, "min") else None,
        "latest_frame_max": int(latest.max()) if hasattr(latest, "max") else None,
        "latest_frame_sha256": hashlib.sha256(raw).hexdigest(),
    }


def candidate_action_packets(
    *,
    env: Any,
    game_name: str,
    observation_guid: str,
    phase: str,
    max_actions: int,
    packet_offset: int = 0,
) -> list[dict[str, Any]]:
    packets = []
    for index, action in enumerate(list(getattr(env, "action_space", []))[:max_actions]):
        packets.append(
            {
                "schema": ACTION_SCHEMA,
                "packet_index": packet_offset + index,
                "game_name": game_name,
                "game_id": str(getattr(env.info, "game_id", "")),
                "phase": phase,
                "observation_guid": observation_guid,
                "action_name": action_name(action),
                "action_value": action_value(action),
                "reasoning": {
                    "policy": "io_smoke_enumerate_available_actions",
                    "submit_online": False,
                    "arc_solve_claim": False,
                },
                "training_data_promoted": False,
                "arc_solve_claim": False,
            }
        )
    return packets


def action_by_value(actions: Any, value: int) -> Any:
    for action in actions:
        if action_value(action) == value:
            return action
    raise ValueError(f"action value {value} is not available")


def action_values(actions: Any) -> list[int]:
    return [action_value(action) for action in actions]


def action_value(action: Any) -> int:
    return int(getattr(action, "value", action))


def action_name(action: Any) -> str:
    return str(getattr(action, "name", f"ACTION{action_value(action)}"))


def state_name(state: Any) -> str:
    return str(getattr(state, "name", state))


def package_version(module_name: str) -> str:
    try:
        module = __import__(module_name)
    except ImportError:
        return "not_importable"
    return str(getattr(module, "__version__", "unknown"))


def condition_payload(
    args: argparse.Namespace,
    *,
    out_dir: Path,
    arc_repo: Path,
    environments_dir: Path,
    source_condition: Path,
    selected_game: dict[str, Any],
    arcade: Any,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "run_label": args.run_label,
        "run_kind": "arc_agi3_environment_io_smoke",
        "run_label_semantics": "new_experiment_offline_arc_agi3_io_readiness",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _repo_rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(ROOT, ["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ROOT, ignored_paths=[out_dir]),
        "source_condition_artifact": _rel(arc_repo, source_condition),
        "source_condition_sha256": _sha256(source_condition),
        "source_repo_path": str(arc_repo),
        "source_repo_commit": _git(arc_repo, ["rev-parse", "HEAD"]),
        "source_repo_dirty": _git_dirty(arc_repo),
        "dataset_path": _rel(arc_repo, environments_dir),
        "environments_dir": str(environments_dir),
        "selected_game": selected_game,
        "operation_mode": args.operation_mode,
        "toolkit": "arc_agi.Arcade",
        "toolkit_versions": {
            "arc_agi": package_version("arc_agi"),
            "arcengine": package_version("arcengine"),
        },
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_environment_reset",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": "not_applicable_local_io_smoke",
        "loader_mode": "arc_agi_offline_local_environment_wrapper",
        "loader_settings": {
            "operation_mode": args.operation_mode,
            "game": args.game,
            "max_candidate_actions": args.max_candidate_actions,
            "step_count": args.step_count,
            "online_submission": False,
            "scorecard_submission": False,
        },
        "metric_to_compare": "arc_agi3_io_validity_and_candidate_action_packet_count",
        "historical_comparator": args.historical_comparator,
        "historical_comparator_artifact": (
            None if args.historical_comparator_artifact is None else _repo_rel(args.historical_comparator_artifact)
        ),
        "quantization_policy": "none",
        "compile_kernel_policy": "not_applicable_python_sdk_io",
        "arc_data_used": True,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
        "arcade_class": type(arcade).__name__,
    }


def summarize(
    *,
    condition: dict[str, Any],
    games: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
    candidate_packets: list[dict[str, Any]],
    executed_steps: int,
) -> dict[str, Any]:
    frame_shapes = sorted({tuple(row["latest_frame_shape"]) for row in observation_rows})
    available_action_counts = [len(row["available_action_values"]) for row in observation_rows]
    valid = bool(
        observation_rows
        and candidate_packets
        and all(row["latest_frame_shape"] == [64, 64] for row in observation_rows if row["latest_frame_shape"])
        and all(row["latest_frame_min"] is None or 0 <= row["latest_frame_min"] <= 15 for row in observation_rows)
        and all(row["latest_frame_max"] is None or 0 <= row["latest_frame_max"] <= 15 for row in observation_rows)
        and not condition["training_data_promoted"]
        and not condition["arc_solve_claim"]
        and not condition["online_submission"]
    )
    return {
        "schema": SCHEMA,
        "condition": condition,
        "available_game_count": len(games),
        "selected_game": condition["selected_game"],
        "observation_rows": len(observation_rows),
        "candidate_action_packets": len(candidate_packets),
        "executed_local_steps": executed_steps,
        "frame_shapes": [list(shape) for shape in frame_shapes],
        "available_action_count_min": min(available_action_counts) if available_action_counts else 0,
        "available_action_count_max": max(available_action_counts) if available_action_counts else 0,
        "states_observed": sorted({row["state"] for row in observation_rows}),
        "levels_completed_max": max((row["levels_completed"] for row in observation_rows), default=0),
        "win_levels_max": max((row["win_levels"] for row in observation_rows), default=0),
        "valid_io_smoke": valid,
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
        "scorecard_submission": False,
    }


def format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    lines = [
        "# ARC-AGI-3 I/O V041 Results",
        "",
        "Status: local/offline ARC-AGI-3 environment I/O smoke. No online submission, no score claim, no training data promoted.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- source condition: `{condition['source_condition_artifact']}`",
        f"- environments dir: `{condition['dataset_path']}`",
        f"- operation mode: `{condition['operation_mode']}`",
        f"- selected game: `{condition['selected_game']['game_id']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        f"- training data promoted: `{condition['training_data_promoted']}`",
        f"- ARC solve claim: `{condition['arc_solve_claim']}`",
        f"- online submission: `{condition['online_submission']}`",
        "",
        "## Metrics",
        "",
        f"- valid I/O smoke: `{metrics['valid_io_smoke']}`",
        f"- available games: `{metrics['available_game_count']}`",
        f"- observation rows: `{metrics['observation_rows']}`",
        f"- candidate action packets: `{metrics['candidate_action_packets']}`",
        f"- executed local steps: `{metrics['executed_local_steps']}`",
        f"- frame shapes: `{metrics['frame_shapes']}`",
        f"- action count range: `{metrics['available_action_count_min']}..{metrics['available_action_count_max']}`",
        f"- states observed: `{metrics['states_observed']}`",
        f"- max levels completed: `{metrics['levels_completed_max']}`",
        f"- max win levels: `{metrics['win_levels_max']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arc-repo", type=Path, default=DEFAULT_ARC_REPO)
    parser.add_argument("--environments-dir", type=Path, default=DEFAULT_ENVIRONMENTS_DIR)
    parser.add_argument("--source-condition-artifact", type=Path, default=DEFAULT_SOURCE_CONDITION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="arc_agi3_io_v041_offline_smoke")
    parser.add_argument("--operation-mode", choices=("OFFLINE",), default="OFFLINE")
    parser.add_argument("--game", default="ls20")
    parser.add_argument("--max-candidate-actions", type=int, default=8)
    parser.add_argument("--step-count", type=int, default=1)
    parser.add_argument("--historical-comparator", default="none_first_arc_agi3_io_smoke")
    parser.add_argument("--historical-comparator-artifact", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run(args)
    print(
        json.dumps(
            {
                "run_label": metrics["condition"]["run_label"],
                "valid_io_smoke": metrics["valid_io_smoke"],
                "selected_game": metrics["selected_game"],
                "observation_rows": metrics["observation_rows"],
                "candidate_action_packets": metrics["candidate_action_packets"],
                "executed_local_steps": metrics["executed_local_steps"],
                "out_dir": _repo_rel(args.out_dir.resolve()),
                "training_data_promoted": metrics["training_data_promoted"],
                "arc_solve_claim": metrics["arc_solve_claim"],
                "online_submission": metrics["online_submission"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
