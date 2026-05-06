#!/usr/bin/env python3
"""Run deterministic value/overhead ablations over a Dream Kernel sequence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments" / "2026-05-06_chronometric_sensory_smattering_v034_human_eval"
DEFAULT_SEQUENCE = DEFAULT_EXPERIMENT / "dream_sequence.json"
DEFAULT_CONFIRMATIONS = DEFAULT_EXPERIMENT / "nemo_relay_confirmations.json"
DEFAULT_REVIEWS = DEFAULT_EXPERIMENT / "nemo_relay_reviews.json"
DEFAULT_OUT_DIR = ROOT / "experiments" / "2026-05-06_dream_kernel_ablation_v001_value_layers"
SCORE_LAYERS = (
    "branch_matrix",
    "rays",
    "chrono_datapoints",
    "branch_potentials",
    "object_links",
)
COUNT_KEYS = (
    "ray_contacts",
    "potential_datapoints",
    "branch_potential_refs",
    "object_link_refs",
    "risk_support_refs",
    "nemo_question_refs",
)


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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _canonical_size(value: Any) -> int:
    return len(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def run(args: argparse.Namespace) -> dict[str, Any]:
    sequence_path = args.sequence.resolve()
    confirmations_path = args.confirmations.resolve()
    reviews_path = args.reviews.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    sequence = _read_json(sequence_path)
    confirmations = _read_optional_json(confirmations_path)
    reviews = _read_optional_json(reviews_path)
    if not isinstance(sequence, dict):
        raise ValueError(f"{sequence_path} must contain a JSON object")

    condition = _condition(args, sequence_path, confirmations_path, reviews_path, out_dir)
    context = _context(sequence, confirmations, reviews)
    layer_rows = _layer_rows(context)
    ablation_rows = _ablation_rows(context, layer_rows)
    object_rows = _object_value_rows(context)
    compression = _compression_summary(layer_rows, object_rows)
    metrics = {
        "condition": condition,
        "source_summary": context["source_summary"],
        "layer_rows": layer_rows,
        "ablation_rows": ablation_rows,
        "object_value_summary": _object_value_summary(object_rows),
        "compression_summary": compression,
    }

    (out_dir / "condition.json").write_text(json.dumps(condition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_jsonl(out_dir / "ablation_rows.jsonl", ablation_rows)
    _write_jsonl(out_dir / "layer_value_rows.jsonl", layer_rows)
    _write_jsonl(out_dir / "object_value_rows.jsonl", object_rows)
    (out_dir / "RESULTS.md").write_text(_format_results(metrics), encoding="utf-8")
    return metrics


def _condition(
    args: argparse.Namespace,
    sequence_path: Path,
    confirmations_path: Path,
    reviews_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    condition = {
        "run_label": args.run_label,
        "run_kind": "deterministic_dream_kernel_value_ablation_no_training",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": _rel(script_path),
        "script_sha256": _sha256(script_path),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_dirty": _git_dirty(ignored_paths=[out_dir]),
        "sequence": _rel(sequence_path),
        "sequence_sha256": _sha256(sequence_path),
        "nemo_confirmations": _rel(confirmations_path) if confirmations_path.exists() else None,
        "nemo_confirmations_sha256": _sha256(confirmations_path) if confirmations_path.exists() else None,
        "nemo_reviews": _rel(reviews_path) if reviews_path.exists() else None,
        "nemo_reviews_sha256": _sha256(reviews_path) if reviews_path.exists() else None,
        "dataset_path": "not_applicable_local_dream_sequence_artifact",
        "tokenizer_path": "not_applicable",
        "vocab_size": "not_applicable",
        "seed": "not_applicable_deterministic_artifact_analysis",
        "gpu_count": 0,
        "world_size": 1,
        "wallclock_budget": "not_applicable_posthoc_local_analysis",
        "loader_mode": "json_artifact_direct",
        "loader_settings": {"dream_sequence_schema_required_prefix": "dream_kernel.sequence."},
        "quantization_policy": "none",
        "compile_kernel_policy": "none",
        "metric_to_compare": "proxy_rank_preservation_and_value_density",
        "historical_comparator": "none_first_dream_kernel_value_ablation",
        "historical_comparator_artifact": None,
        "run_label_semantics": "new_experiment",
        "training_data_promoted": False,
    }
    return condition


def _context(
    sequence: dict[str, Any],
    confirmations: dict[str, Any] | None,
    reviews: dict[str, Any] | None,
) -> dict[str, Any]:
    branches = list(sequence.get("branch_matrix") or [])
    frames = {int(frame.get("tick")): frame for frame in sequence.get("frames") or [] if "tick" in frame}
    registry = {
        str(row.get("object_id")): row
        for row in sequence.get("object_registry") or []
        if isinstance(row, dict) and row.get("object_id")
    }
    full_scores = {str(row.get("branch_id")): float(row.get("chrono_y_net") or 0.0) for row in branches}
    branch_ids = [str(row.get("branch_id")) for row in branches]
    critical_objects = {
        object_id
        for object_id, row in registry.items()
        if _is_critical_object(row)
    }
    source_summary = {
        "schema": sequence.get("schema"),
        "sequence_hash": (sequence.get("integrity") or {}).get("sequence_hash"),
        "frames": len(sequence.get("frames") or []),
        "objects": len(registry),
        "branches": len(branches),
        "branch_potentials": len(sequence.get("branch_potentials") or []),
        "object_link_hypotheses": len(sequence.get("object_link_hypotheses") or []),
        "nemo_open_questions": len((sequence.get("nemo_relay") or {}).get("open_questions") or []),
        "nemo_confirmations": len(((confirmations or {}).get("confirmations") or {})),
        "nemo_reviews": len(((reviews or {}).get("reviews") or {})),
    }
    return {
        "sequence": sequence,
        "confirmations": confirmations or {"confirmations": {}},
        "reviews": reviews or {"reviews": {}, "promoted_evidence": {}},
        "branches": branches,
        "frames": frames,
        "registry": registry,
        "critical_objects": critical_objects,
        "branch_ids": branch_ids,
        "full_scores": full_scores,
        "source_summary": source_summary,
    }


def _is_critical_object(row: dict[str, Any]) -> bool:
    category = str(row.get("category_id") or "")
    tags = {str(tag) for tag in row.get("open_tags") or []}
    if category in {"entity.agent.self", "map.terminal.positive", "map.terminal.negative"}:
        return True
    return bool(tags & {"self_anchor", "branch_reward_candidate", "branch_risk_candidate", "terminal"})


def _layer_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        _score_layer_row(context, "branch_matrix", _branch_matrix_scores(context), context["sequence"].get("branch_matrix") or []),
        _score_layer_row(context, "rays", _ray_scores(context), _all_rays(context)),
        _score_layer_row(
            context,
            "chrono_datapoints",
            _chrono_datapoint_scores(context),
            _all_chrono_datapoints(context),
        ),
        _score_layer_row(
            context,
            "branch_potentials",
            _branch_potential_scores(context),
            context["sequence"].get("branch_potentials") or [],
        ),
        _score_layer_row(
            context,
            "object_links",
            _object_link_scores(context),
            context["sequence"].get("object_link_hypotheses") or [],
        ),
        _metadata_layer_row(
            context,
            "object_registry_categories",
            context["sequence"].get("object_registry") or [],
            _registry_objects(context),
        ),
        _metadata_layer_row(
            context,
            "nemo_relay_questions",
            (context["sequence"].get("nemo_relay") or {}).get("open_questions") or [],
            _nemo_question_objects(context),
        ),
        _nemo_confirmation_row(context),
    ]
    return sorted(rows, key=lambda row: (-float(row["proxy_value_density_per_kb"]), row["layer"]))


def _score_layer_row(
    context: dict[str, Any],
    layer: str,
    scores: dict[str, float],
    payload: Any,
) -> dict[str, Any]:
    full = context["full_scores"]
    branch_ids = context["branch_ids"]
    objects = _objects_for_layer(context, layer)
    bytes_used = _canonical_size(payload)
    metrics = _score_metrics(full, scores, branch_ids)
    object_coverage = _coverage(objects, set(context["registry"]))
    critical_coverage = _coverage(objects, context["critical_objects"])
    terminal_coverage = _terminal_branch_coverage(context, set(scores))
    value_score = _proxy_value_score(metrics, object_coverage, critical_coverage, terminal_coverage)
    return {
        "layer": layer,
        "layer_kind": "score_layer",
        "items": _item_count(payload),
        "bytes": bytes_used,
        "bytes_pct_of_sequence": bytes_used / max(1, _canonical_size(context["sequence"])),
        "referenced_objects": len(objects),
        "object_coverage": object_coverage,
        "critical_object_coverage": critical_coverage,
        "terminal_branch_coverage": terminal_coverage,
        "proxy_value_score": value_score,
        "proxy_value_density_per_kb": value_score / max(bytes_used / 1024.0, 0.001),
        **metrics,
    }


def _metadata_layer_row(
    context: dict[str, Any],
    layer: str,
    payload: Any,
    objects: set[str],
) -> dict[str, Any]:
    bytes_used = _canonical_size(payload)
    object_coverage = _coverage(objects, set(context["registry"]))
    critical_coverage = _coverage(objects, context["critical_objects"])
    value_score = 0.45 * critical_coverage + 0.35 * object_coverage + 0.20 * min(1.0, _item_count(payload) / 12.0)
    return {
        "layer": layer,
        "layer_kind": "metadata_layer",
        "items": _item_count(payload),
        "bytes": bytes_used,
        "bytes_pct_of_sequence": bytes_used / max(1, _canonical_size(context["sequence"])),
        "referenced_objects": len(objects),
        "object_coverage": object_coverage,
        "critical_object_coverage": critical_coverage,
        "terminal_branch_coverage": None,
        "proxy_value_score": value_score,
        "proxy_value_density_per_kb": value_score / max(bytes_used / 1024.0, 0.001),
        "pearson_to_full": None,
        "spearman_to_full": None,
        "sign_accuracy": None,
        "top_branch_match": None,
        "normalized_mae_to_full": None,
    }


def _nemo_confirmation_row(context: dict[str, Any]) -> dict[str, Any]:
    confirmations = (context["confirmations"].get("confirmations") or {})
    branch_ids = set(context["branch_ids"])
    relay_ok = [row for row in confirmations.values() if row.get("relay_ok") is not False]
    parsed = [_parse_confirmation(row) for row in relay_ok]
    confidences = [float(row.get("confidence")) for row in parsed if isinstance(row.get("confidence"), (int, float))]
    bytes_used = _canonical_size(context["confirmations"])
    branch_coverage = _coverage(set(confirmations), branch_ids)
    parse_coverage = len(parsed) / max(1, len(branch_ids))
    value_score = 0.45 * branch_coverage + 0.30 * parse_coverage + 0.25 * min(1.0, sum(confidences) / max(1, len(confidences)))
    return {
        "layer": "nemo_confirmations",
        "layer_kind": "semantic_sidecar",
        "items": len(confirmations),
        "bytes": bytes_used,
        "bytes_pct_of_sequence": bytes_used / max(1, _canonical_size(context["sequence"])),
        "referenced_objects": 0,
        "object_coverage": None,
        "critical_object_coverage": None,
        "terminal_branch_coverage": branch_coverage,
        "proxy_value_score": value_score,
        "proxy_value_density_per_kb": value_score / max(bytes_used / 1024.0, 0.001),
        "pearson_to_full": None,
        "spearman_to_full": None,
        "sign_accuracy": None,
        "top_branch_match": None,
        "normalized_mae_to_full": None,
        "relay_ok": len(relay_ok),
        "parseable_confirmations": len(parsed),
        "mean_confirmation_confidence": sum(confidences) / len(confidences) if confidences else None,
    }


def _ablation_rows(context: dict[str, Any], layer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    score_maps = {
        "branch_matrix": _branch_matrix_scores(context),
        "rays": _ray_scores(context),
        "chrono_datapoints": _chrono_datapoint_scores(context),
        "branch_potentials": _branch_potential_scores(context),
        "object_links": _object_link_scores(context),
    }
    layer_bytes = {row["layer"]: int(row["bytes"]) for row in layer_rows}
    full_proxy = _aggregate_scores(context["branch_ids"], score_maps.values())
    rows = [_ablation_row(context, "full_proxy_all_score_layers", "keep_all", full_proxy, 0)]
    for layer in SCORE_LAYERS:
        kept = [scores for name, scores in score_maps.items() if name != layer]
        rows.append(
            _ablation_row(
                context,
                f"drop_{layer}",
                "drop_score_layer",
                _aggregate_scores(context["branch_ids"], kept),
                layer_bytes.get(layer, 0),
            )
        )
    semantic_bytes = layer_bytes.get("nemo_confirmations", 0) + layer_bytes.get("nemo_relay_questions", 0)
    rows.append(
        _ablation_row(
            context,
            "drop_semantic_relay_sidecars",
            "drop_non_deterministic_semantic_layers",
            full_proxy,
            semantic_bytes,
        )
    )
    rows.append(
        _ablation_row(
            context,
            "drop_object_registry_categories",
            "drop_open_category_metadata",
            full_proxy,
            layer_bytes.get("object_registry_categories", 0),
        )
    )
    return rows


def _ablation_row(
    context: dict[str, Any],
    ablation: str,
    ablation_kind: str,
    scores: dict[str, float],
    bytes_removed: int,
) -> dict[str, Any]:
    metrics = _score_metrics(context["full_scores"], scores, context["branch_ids"])
    preserved = _preservation_score(metrics)
    return {
        "ablation": ablation,
        "ablation_kind": ablation_kind,
        "bytes_removed": bytes_removed,
        "bytes_removed_pct_of_sequence": bytes_removed / max(1, _canonical_size(context["sequence"])),
        "rank_preservation_score": preserved,
        "compression_candidate": bytes_removed > 0 and preserved >= 0.90,
        **metrics,
    }


def _object_value_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    registry = context["registry"]
    rows: dict[str, dict[str, Any]] = {
        object_id: {
            "object_id": object_id,
            "category_id": row.get("category_id"),
            "open_tags": row.get("open_tags") or [],
            "bytes": _canonical_size(row),
            "critical_object": _is_critical_object(row),
            "signed_y_abs_sum": 0.0,
            **{key: 0 for key in COUNT_KEYS},
        }
        for object_id, row in registry.items()
    }
    for frame in context["frames"].values():
        for ray in frame.get("rays") or []:
            object_id = str((ray.get("contact") or {}).get("object_id") or "")
            if object_id in rows:
                rows[object_id]["ray_contacts"] += 1
                rows[object_id]["signed_y_abs_sum"] += abs(float(ray.get("signed_potential_y") or 0.0))
        for datum in (frame.get("chronometric") or {}).get("potential_datapoints") or []:
            object_id = str(datum.get("object_id") or "")
            if object_id in rows:
                rows[object_id]["potential_datapoints"] += 1
                rows[object_id]["signed_y_abs_sum"] += abs(float(datum.get("chrono_y", datum.get("value") or 0.0) or 0.0))
    for potential in context["sequence"].get("branch_potentials") or []:
        object_id = str(potential.get("object_id") or "")
        if object_id in rows:
            rows[object_id]["branch_potential_refs"] += 1
            rows[object_id]["signed_y_abs_sum"] += abs(float(potential.get("chrono_y_correlation") or 0.0))
    for link in context["sequence"].get("object_link_hypotheses") or []:
        for key in ("source_object_id", "target_object_id"):
            object_id = str(link.get(key) or "")
            if object_id in rows:
                rows[object_id]["object_link_refs"] += 1
                rows[object_id]["signed_y_abs_sum"] += abs(float(link.get("chrono_y_correlation") or 0.0))
    for branch in context["branches"]:
        for object_id in [*(branch.get("supporting_objects") or []), *(branch.get("risk_objects") or [])]:
            if object_id in rows:
                rows[object_id]["risk_support_refs"] += 1
    for question in (context["sequence"].get("nemo_relay") or {}).get("open_questions") or []:
        object_id = str(question.get("object_id") or "")
        if object_id in rows:
            rows[object_id]["nemo_question_refs"] += 1

    for row in rows.values():
        count_score = (
            row["ray_contacts"] * 2.0
            + row["potential_datapoints"] * 1.0
            + row["branch_potential_refs"] * 1.0
            + row["object_link_refs"] * 0.25
            + row["risk_support_refs"] * 3.0
            + row["nemo_question_refs"] * 0.5
        )
        row["proxy_object_value_score"] = count_score + row["signed_y_abs_sum"] + (8.0 if row["critical_object"] else 0.0)
        row["proxy_value_density_per_kb"] = row["proxy_object_value_score"] / max(row["bytes"] / 1024.0, 0.001)
        row["compression_candidate"] = (
            not row["critical_object"]
            and str(row["category_id"]) == "map.structural.wall"
            and row["proxy_object_value_score"] <= 12.0
        )
    return sorted(rows.values(), key=lambda row: (row["proxy_object_value_score"], row["object_id"]))


def _object_value_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if row["compression_candidate"]]
    return {
        "objects": len(rows),
        "compression_candidates": len(candidates),
        "candidate_ids": [row["object_id"] for row in candidates],
        "lowest_value_objects": [
            {
                "object_id": row["object_id"],
                "category_id": row["category_id"],
                "proxy_object_value_score": row["proxy_object_value_score"],
            }
            for row in rows[:6]
        ],
    }


def _compression_summary(layer_rows: list[dict[str, Any]], object_rows: list[dict[str, Any]]) -> dict[str, Any]:
    value_layers = [row for row in layer_rows if row.get("proxy_value_score") is not None]
    densities = sorted(float(row["proxy_value_density_per_kb"]) for row in value_layers)
    median_density = densities[len(densities) // 2] if densities else 0.0
    low_density_layers = [
        row["layer"]
        for row in value_layers
        if float(row["proxy_value_density_per_kb"]) < median_density * 0.5
        and row["layer"] not in {"branch_matrix", "object_registry_categories"}
    ]
    high_value_layers = [
        row["layer"]
        for row in value_layers
        if float(row["proxy_value_score"]) >= 0.80
    ]
    candidate_objects = [row["object_id"] for row in object_rows if row["compression_candidate"]]
    return {
        "median_layer_value_density_per_kb": median_density,
        "high_value_layers": high_value_layers,
        "low_density_layers_for_sparse_or_gated_attention": low_density_layers,
        "object_compression_candidates": candidate_objects,
        "recommended_policy": (
            "Keep deterministic branch_matrix/object_registry as integrity anchors. "
            "Use sparse/gated attention first on low-density semantic or relation layers, "
            "and only skip low-value structural walls until a branch becomes stuck or uncertain."
        ),
    }


def _score_metrics(full: dict[str, float], scores: dict[str, float], branch_ids: list[str]) -> dict[str, Any]:
    target = [float(full.get(branch_id, 0.0)) for branch_id in branch_ids]
    observed = [float(scores.get(branch_id, 0.0)) for branch_id in branch_ids]
    return {
        "pearson_to_full": _pearson(target, observed),
        "spearman_to_full": _spearman(target, observed),
        "sign_accuracy": _sign_accuracy(target, observed),
        "top_branch_match": _top_branch(target, branch_ids) == _top_branch(observed, branch_ids),
        "normalized_mae_to_full": _normalized_mae(target, observed),
    }


def _proxy_value_score(
    metrics: dict[str, Any],
    object_coverage: float,
    critical_coverage: float,
    terminal_coverage: float,
) -> float:
    corr = max(0.0, float(metrics["spearman_to_full"] or 0.0))
    sign = float(metrics["sign_accuracy"] or 0.0)
    top = 1.0 if metrics["top_branch_match"] else 0.0
    return 0.36 * corr + 0.20 * sign + 0.14 * top + 0.12 * object_coverage + 0.12 * critical_coverage + 0.06 * terminal_coverage


def _preservation_score(metrics: dict[str, Any]) -> float:
    corr = max(0.0, float(metrics["spearman_to_full"] or 0.0))
    sign = float(metrics["sign_accuracy"] or 0.0)
    top = 1.0 if metrics["top_branch_match"] else 0.0
    mae = float(metrics["normalized_mae_to_full"] or 1.0)
    return 0.42 * corr + 0.24 * sign + 0.18 * top + 0.16 * max(0.0, 1.0 - mae)


def _branch_matrix_scores(context: dict[str, Any]) -> dict[str, float]:
    return dict(context["full_scores"])


def _ray_scores(context: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for branch in context["branches"]:
        frame = context["frames"].get(int(branch.get("end_tick") or -1), {})
        values = [float(ray.get("signed_potential_y") or 0.0) for ray in frame.get("rays") or []]
        scores[str(branch.get("branch_id"))] = sum(values) / max(1, len(values))
    return scores


def _chrono_datapoint_scores(context: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for branch in context["branches"]:
        frame = context["frames"].get(int(branch.get("end_tick") or -1), {})
        values = [
            float(datum.get("chrono_y", datum.get("value") or 0.0) or 0.0)
            for datum in (frame.get("chronometric") or {}).get("potential_datapoints") or []
        ]
        scores[str(branch.get("branch_id"))] = sum(values) / max(1, len(values))
    return scores


def _branch_potential_scores(context: dict[str, Any]) -> dict[str, float]:
    scores = {branch_id: [] for branch_id in context["branch_ids"]}
    for row in context["sequence"].get("branch_potentials") or []:
        branch_id = str(row.get("branch_id") or "")
        if branch_id in scores:
            scores[branch_id].append(float(row.get("chrono_y_correlation") or 0.0))
    return {branch_id: sum(values) / max(1, len(values)) for branch_id, values in scores.items()}


def _object_link_scores(context: dict[str, Any]) -> dict[str, float]:
    scores = {branch_id: [] for branch_id in context["branch_ids"]}
    for row in context["sequence"].get("object_link_hypotheses") or []:
        branch_id = str(row.get("branch_id") or "")
        if branch_id in scores:
            probability = float(row.get("probability") or 0.0)
            scores[branch_id].append(float(row.get("chrono_y_correlation") or 0.0) * max(0.05, probability))
    return {branch_id: sum(values) / max(1, len(values)) for branch_id, values in scores.items()}


def _aggregate_scores(branch_ids: list[str], score_maps: Iterable[dict[str, float]]) -> dict[str, float]:
    score_maps = list(score_maps)
    out: dict[str, float] = {}
    normalized = [_normalize_scores(branch_ids, scores) for scores in score_maps]
    for branch_id in branch_ids:
        values = [scores.get(branch_id, 0.0) for scores in normalized]
        out[branch_id] = sum(values) / max(1, len(values))
    return out


def _normalize_scores(branch_ids: list[str], scores: dict[str, float]) -> dict[str, float]:
    values = [float(scores.get(branch_id, 0.0)) for branch_id in branch_ids]
    if not values:
        return {}
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        return {branch_id: 0.0 for branch_id in branch_ids}
    return {branch_id: (float(scores.get(branch_id, 0.0)) - lo) / (hi - lo) * 2.0 - 1.0 for branch_id in branch_ids}


def _objects_for_layer(context: dict[str, Any], layer: str) -> set[str]:
    if layer == "branch_matrix":
        objects: set[str] = set()
        for branch in context["branches"]:
            objects.update(str(item) for item in branch.get("supporting_objects") or [])
            objects.update(str(item) for item in branch.get("risk_objects") or [])
        return objects
    if layer == "rays":
        return {
            str((ray.get("contact") or {}).get("object_id"))
            for ray in _all_rays(context)
            if (ray.get("contact") or {}).get("object_id")
        }
    if layer == "chrono_datapoints":
        return {str(row.get("object_id")) for row in _all_chrono_datapoints(context) if row.get("object_id")}
    if layer == "branch_potentials":
        return {str(row.get("object_id")) for row in context["sequence"].get("branch_potentials") or [] if row.get("object_id")}
    if layer == "object_links":
        objects = set()
        for row in context["sequence"].get("object_link_hypotheses") or []:
            objects.add(str(row.get("source_object_id")))
            objects.add(str(row.get("target_object_id")))
        return {object_id for object_id in objects if object_id and object_id != "None"}
    return set()


def _all_rays(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for frame in context["frames"].values():
        rows.extend(frame.get("rays") or [])
    return rows


def _all_chrono_datapoints(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for frame in context["frames"].values():
        rows.extend((frame.get("chronometric") or {}).get("potential_datapoints") or [])
    return rows


def _registry_objects(context: dict[str, Any]) -> set[str]:
    return set(context["registry"])


def _nemo_question_objects(context: dict[str, Any]) -> set[str]:
    return {
        str(row.get("object_id"))
        for row in (context["sequence"].get("nemo_relay") or {}).get("open_questions") or []
        if row.get("object_id")
    }


def _terminal_branch_coverage(context: dict[str, Any], covered_branches: set[str]) -> float:
    terminal_branches = {
        str(branch.get("branch_id"))
        for branch in context["branches"]
        if (context["frames"].get(int(branch.get("end_tick") or -1), {}).get("outcome") or {}).get("terminal")
    }
    return _coverage(covered_branches, terminal_branches)


def _coverage(observed: set[str], expected: set[str]) -> float:
    if not expected:
        return 1.0
    return len(observed & expected) / len(expected)


def _item_count(payload: Any) -> int:
    if isinstance(payload, (list, tuple, set, dict)):
        return len(payload)
    return 1


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    left_den = math.sqrt(sum((a - left_mean) ** 2 for a in left))
    right_den = math.sqrt(sum((b - right_mean) ** 2 for b in right))
    if left_den == 0 or right_den == 0:
        return None
    return numerator / (left_den * right_den)


def _spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    return _pearson(_ranks(left), _ranks(right))


def _ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and math.isclose(indexed[end][1], indexed[index][1]):
            end += 1
        rank = (index + end - 1) / 2.0
        for original, _value in indexed[index:end]:
            ranks[original] = rank
        index = end
    return ranks


def _sign_accuracy(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    return sum(_sign(a) == _sign(b) for a, b in zip(left, right)) / len(left)


def _sign(value: float) -> int:
    if value > 0.0001:
        return 1
    if value < -0.0001:
        return -1
    return 0


def _top_branch(scores: list[float], branch_ids: list[str]) -> str | None:
    if not scores or not branch_ids:
        return None
    return branch_ids[max(range(len(scores)), key=lambda index: scores[index])]


def _normalized_mae(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 1.0
    left_norm = list(_normalize_vector(left))
    right_norm = list(_normalize_vector(right))
    return sum(abs(a - b) for a, b in zip(left_norm, right_norm)) / len(left_norm)


def _normalize_vector(values: list[float]) -> list[float]:
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        return [0.0 for _ in values]
    return [(value - lo) / (hi - lo) * 2.0 - 1.0 for value in values]


def _parse_confirmation(row: dict[str, Any]) -> dict[str, Any]:
    text = str(row.get("response_text") or "").strip()
    if not text:
        return {}
    candidates = [text]
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _format_results(metrics: dict[str, Any]) -> str:
    condition = metrics["condition"]
    source = metrics["source_summary"]
    layers = metrics["layer_rows"]
    ablations = metrics["ablation_rows"]
    compression = metrics["compression_summary"]
    lines = [
        "# Dream Kernel Ablation V001 Results",
        "",
        "Status: deterministic posthoc value/overhead analysis. No training data promoted.",
        "",
        "## Condition",
        "",
        f"- run label: `{condition['run_label']}`",
        f"- run kind: `{condition['run_kind']}`",
        f"- run label semantics: `{condition['run_label_semantics']}`",
        f"- git commit: `{condition['git_commit']}`",
        f"- git dirty at run: `{condition['git_dirty']}`",
        f"- script: `{condition['script']}`",
        f"- sequence: `{condition['sequence']}`",
        f"- sequence sha256: `{condition['sequence_sha256']}`",
        f"- metric: `{condition['metric_to_compare']}`",
        "",
        "## Source",
        "",
        f"- schema: `{source['schema']}`",
        f"- sequence hash: `{source['sequence_hash']}`",
        f"- frames: `{source['frames']}`",
        f"- objects: `{source['objects']}`",
        f"- branches: `{source['branches']}`",
        f"- branch potentials: `{source['branch_potentials']}`",
        f"- object links: `{source['object_link_hypotheses']}`",
        f"- Nemo open questions: `{source['nemo_open_questions']}`",
        f"- Nemo confirmations: `{source['nemo_confirmations']}`",
        f"- Nemo reviews: `{source['nemo_reviews']}`",
        "",
        "## Layer Value Density",
        "",
        "| layer | kind | items | bytes | value | density/kB | spearman | sign acc | top match | object coverage |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in layers:
        lines.append(
            "| {layer} | {kind} | {items} | {bytes} | {value} | {density} | {spearman} | {sign} | {top} | {objects} |".format(
                layer=row["layer"],
                kind=row["layer_kind"],
                items=row["items"],
                bytes=row["bytes"],
                value=_fmt(row.get("proxy_value_score")),
                density=_fmt(row.get("proxy_value_density_per_kb")),
                spearman=_fmt(row.get("spearman_to_full")),
                sign=_fmt(row.get("sign_accuracy")),
                top=row.get("top_branch_match"),
                objects=_fmt(row.get("object_coverage")),
            )
        )
    lines.extend(
        [
            "",
            "## Drop-Ablation Proxy",
            "",
            "| ablation | bytes removed | preservation | compression candidate | spearman | sign acc | top match | norm MAE |",
            "| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |",
        ]
    )
    for row in ablations:
        lines.append(
            "| {name} | {bytes} | {preserve} | {candidate} | {spearman} | {sign} | {top} | {mae} |".format(
                name=row["ablation"],
                bytes=row["bytes_removed"],
                preserve=_fmt(row["rank_preservation_score"]),
                candidate=row["compression_candidate"],
                spearman=_fmt(row.get("spearman_to_full")),
                sign=_fmt(row.get("sign_accuracy")),
                top=row.get("top_branch_match"),
                mae=_fmt(row.get("normalized_mae_to_full")),
            )
        )
    lines.extend(
        [
            "",
            "## Compression Readout",
            "",
            f"- high-value layers: `{compression['high_value_layers']}`",
            f"- low-density layers for sparse/gated attention: `{compression['low_density_layers_for_sparse_or_gated_attention']}`",
            f"- object compression candidates: `{compression['object_compression_candidates']}`",
            f"- recommended policy: {compression['recommended_policy']}",
            "",
            "## Interpretation",
            "",
            "- This is a proxy analysis against the deterministic full branch score, not ground-truth human preference.",
            "- A layer can be system-critical even if it is low-density; the compression pass should gate it, not delete it.",
            "- Use human reviews to decide which Nemo semantic outputs become training targets.",
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
    parser.add_argument("--sequence", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--confirmations", type=Path, default=DEFAULT_CONFIRMATIONS)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-label", default="dream_kernel_ablation_v001_value_layers")
    return parser.parse_args()


def main() -> int:
    metrics = run(parse_args())
    summary = {
        "run_label": metrics["condition"]["run_label"],
        "source_sequence_hash": metrics["source_summary"]["sequence_hash"],
        "top_value_layer": metrics["layer_rows"][0]["layer"] if metrics["layer_rows"] else None,
        "low_density_layers": metrics["compression_summary"]["low_density_layers_for_sparse_or_gated_attention"],
        "object_compression_candidates": metrics["compression_summary"]["object_compression_candidates"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
