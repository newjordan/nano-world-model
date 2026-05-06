#!/usr/bin/env python
"""Serve a local human-eval harness for chronometric sensory records."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dream_kernel_sequence_validation import require_dream_sequence

DEFAULT_EXPERIMENT = ROOT / "experiments" / "2026-05-06_chronometric_sensory_smattering_v034_human_eval"
LABEL_SCHEMA = "chronometric.human_eval_labels.v001"
LABEL_FILE = "human_labels.json"
EVENT_FILE = "human_label_events.jsonl"
MARKDOWN_FILE = "HUMAN_LABELS.md"
DREAM_SEQUENCE_FILE = "dream_sequence.json"
NEMO_CONFIRMATION_FILE = "nemo_relay_confirmations.json"
NEMO_REVIEW_FILE = "nemo_relay_reviews.json"
NEMO_REVIEW_EVENT_FILE = "nemo_relay_review_events.jsonl"
NEMO_RELAY_URL = os.environ.get("NEMO_RELAY_URL", "http://127.0.0.1:8000/v1/responses")
NEMO_RELAY_MODEL = os.environ.get("NEMO_RELAY_MODEL", "nemotron_3_nano_omni")
THREE_MODULE_PATH = ROOT / "vendor" / "three" / "three.module.min.js"
GRID_KEYS = ("predicted_grid", "truth_grid", "predicted_after_grid", "actual_after_grid")
HUMAN_LABELS = {"", "accept", "reject", "unsure"}
OUTCOME_LABELS = {
    "",
    "sensible_positive",
    "sensible_negative",
    "visual_map_failure",
    "temporal_transition_failure",
    "outcome_sign_failure",
    "outcome_magnitude_failure",
    "not_enough_info",
}
FAILURE_MODES = {
    "visual.map",
    "visual.geometry_projection",
    "temporal.transition",
    "outcome.polarity",
    "outcome.magnitude",
    "prompt_mismatch",
    "other",
}
NEMO_REVIEW_LABELS = {"", "trust", "partial", "reject", "needs_more"}
NEMO_PROMOTION_FIELDS = (
    "category_revisions",
    "relation_candidates",
    "evidence_needed",
    "action_recommendation",
)


def main() -> int:
    args = _parse_args()
    experiment_dir = args.experiment.resolve()
    load_session(experiment_dir)

    server = HumanEvalServer((args.host, args.port), HumanEvalHandler, experiment_dir=experiment_dir)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Human eval harness: {url}", flush=True)
    print(f"Experiment: {experiment_dir}", flush=True)
    print(f"Labels: {experiment_dir / LABEL_FILE}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def load_session(experiment_dir: Path) -> dict[str, Any]:
    experiment_dir = experiment_dir.resolve()
    condition = _read_json(experiment_dir / "condition.json")
    metrics = _read_json(experiment_dir / "metrics.json")
    records = _read_jsonl(experiment_dir / "sensory_records.jsonl")
    records = _with_review_assets(records, condition)
    labels_payload = load_labels(experiment_dir)
    dream_sequence = load_dream_sequence(experiment_dir)
    nemo_confirmations = load_nemo_confirmations(experiment_dir)
    nemo_reviews = load_nemo_reviews(experiment_dir)
    return {
        "experiment": {
            "path": str(experiment_dir),
            "record_file": str(experiment_dir / "sensory_records.jsonl"),
            "label_file": str(experiment_dir / LABEL_FILE),
            "event_file": str(experiment_dir / EVENT_FILE),
            "markdown_file": str(experiment_dir / MARKDOWN_FILE),
            "dream_sequence_file": str(experiment_dir / DREAM_SEQUENCE_FILE),
            "nemo_confirmation_file": str(experiment_dir / NEMO_CONFIRMATION_FILE),
            "nemo_review_file": str(experiment_dir / NEMO_REVIEW_FILE),
            "nemo_review_event_file": str(experiment_dir / NEMO_REVIEW_EVENT_FILE),
        },
        "condition": condition,
        "metrics": metrics,
        "records": records,
        "labels": labels_payload.get("labels", {}),
        "label_schema": LABEL_SCHEMA,
        "dream_sequence": dream_sequence,
        "nemo_confirmations": nemo_confirmations,
        "nemo_reviews": nemo_reviews,
    }


def load_labels(experiment_dir: Path) -> dict[str, Any]:
    path = experiment_dir / LABEL_FILE
    if not path.exists():
        return {"schema": LABEL_SCHEMA, "labels": {}}
    payload = _read_json(path)
    labels = payload.get("labels")
    if not isinstance(labels, dict):
        raise ValueError(f"{path} must contain a labels object")
    return payload


def load_dream_sequence(experiment_dir: Path) -> dict[str, Any] | None:
    path = experiment_dir / DREAM_SEQUENCE_FILE
    if not path.exists():
        return None
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    frames = payload.get("frames")
    if not isinstance(frames, list):
        raise ValueError(f"{path} must contain a frames list")
    require_dream_sequence(payload, source=str(path))
    return payload


def load_nemo_confirmations(experiment_dir: Path) -> dict[str, Any]:
    path = experiment_dir / NEMO_CONFIRMATION_FILE
    if not path.exists():
        return {"schema": "dream_kernel.nemo_relay_confirmations.v001", "confirmations": {}}
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    payload.setdefault("schema", "dream_kernel.nemo_relay_confirmations.v001")
    payload.setdefault("confirmations", {})
    return payload


def load_nemo_reviews(experiment_dir: Path) -> dict[str, Any]:
    path = experiment_dir / NEMO_REVIEW_FILE
    if not path.exists():
        return {
            "schema": "dream_kernel.nemo_relay_reviews.v001",
            "reviews": {},
            "promoted_evidence": {},
        }
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    payload.setdefault("schema", "dream_kernel.nemo_relay_reviews.v001")
    payload.setdefault("reviews", {})
    payload.setdefault("promoted_evidence", {})
    return payload


def sanitize_label(payload: dict[str, Any], case_ids: set[str]) -> dict[str, Any]:
    case_id = str(payload.get("case_id", "")).strip()
    if case_id not in case_ids:
        raise ValueError(f"unknown case_id: {case_id}")

    human_label = str(payload.get("human_label", "")).strip()
    if human_label not in HUMAN_LABELS:
        raise ValueError(f"human_label must be one of {sorted(HUMAN_LABELS)}")

    outcome_label = str(payload.get("outcome_label", "")).strip()
    if outcome_label not in OUTCOME_LABELS:
        raise ValueError(f"outcome_label must be one of {sorted(OUTCOME_LABELS)}")

    rank = _clean_rank(payload.get("rank"))
    failure_modes = _clean_failure_modes(payload.get("failure_modes", []))
    image_notes = _clean_image_notes(payload.get("image_notes", {}))
    return {
        "case_id": case_id,
        "human_label": human_label or None,
        "rank": rank,
        "outcome_label": outcome_label or None,
        "failure_modes": failure_modes,
        "human_notes": _clean_text(payload.get("human_notes", ""), limit=20000),
        "image_notes": image_notes,
        "reviewed_at": _now_iso(),
    }


def save_label(experiment_dir: Path, label: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    experiment_dir = experiment_dir.resolve()
    payload = load_labels(experiment_dir)
    payload["schema"] = LABEL_SCHEMA
    payload["experiment_path"] = str(experiment_dir)
    payload["source_record_file"] = str(experiment_dir / "sensory_records.jsonl")
    payload["updated_at"] = _now_iso()
    payload.setdefault("labels", {})
    payload["labels"][label["case_id"]] = label

    _write_json_atomic(experiment_dir / LABEL_FILE, payload)
    _append_jsonl(
        experiment_dir / EVENT_FILE,
        {
            "event": "label_saved",
            "saved_at": label["reviewed_at"],
            "label": label,
        },
    )
    _write_markdown(experiment_dir / MARKDOWN_FILE, payload, session)
    return payload


def sanitize_nemo_review(payload: dict[str, Any], branch_ids: set[str]) -> dict[str, Any]:
    branch_id = str(payload.get("branch_id", "")).strip()
    if branch_id not in branch_ids:
        raise ValueError(f"unknown branch_id: {branch_id}")

    review_label = str(payload.get("review_label", "")).strip()
    if review_label not in NEMO_REVIEW_LABELS:
        raise ValueError(f"review_label must be one of {sorted(NEMO_REVIEW_LABELS)}")

    source_flags = payload.get("promotion_flags")
    if not isinstance(source_flags, dict):
        source_flags = {}
    promotion_flags = {
        field: _clean_bool(source_flags.get(field, payload.get(f"promote_{field}", False)))
        for field in NEMO_PROMOTION_FIELDS
    }
    return {
        "branch_id": branch_id,
        "review_label": review_label or None,
        "promotion_flags": promotion_flags,
        "review_notes": _clean_text(payload.get("review_notes", ""), limit=20000),
        "reviewed_at": _now_iso(),
    }


def save_nemo_review(experiment_dir: Path, review: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    experiment_dir = experiment_dir.resolve()
    payload = load_nemo_reviews(experiment_dir)
    branch_id = review["branch_id"]
    payload["schema"] = "dream_kernel.nemo_relay_reviews.v001"
    payload["experiment_path"] = str(experiment_dir)
    payload["source_dream_sequence_file"] = str(experiment_dir / DREAM_SEQUENCE_FILE)
    payload["source_confirmation_file"] = str(experiment_dir / NEMO_CONFIRMATION_FILE)
    payload["updated_at"] = review["reviewed_at"]
    payload.setdefault("reviews", {})[branch_id] = review

    promoted = _promoted_evidence_from_review(review, session)
    payload.setdefault("promoted_evidence", {})
    if promoted is None:
        payload["promoted_evidence"].pop(branch_id, None)
    else:
        payload["promoted_evidence"][branch_id] = promoted

    _write_json_atomic(experiment_dir / NEMO_REVIEW_FILE, payload)
    _append_jsonl(
        experiment_dir / NEMO_REVIEW_EVENT_FILE,
        {
            "event": "nemo_review_saved",
            "saved_at": review["reviewed_at"],
            "review": review,
            "promoted_evidence": promoted,
        },
    )
    return payload


def _promoted_evidence_from_review(review: dict[str, Any], session: dict[str, Any]) -> dict[str, Any] | None:
    promotion_flags = review.get("promotion_flags") or {}
    selected_fields = [field for field in NEMO_PROMOTION_FIELDS if promotion_flags.get(field)]
    if not selected_fields:
        return None

    branch_id = review["branch_id"]
    confirmation = ((session.get("nemo_confirmations") or {}).get("confirmations") or {}).get(branch_id)
    if not isinstance(confirmation, dict):
        raise ValueError(f"cannot promote {branch_id}: no Nemo confirmation exists")
    if confirmation.get("relay_ok") is False:
        raise ValueError(f"cannot promote {branch_id}: Nemo confirmation is marked relay_ok=false")

    parsed = _parse_confirmation_json(confirmation)
    promoted: dict[str, Any] = {
        "schema": "dream_kernel.promoted_branch_evidence.v001",
        "branch_id": branch_id,
        "promoted_at": review["reviewed_at"],
        "review_label": review.get("review_label"),
        "promotion_flags": {field: bool(promotion_flags.get(field)) for field in NEMO_PROMOTION_FIELDS},
        "source_confirmation": {
            "created_at": confirmation.get("created_at"),
            "model": confirmation.get("model"),
            "relay_url": confirmation.get("relay_url"),
        },
        "source_confidence": parsed.get("confidence"),
    }
    for field in selected_fields:
        promoted[field] = parsed.get(field)
    return promoted


def _parse_confirmation_json(confirmation: dict[str, Any]) -> dict[str, Any]:
    text = str(confirmation.get("response_text") or "").strip()
    if not text:
        raise ValueError("Nemo confirmation response_text is empty")
    candidates = [text]
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        candidates.append("\n".join(lines).strip())
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])
    last_error: Exception | None = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(parsed, dict):
            raise ValueError("Nemo confirmation JSON must decode to an object")
        return parsed
    raise ValueError(f"Nemo confirmation response_text is not parseable JSON: {last_error}")


def run_nemo_relay(experiment_dir: Path, payload: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    sequence = session.get("dream_sequence") or {}
    branch_id = str(payload.get("branch_id", "")).strip()
    if not branch_id:
        raise ValueError("branch_id is required")
    branch_ids = {str(branch.get("branch_id")) for branch in sequence.get("branch_matrix", [])}
    if branch_id not in branch_ids:
        raise ValueError(f"unknown branch_id: {branch_id}")

    packet = _nemo_branch_packet(sequence, branch_id)
    relay_ok = True
    relay_error = None
    try:
        model_response = _call_nemo(packet)
    except Exception as exc:  # noqa: BLE001
        relay_ok = False
        relay_error = str(exc)
        model_response = f"Nemo relay failed: {relay_error}"
    confirmation = {
        "schema": "dream_kernel.nemo_branch_confirmation.v001",
        "branch_id": branch_id,
        "created_at": _now_iso(),
        "model": NEMO_RELAY_MODEL,
        "relay_url": NEMO_RELAY_URL,
        "relay_ok": relay_ok,
        "relay_error": relay_error,
        "request_counts": {
            "branch_potentials": len(packet["branch_potentials"]),
            "object_link_hypotheses": len(packet["object_link_hypotheses"]),
            "open_questions": len(packet["open_questions"]),
        },
        "response_text": model_response,
    }
    confirmations = load_nemo_confirmations(experiment_dir)
    confirmations["updated_at"] = confirmation["created_at"]
    confirmations.setdefault("confirmations", {})[branch_id] = confirmation
    _write_json_atomic(experiment_dir / NEMO_CONFIRMATION_FILE, confirmations)
    return confirmation


def _nemo_branch_packet(sequence: dict[str, Any], branch_id: str) -> dict[str, Any]:
    branch = next(
        (row for row in sequence.get("branch_matrix", []) if str(row.get("branch_id")) == branch_id),
        None,
    )
    if not isinstance(branch, dict):
        raise ValueError(f"missing branch matrix row for {branch_id}")
    potentials = [
        _compact_branch_potential(row)
        for row in sequence.get("branch_potentials", [])
        if str(row.get("branch_id")) == branch_id
    ][:16]
    links = [
        _compact_object_link(row)
        for row in sequence.get("object_link_hypotheses", [])
        if str(row.get("branch_id")) == branch_id
    ][:16]
    questions = [
        _compact_open_question(row)
        for row in (sequence.get("nemo_relay") or {}).get("open_questions", [])
        if row.get("branch_id") == branch_id
    ][:12]
    registry = {
        str(row.get("object_id")): {
            "category_id": row.get("category_id"),
            "open_tags": row.get("open_tags", []),
            "map_coord": row.get("map_coord"),
            "hypothesis_refs": row.get("hypothesis_refs", [])[:6],
        }
        for row in sequence.get("object_registry", [])
        if isinstance(row, dict)
    }
    return {
        "schema": "dream_kernel.nemo_branch_packet.v001",
        "branch": branch,
        "object_registry_subset": {
            object_id: registry[object_id]
            for object_id in sorted(
                {
                    str(row.get("object_id"))
                    for row in potentials
                    if row.get("object_id") is not None
                }
                | {
                    str(row.get("source_object_id"))
                    for row in links
                    if row.get("source_object_id") is not None
                }
                | {
                    str(row.get("target_object_id"))
                    for row in links
                    if row.get("target_object_id") is not None
                }
            )
            if object_id in registry
        },
        "branch_potentials": potentials,
        "object_link_hypotheses": links,
        "open_questions": questions,
        "instruction": (
            "Act as Nemo semantic relay. Keep categories open-ended, evaluate possible object "
            "relations, identify what evidence would confirm or reject them, and return compact "
            "JSON with only these top-level keys: branch_id, category_revisions, "
            "relation_candidates, confidence, evidence_needed, action_recommendation. "
            "Keep arrays short: at most 4 category revisions, 6 relation candidates, "
            "and 6 evidence-needed entries. "
            "Do not expose hidden reasoning."
        ),
    }


def _compact_branch_potential(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "potential_id": row.get("potential_id"),
        "branch_id": row.get("branch_id"),
        "object_id": row.get("object_id"),
        "category_id": row.get("category_id"),
        "event_coord": row.get("event_coord"),
        "outcome_probability": row.get("outcome_probability"),
        "positive_probability": row.get("positive_probability"),
        "negative_probability": row.get("negative_probability"),
        "chrono_y_correlation": row.get("chrono_y_correlation"),
        "evidence_sources": row.get("evidence_sources", [])[:4],
        "relation_candidate_ids": row.get("relation_candidate_ids", [])[:4],
        "hypothesis": _short_text(row.get("hypothesis", ""), 240),
    }


def _compact_object_link(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "link_id": row.get("link_id"),
        "branch_id": row.get("branch_id"),
        "source_object_id": row.get("source_object_id"),
        "target_object_id": row.get("target_object_id"),
        "relation_kind": row.get("relation_kind"),
        "probability": row.get("probability"),
        "chrono_y_correlation": row.get("chrono_y_correlation"),
        "evidence_sources": row.get("evidence_sources", [])[:4],
        "unresolved_questions": [
            _short_text(item, 180) for item in row.get("unresolved_questions", [])[:2]
        ],
    }


def _compact_open_question(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": row.get("question_id"),
        "branch_id": row.get("branch_id"),
        "object_id": row.get("object_id"),
        "link_id": row.get("link_id"),
        "prompt": _short_text(row.get("prompt", ""), 360),
        "hypothesis_refs": row.get("hypothesis_refs", [])[:4],
        "expected_answer_shape": row.get("expected_answer_shape"),
    }


def _short_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: limit - 1] + "..."


def _call_nemo(packet: dict[str, Any]) -> str:
    if NEMO_RELAY_URL.endswith("/v1/responses"):
        body = {
            "model": NEMO_RELAY_MODEL,
            "input": (
                "You are Nemo, a semantic relay for an internal deterministic world-model. "
                "Return one compact final JSON object only in output_text. Do not include private reasoning. "
                "Prefer a short best-effort answer over exhaustive analysis.\n"
                "NEMO_RELAY_PACKET:\n"
                + json.dumps(packet, sort_keys=True)
            ),
            "temperature": 0.1,
            "max_output_tokens": 4096,
        }
    else:
        body = {
            "model": NEMO_RELAY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Nemo, a semantic relay for an internal deterministic world-model. "
                        "Return compact final JSON only in message.content. Do not include private reasoning."
                    ),
                },
                {"role": "user", "content": json.dumps(packet, sort_keys=True)},
            ],
            "temperature": 0.1,
            "max_tokens": 1200,
        }
    request = Request(
        NEMO_RELAY_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:  # noqa: S310 - local relay URL is operator controlled.
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"Nemo relay HTTP {exc.code}: {body or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Nemo relay connection failed: {exc.reason}") from exc
    content = _extract_nemo_text(payload)
    if not content:
        raise ValueError("Nemo relay returned an empty final answer")
    return content


def _extract_nemo_text(payload: dict[str, Any]) -> str:
    output_texts: list[str] = []
    for item in payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text" and content.get("text"):
                output_texts.append(str(content["text"]))
    if output_texts:
        return "\n".join(output_texts).strip()

    choices = payload.get("choices") or []
    if choices:
        content = (choices[0].get("message") or {}).get("content")
        if content:
            return str(content).strip()
        text = choices[0].get("text")
        if text:
            return str(text).strip()
    return ""


def _with_review_assets(records: list[dict[str, Any]], condition: dict[str, Any]) -> list[dict[str, Any]]:
    fallback_assets = _fallback_review_assets(condition)
    enriched = []
    for record in records:
        row = dict(record)
        assets = row.get("review_assets")
        if not isinstance(assets, dict):
            assets = fallback_assets.get(str(row.get("state_id", "")))
        if isinstance(assets, dict):
            row["review_assets"] = assets
        enriched.append(row)
    return enriched


def _fallback_review_assets(condition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if condition.get("run_type") != "chronometric_sensory_smattering_v034":
        return {}
    script_path = ROOT / "scripts" / "run_chronometric_sensory_smattering.py"
    spec = importlib.util.spec_from_file_location("_chronometric_sensory_smattering_v034", script_path)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assets: dict[str, dict[str, Any]] = {}
    for case in module._cases():
        assets[str(case.case_id)] = {
            "schema": "chronometric.grid_review.v001",
            "predicted_grid": _grid_to_lists(case.predicted_grid),
            "truth_grid": _grid_to_lists(case.truth_grid),
            "predicted_after_grid": _grid_to_lists(case.predicted_after_grid),
            "actual_after_grid": _grid_to_lists(case.actual_after_grid),
        }
    return assets


def _clean_rank(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        rank = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("rank must be blank or an integer from 1 to 5") from exc
    if rank < 1 or rank > 5:
        raise ValueError("rank must be blank or an integer from 1 to 5")
    return rank


def _clean_failure_modes(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("failure_modes must be a list")
    modes = []
    for mode in value:
        text = str(mode).strip()
        if text not in FAILURE_MODES:
            raise ValueError(f"unknown failure mode: {text}")
        if text not in modes:
            modes.append(text)
    return modes


def _clean_image_notes(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("image_notes must be an object")
    notes: dict[str, str] = {}
    for key in GRID_KEYS:
        notes[key] = _clean_text(value.get(key, ""), limit=8000)
    return notes


def _clean_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _clean_text(value: Any, *, limit: int) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return text[:limit]


def _write_markdown(path: Path, payload: dict[str, Any], session: dict[str, Any]) -> None:
    records = {record["state_id"]: record for record in session["records"]}
    lines = [
        "# Human Labels",
        "",
        f"Updated: `{payload.get('updated_at', '')}`",
        f"Source records: `{payload.get('source_record_file', '')}`",
        "",
    ]
    labels = payload.get("labels", {})
    if not labels:
        lines.extend(["No labels saved yet.", ""])
    for case_id, label in sorted(labels.items(), key=lambda item: (_rank_sort(item[1]), item[0])):
        record = records.get(case_id, {})
        lines.extend(
            [
                f"## {case_id}",
                "",
                f"- description: {record.get('case_description', '')}",
                f"- rank: `{label.get('rank')}`",
                f"- human_label: `{label.get('human_label')}`",
                f"- outcome_label: `{label.get('outcome_label')}`",
                f"- failure_modes: `{label.get('failure_modes', [])}`",
                f"- reviewed_at: `{label.get('reviewed_at', '')}`",
                "",
                "### Notes",
                "",
                label.get("human_notes") or "",
                "",
                "### Image Notes",
                "",
            ]
        )
        image_notes = label.get("image_notes", {})
        for key in GRID_KEYS:
            lines.extend([f"- {key}: {image_notes.get(key, '')}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _rank_sort(label: dict[str, Any]) -> int:
    rank = label.get("rank")
    return int(rank) if isinstance(rank, int) else 99


def _grid_to_lists(grid: Any) -> list[list[int]]:
    return [[int(value) for value in row] for row in grid]


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no} is not a JSON object")
        rows.append(row)
    return rows


def _write_json_atomic(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class HumanEvalServer(ThreadingHTTPServer):
    def __init__(self, *args: Any, experiment_dir: Path, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.experiment_dir = experiment_dir


class HumanEvalHandler(BaseHTTPRequestHandler):
    server: HumanEvalServer

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route in {"/", "/index.html"}:
            self._send_text(INDEX_HTML, content_type="text/html; charset=utf-8")
            return
        if route == "/vendor/three/three.module.min.js":
            self._send_file(THREE_MODULE_PATH, content_type="text/javascript; charset=utf-8")
            return
        if route == "/api/session":
            self._send_json(load_session(self.server.experiment_dir))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/nemo-relay":
            try:
                payload = self._read_json_body()
                session = load_session(self.server.experiment_dir)
                confirmation = run_nemo_relay(self.server.experiment_dir, payload, session)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"ok": True, "confirmation": confirmation})
            return
        if route == "/api/nemo-review":
            try:
                payload = self._read_json_body()
                session = load_session(self.server.experiment_dir)
                sequence = session.get("dream_sequence") or {}
                branch_ids = {str(branch.get("branch_id")) for branch in sequence.get("branch_matrix", [])}
                review = sanitize_nemo_review(payload, branch_ids)
                reviews_payload = save_nemo_review(self.server.experiment_dir, review, session)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"ok": True, "review": review, "nemo_reviews": reviews_payload})
            return
        if route != "/api/label":
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return
        try:
            payload = self._read_json_body()
            session = load_session(self.server.experiment_dir)
            case_ids = {str(record["state_id"]) for record in session["records"]}
            label = sanitize_label(payload, case_ids)
            labels_payload = save_label(self.server.experiment_dir, label, session)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"ok": True, "label": label, "labels": labels_payload.get("labels", {})})

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), format % args))

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def _send_json(self, payload: Any, *, status: int | HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, body: str, *, content_type: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path, *, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Human Eval Harness</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f6f1;
      --panel: #ffffff;
      --panel-soft: #fbfaf5;
      --ink: #1f2428;
      --muted: #66706c;
      --line: #d8d5ca;
      --accent: #0b6f73;
      --warn: #b45f06;
      --bad: #b3261e;
      --good: #1f7a4d;
      --focus: #f0c94f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    button, select, textarea {
      font: inherit;
    }
    .app {
      display: grid;
      grid-template-columns: minmax(270px, 340px) minmax(0, 1fr);
      min-height: 100vh;
    }
    .sidebar {
      border-right: 1px solid var(--line);
      background: #efede5;
      padding: 18px;
      overflow: auto;
      max-height: 100vh;
    }
    .brand {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }
    h1 {
      font-size: 20px;
      line-height: 1.15;
      margin: 0;
      letter-spacing: 0;
    }
    .progress {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }
    .case-list {
      display: grid;
      gap: 8px;
    }
    .case-button {
      width: 100%;
      min-height: 74px;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 8px;
      text-align: left;
      padding: 10px;
      cursor: pointer;
    }
    .case-button.active {
      outline: 3px solid rgba(11, 111, 115, 0.24);
      border-color: var(--accent);
    }
    .case-id {
      display: block;
      font-weight: 700;
      font-size: 13px;
      margin-bottom: 6px;
      overflow-wrap: anywhere;
    }
    .case-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .pill {
      display: inline-flex;
      min-height: 22px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      color: var(--muted);
      background: var(--panel-soft);
      white-space: nowrap;
    }
    .pill.good { color: var(--good); border-color: rgba(31, 122, 77, 0.35); }
    .pill.bad { color: var(--bad); border-color: rgba(179, 38, 30, 0.35); }
    .pill.warn { color: var(--warn); border-color: rgba(180, 95, 6, 0.35); }
    .main {
      padding: 20px 22px 30px;
      overflow: auto;
      max-height: 100vh;
    }
    .topline {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      border-bottom: 1px solid var(--line);
      padding-bottom: 14px;
      margin-bottom: 16px;
    }
    .title-block h2 {
      margin: 0 0 8px;
      font-size: 22px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    .description {
      color: var(--muted);
      margin: 0;
      max-width: 880px;
      line-height: 1.45;
    }
    .save-state {
      min-width: 170px;
      text-align: right;
      color: var(--muted);
      font-size: 13px;
    }
    .metrics {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(330px, 0.7fr);
      gap: 18px;
      align-items: start;
    }
    .dream-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 18px;
    }
    .dream-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }
    .dream-title {
      font-size: 16px;
      font-weight: 800;
    }
    .dream-controls {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .dream-layout {
      display: grid;
      grid-template-columns: minmax(260px, 0.62fr) minmax(320px, 1fr);
      gap: 14px;
      align-items: start;
    }
    .dream-canvas-stage {
      width: 100%;
      height: min(54vh, 560px);
      min-height: 360px;
      background: #151a1d;
      overflow: hidden;
      margin-bottom: 14px;
    }
    #dreamCanvas {
      display: block;
      width: 100%;
      height: 100%;
      touch-action: none;
      cursor: grab;
    }
    #dreamCanvas.dragging {
      cursor: grabbing;
    }
    .dream-map {
      display: grid;
      gap: 2px;
      padding: 2px;
      background: #a7a397;
      border: 1px solid #8f8b81;
      max-width: 430px;
    }
    .dream-cell {
      aspect-ratio: 1 / 1;
      display: grid;
      place-items: center;
      min-width: 0;
      min-height: 38px;
      font-weight: 900;
      font-size: 14px;
      border: 1px solid rgba(0, 0, 0, 0.16);
      color: #f8f7f2;
      background: #24282a;
    }
    .dream-cell.wall {
      background: #f0efe8;
      color: #202426;
    }
    .dream-cell.goal {
      background: #2454a6;
    }
    .dream-cell.hazard {
      background: #a82f26;
    }
    .dream-cell.agent {
      background: #12955d;
    }
    .dream-cell.open {
      background: #24282a;
    }
    .dream-rays {
      display: grid;
      gap: 7px;
    }
    .dream-chrono {
      display: grid;
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: var(--panel-soft);
      margin-bottom: 8px;
    }
    .chrono-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .potential-vector {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .potential-list {
      display: grid;
      gap: 6px;
      max-height: 230px;
      overflow: auto;
      padding-right: 2px;
    }
    .potential-row {
      display: grid;
      grid-template-columns: minmax(135px, 0.8fr) minmax(0, 1.2fr) 68px;
      gap: 8px;
      align-items: start;
      border-top: 1px solid var(--line);
      padding-top: 6px;
      font-size: 12px;
    }
    .nemo-review-block {
      display: grid;
      gap: 8px;
      border-top: 1px solid var(--line);
      padding-top: 8px;
      font-size: 12px;
    }
    .nemo-review-head {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .nemo-review-grid {
      display: grid;
      grid-template-columns: minmax(150px, 0.45fr) minmax(0, 1fr);
      gap: 8px;
      align-items: start;
    }
    .nemo-promote-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 0;
    }
    .nemo-review-notes {
      min-height: 58px;
    }
    .network-beneficial {
      color: #0c6f45;
      border-color: rgba(12, 111, 69, 0.45);
    }
    .network-adversarial {
      color: var(--bad);
      border-color: rgba(179, 38, 30, 0.45);
    }
    .network-structural {
      color: #4e5f65;
      border-color: rgba(78, 95, 101, 0.42);
    }
    .network-neutral {
      color: #6d5d17;
      border-color: rgba(109, 93, 23, 0.42);
    }
    .ray-row {
      display: grid;
      grid-template-columns: 96px minmax(0, 1fr) 118px;
      gap: 8px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 7px;
      font-size: 13px;
    }
    .ray-row:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }
    .ray-contact {
      font-weight: 800;
      overflow-wrap: anywhere;
    }
    .ray-path {
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    .grid-panels {
      display: grid;
      grid-template-columns: repeat(2, minmax(260px, 1fr));
      gap: 12px;
    }
    .grid-panel,
    .form-panel,
    .facts-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .grid-panel {
      padding: 12px;
    }
    .grid-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      margin-bottom: 10px;
      font-weight: 700;
      font-size: 14px;
    }
    .grid-wrap {
      width: 100%;
      max-width: 360px;
      aspect-ratio: 1.25 / 1;
      display: grid;
      align-items: center;
      justify-items: center;
      margin: 0 auto 10px;
    }
    .grid {
      display: grid;
      width: 100%;
      max-width: 340px;
      border: 1px solid #a7a397;
      background: #c8c5ba;
      gap: 2px;
      padding: 2px;
    }
    .cell {
      aspect-ratio: 1 / 1;
      min-width: 0;
      display: grid;
      place-items: center;
      border: 1px solid rgba(0, 0, 0, 0.12);
      color: #f8f7f2;
      font-size: 12px;
      font-weight: 800;
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);
      position: relative;
    }
    .cell.wall {
      color: #202426;
      text-shadow: none;
    }
    .cell.changed::after {
      content: "";
      position: absolute;
      inset: 2px;
      border: 2px solid var(--focus);
      pointer-events: none;
    }
    .cell.mismatch::before {
      content: "";
      position: absolute;
      inset: 1px;
      border: 2px solid var(--bad);
      pointer-events: none;
    }
    textarea,
    select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px;
    }
    textarea {
      min-height: 70px;
      resize: vertical;
      line-height: 1.35;
    }
    .image-note {
      min-height: 58px;
    }
    .right-rail {
      display: grid;
      gap: 12px;
    }
    .facts-panel,
    .form-panel {
      padding: 14px;
    }
    .facts-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .fact {
      border-bottom: 1px solid var(--line);
      padding-bottom: 8px;
      min-height: 48px;
    }
    .fact-label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 3px;
    }
    .fact-value {
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }
    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    label span {
      color: var(--muted);
    }
    .check-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin: 8px 0 12px;
    }
    .check {
      display: flex;
      gap: 7px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      min-height: 36px;
      padding: 7px;
      background: var(--panel-soft);
      color: var(--ink);
      font-size: 12px;
      font-weight: 600;
    }
    .check input {
      margin: 0;
      flex: 0 0 auto;
    }
    .actions {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      margin-top: 12px;
    }
    .primary {
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      min-height: 38px;
      padding: 8px 14px;
      cursor: pointer;
      font-weight: 800;
    }
    .secondary {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel-soft);
      color: var(--ink);
      min-height: 38px;
      padding: 8px 14px;
      cursor: pointer;
      font-weight: 700;
    }
    .empty {
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      min-height: 130px;
      display: grid;
      place-items: center;
      padding: 18px;
    }
    @media (max-width: 1050px) {
      .app {
        grid-template-columns: 1fr;
      }
      .sidebar,
      .main {
        max-height: none;
      }
      .sidebar {
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .case-list {
        grid-template-columns: repeat(auto-fit, minmax(235px, 1fr));
      }
      .workspace {
        grid-template-columns: 1fr;
      }
      .dream-layout {
        grid-template-columns: 1fr;
      }
    }
    @media (max-width: 700px) {
      .main {
        padding: 14px;
      }
      .topline {
        display: grid;
      }
      .save-state {
        text-align: left;
      }
      .grid-panels,
      .form-grid,
      .facts-grid,
      .check-grid,
      .chrono-grid,
      .nemo-review-grid,
      .potential-row,
      .ray-row {
        grid-template-columns: 1fr;
      }
      .dream-head {
        display: grid;
      }
      .dream-controls {
        justify-content: flex-start;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h1>Human Eval</h1>
        <div id="progress" class="progress"></div>
      </div>
      <div id="caseList" class="case-list"></div>
    </aside>
    <main class="main">
      <div id="detail"></div>
    </main>
  </div>
  <script type="module">
    import * as THREE from "/vendor/three/three.module.min.js";

    const gridKeys = ["predicted_grid", "truth_grid", "predicted_after_grid", "actual_after_grid"];
    const gridTitles = {
      predicted_grid: "Predicted Start",
      truth_grid: "Truth Start",
      predicted_after_grid: "Predicted After",
      actual_after_grid: "Actual After"
    };
    const failureModes = [
      ["visual.map", "visual map"],
      ["visual.geometry_projection", "geometry"],
      ["temporal.transition", "temporal"],
      ["outcome.polarity", "polarity"],
      ["outcome.magnitude", "magnitude"],
      ["prompt_mismatch", "prompt"],
      ["other", "other"]
    ];
    let session = null;
    let selectedId = null;
    let labels = {};
    let nemoConfirmations = {};
    let nemoReviews = {reviews: {}, promoted_evidence: {}};
    let nemoRelayBusy = false;
    let dreamFrameIndex = 0;
    const dreamThree = {
      renderer: null,
      scene: null,
      camera: null,
      animation: null,
      yaw: -0.72,
      height: 5.6,
      dragging: false,
      lastX: 0,
      lastY: 0
    };

    async function boot() {
      const response = await fetch("/api/session");
      session = await response.json();
      labels = session.labels || {};
      nemoConfirmations = session.nemo_confirmations?.confirmations || {};
      nemoReviews = session.nemo_reviews || {reviews: {}, promoted_evidence: {}};
      selectedId = (session.records[0] || {}).state_id || null;
      render();
    }

    function render() {
      renderSidebar();
      renderDetail();
    }

    function sortedRecords() {
      return [...session.records].sort((left, right) => {
        const leftRank = labels[left.state_id]?.rank ?? 99;
        const rightRank = labels[right.state_id]?.rank ?? 99;
        if (leftRank !== rightRank) return leftRank - rightRank;
        return session.records.indexOf(left) - session.records.indexOf(right);
      });
    }

    function renderSidebar() {
      const list = document.getElementById("caseList");
      const reviewed = session.records.filter((record) => labels[record.state_id]?.human_label).length;
      document.getElementById("progress").textContent = `${reviewed}/${session.records.length}`;
      list.innerHTML = sortedRecords().map((record) => {
        const label = labels[record.state_id] || {};
        const trusted = record.confirmation?.trusted;
        const className = record.state_id === selectedId ? "case-button active" : "case-button";
        return `<button class="${className}" data-case="${escapeHtml(record.state_id)}">
          <span class="case-id">${escapeHtml(record.state_id)}</span>
          <span class="case-meta">
            ${chip(label.human_label || "open", label.human_label ? "good" : "warn")}
            ${chip(label.rank ? `rank ${label.rank}` : "unranked", "")}
            ${chip(trusted ? "trusted" : "blocked", trusted ? "good" : "bad")}
          </span>
        </button>`;
      }).join("");
      list.querySelectorAll("button[data-case]").forEach((button) => {
        button.addEventListener("click", () => {
          selectedId = button.dataset.case;
          render();
        });
      });
    }

    function renderDetail() {
      const record = session.records.find((row) => row.state_id === selectedId);
      const root = document.getElementById("detail");
      if (!record) {
        root.innerHTML = `<div class="empty">No records found.</div>`;
        disposeDreamThree();
        return;
      }
      const label = labels[record.state_id] || {};
      root.innerHTML = `
        <section class="topline">
          <div class="title-block">
            <h2>${escapeHtml(record.state_id)}</h2>
            <p class="description">${escapeHtml(record.case_description || "")}</p>
          </div>
          <div id="saveState" class="save-state">${escapeHtml(label.reviewed_at || "")}</div>
        </section>
        <section class="metrics">${metrics(record)}</section>
        ${dreamPanel()}
        <section class="workspace">
          <div class="grid-panels">${gridPanels(record, label)}</div>
          <div class="right-rail">
            ${factsPanel(record)}
            ${formPanel(record, label)}
          </div>
        </section>
      `;
      bindDreamControls();
      bindForm(record);
      drawDreamThree(session.dream_sequence, (session.dream_sequence?.frames || [])[dreamFrameIndex]);
    }

    function metrics(record) {
      const visual = record.senses?.visual?.map;
      const geometry = record.senses?.visual?.geometry_projection;
      const temporal = record.senses?.temporal;
      const outcome = record.outcome_imagination;
      return [
        chip(`action ${record.action || ""}`, ""),
        chip(`visual ${fmtPct(visual?.cell_accuracy)}`, visual?.trusted ? "good" : "bad"),
        chip(`geometry ${fmtPct(geometry?.label_projection_accuracy)}`, geometry?.trusted ? "good" : "bad"),
        chip(`temporal ${fmtPct(temporal?.transition_cell_accuracy)}`, temporal?.trusted ? "good" : "bad"),
        chip(`outcome ${outcome?.trusted ? "match" : "miss"}`, outcome?.trusted ? "good" : "bad")
      ].join("");
    }

    function gridPanels(record, label) {
      const assets = record.review_assets || {};
      if (!assets.predicted_grid) {
        return `<div class="empty">No grid assets found for this record.</div>`;
      }
      return gridKeys.map((key) => {
        const note = label.image_notes?.[key] || "";
        const compareKey = key === "predicted_grid" ? "truth_grid" : key === "predicted_after_grid" ? "actual_after_grid" : null;
        const baseKey = key.endsWith("_after_grid") ? "truth_grid" : null;
        return `<article class="grid-panel">
          <div class="grid-title">
            <span>${gridTitles[key]}</span>
            ${compareKey ? chip("checked", "") : ""}
          </div>
          <div class="grid-wrap">${renderGrid(assets[key], compareKey ? assets[compareKey] : null, baseKey ? assets[baseKey] : null)}</div>
          <textarea class="image-note" data-image-note="${key}" placeholder="${gridTitles[key]} thoughts">${escapeHtml(note)}</textarea>
        </article>`;
      }).join("");
    }

    function renderGrid(grid, compareGrid, baseGrid) {
      if (!Array.isArray(grid) || !Array.isArray(grid[0])) return `<div class="empty">Missing grid.</div>`;
      const width = grid[0].length;
      const cells = [];
      for (let y = 0; y < grid.length; y += 1) {
        for (let x = 0; x < width; x += 1) {
          const value = Number(grid[y][x]);
          const compare = compareGrid && compareGrid[y] ? Number(compareGrid[y][x]) : value;
          const base = baseGrid && baseGrid[y] ? Number(baseGrid[y][x]) : value;
          const mismatch = value !== compare ? " mismatch" : "";
          const changed = value !== base ? " changed" : "";
          const wall = labelName(value).includes("wall") ? " wall" : "";
          cells.push(`<div class="cell${mismatch}${changed}${wall}" style="background:${labelColor(value)}" title="x ${x}, y ${y}, ${escapeHtml(labelName(value))}">${cellText(value)}</div>`);
        }
      }
      return `<div class="grid" style="grid-template-columns: repeat(${width}, minmax(0, 1fr));">${cells.join("")}</div>`;
    }

    function factsPanel(record) {
      const outcome = record.outcome_imagination || {};
      const temporal = record.senses?.temporal || {};
      const visual = record.senses?.visual?.map || {};
      const failed = [...(record.confirmation?.failed_senses || []), ...(record.confirmation?.failed_outcome || []).map((item) => `outcome.${item}`)];
      return `<section class="facts-panel">
        <div class="facts-grid">
          ${fact("prompt", record.human_eval?.prompt || "")}
          ${fact("failed", failed.length ? failed.join(", ") : "none")}
          ${fact("imagined", signed(outcome.imagined))}
          ${fact("observed", signed(outcome.observed))}
          ${fact("change recall", fmtPct(temporal.change_recall))}
          ${fact("ray exact", fmtPct(visual.ray?.ray_exact_accuracy))}
        </div>
      </section>`;
    }

    function dreamPanel() {
      const sequence = session.dream_sequence;
      const frames = sequence?.frames || [];
      if (!frames.length) {
        return `<section class="dream-panel">
          <div class="dream-head">
            <div class="dream-title">Dream Kernel</div>
            ${chip("no sequence artifact", "warn")}
          </div>
          <div class="empty">No dream_sequence.json found in this experiment.</div>
        </section>`;
      }
      if (dreamFrameIndex >= frames.length) dreamFrameIndex = frames.length - 1;
      if (dreamFrameIndex < 0) dreamFrameIndex = 0;
      const frame = frames[dreamFrameIndex];
      const outcome = frame.outcome;
      const chrono = frame.chronometric || {};
      const integrity = sequence.integrity || {};
      return `<section class="dream-panel">
        <div class="dream-head">
          <div>
            <div class="dream-title">Dream Kernel</div>
            <div class="description">internal known-map rollout frame ${dreamFrameIndex + 1} of ${frames.length} / ${escapeHtml(sequence.schema || "unknown schema")}</div>
          </div>
          <div class="dream-controls">
            ${chip(`tick ${frame.tick}`, "")}
            ${chip(integrity.invariant_passed === false ? "integrity fail" : "integrity pass", integrity.invariant_passed === false ? "bad" : "good")}
            ${chip(`objects ${(sequence.object_registry || []).length}`, "")}
            ${chip(`branches ${(sequence.branch_matrix || []).length}`, "")}
            ${chip(`potentials ${(sequence.branch_potentials || []).length}`, "")}
            ${chip(`links ${(sequence.object_link_hypotheses || []).length}`, "")}
            ${chip(`nemo q ${((sequence.nemo_relay || {}).open_questions || []).length}`, "")}
            ${chip(`reviews ${Object.keys(nemoReviews.reviews || {}).length}`, Object.keys(nemoReviews.promoted_evidence || {}).length ? "good" : "")}
            ${outcome ? chip(outcome.accepted ? "accepted" : "rejected", outcome.accepted ? "good" : "bad") : chip("initial state", "")}
            ${outcome?.terminal ? chip("terminal", "warn") : ""}
            <button class="secondary" id="dreamPrev" type="button">Prev</button>
            <button class="secondary" id="dreamNext" type="button">Next</button>
          </div>
        </div>
        <div class="dream-canvas-stage">
          <canvas id="dreamCanvas"></canvas>
        </div>
        <div class="dream-layout">
          <div>
            ${renderDreamGrid(frame.render_top_down || [])}
          </div>
          <div class="dream-rays">
            ${fact("outcome", outcome ? `${outcome.reason}; reward ${outcome.reward}` : "pre-action state")}
            ${renderSequenceIntegrity(sequence)}
            ${renderNemoRelay(sequence, frame)}
            ${renderBranchMatrix(sequence, frame)}
            ${renderChronometric(chrono)}
            ${renderDreamRays(frame.rays || [])}
          </div>
        </div>
      </section>`;
    }

    function bindDreamControls() {
      const prev = document.getElementById("dreamPrev");
      const next = document.getElementById("dreamNext");
      if (prev && next) {
        prev.addEventListener("click", () => {
          dreamFrameIndex = Math.max(0, dreamFrameIndex - 1);
          renderDetail();
        });
        next.addEventListener("click", () => {
          const frames = session.dream_sequence?.frames || [];
          dreamFrameIndex = Math.min(Math.max(frames.length - 1, 0), dreamFrameIndex + 1);
          renderDetail();
        });
      }
      document.querySelectorAll("button[data-nemo-branch]").forEach((button) => {
        button.addEventListener("click", () => runNemoRelay(button.dataset.nemoBranch));
      });
      document.querySelectorAll("button[data-nemo-review-branch]").forEach((button) => {
        button.addEventListener("click", () => saveNemoReview(button.dataset.nemoReviewBranch));
      });
    }

    function renderDreamGrid(rows) {
      if (!Array.isArray(rows) || !rows.length) return `<div class="empty">Missing Dream Kernel render.</div>`;
      const width = Math.max(...rows.map((row) => String(row).length));
      const cells = [];
      rows.forEach((row, y) => {
        [...String(row)].forEach((ch, x) => {
          cells.push(`<div class="dream-cell ${dreamCellClass(ch)}" title="x ${x}, y ${y}">${escapeHtml(ch === "." ? "" : ch)}</div>`);
        });
      });
      return `<div class="dream-map" style="grid-template-columns: repeat(${width}, minmax(0, 1fr));">${cells.join("")}</div>`;
    }

    function dreamCellClass(ch) {
      if (ch === "#") return "wall";
      if (ch === "G") return "goal";
      if (ch === "H") return "hazard";
      if (ch === "A") return "agent";
      return "open";
    }

    function renderChronometric(chrono) {
      if (!chrono || !Array.isArray(chrono.potential_family_names)) {
        return `<div class="dream-chrono"><div class="empty">No chronometric overlay data in this frame.</div></div>`;
      }
      const names = chrono.potential_family_names || [];
      const vector = chrono.potential_family_vector || [];
      const datapoints = chrono.potential_datapoints || [];
      const calibration = chrono.outcome_calibration || {};
      return `<div class="dream-chrono">
        <div class="chrono-grid">
          ${fact("event_mu", vectorText(chrono.event_mu))}
          ${fact("branch_direction_n", vectorText(chrono.branch_direction_n))}
          ${fact("phase_theta", formatNumber(chrono.phase_theta))}
          ${fact("signed_outcome_y", formatNumber(chrono.signed_outcome_y))}
          ${fact("imagined_y", formatNumber(calibration.imagined_chrono_y))}
          ${fact("observed_y", calibration.observed_chrono_y === null || calibration.observed_chrono_y === undefined ? "n/a" : formatNumber(calibration.observed_chrono_y))}
          ${fact("cal_error", calibration.calibration_error === null || calibration.calibration_error === undefined ? "n/a" : formatNumber(calibration.calibration_error))}
          ${fact("calibrated_y", formatNumber(calibration.calibrated_chrono_y))}
        </div>
        <div class="potential-vector">
          ${names.map((name, index) => chip(`${shortFamily(name)} ${formatNumber(vector[index] ?? 0)}`, potentialTone(vector[index] ?? 0))).join("")}
        </div>
        <div class="potential-list">
          ${datapoints.map(renderPotentialDatum).join("") || `<div class="empty">No potential datapoints.</div>`}
        </div>
      </div>`;
    }

    function renderSequenceIntegrity(sequence) {
      const integrity = sequence.integrity || {};
      const errors = integrity.invariant_errors || [];
      return `<div class="dream-chrono">
        <div class="potential-vector">
          ${chip(`sequence ${shortHash(integrity.sequence_hash)}`, "")}
          ${chip(integrity.invariant_passed === false ? "invariants failed" : "invariants passed", integrity.invariant_passed === false ? "bad" : "good")}
          ${chip(`frames ${integrity.frame_count ?? (sequence.frames || []).length}`, "")}
        </div>
        ${errors.length ? `<div class="ray-path">${escapeHtml(errors.slice(0, 4).join(" | "))}</div>` : ""}
      </div>`;
    }

    function renderNemoRelay(sequence, frame) {
      const relay = sequence.nemo_relay || {};
      const branchIds = currentBranchIds(sequence, frame);
      if (!branchIds.length && !relay.schema) return "";
      const questions = (relay.open_questions || []).filter((question) => branchIds.includes(question.branch_id));
      const confirmations = branchIds.map((branchId) => nemoConfirmations[branchId]).filter(Boolean);
      const reviewed = branchIds.filter((branchId) => (nemoReviews.reviews || {})[branchId]).length;
      return `<div class="dream-chrono">
        <div class="ray-contact">Nemo Relay</div>
        <div class="potential-vector">
          ${chip(relay.relay_status || "relay unavailable", relay.relay_status === "packet_ready_model_not_called" ? "warn" : "")}
          ${chip(relay.required_model || "no model", "")}
          ${chip(`questions ${questions.length}`, "")}
          ${chip(`confirmed ${confirmations.length}`, confirmations.length ? "good" : "")}
          ${chip(`reviewed ${reviewed}`, reviewed ? "good" : "")}
        </div>
        ${branchIds.map((branchId) => renderNemoBranchReview(branchId, questions)).join("")}
      </div>`;
    }

    function renderNemoBranchReview(branchId, questions) {
      const confirmation = nemoConfirmations[branchId];
      const review = (nemoReviews.reviews || {})[branchId] || {};
      const promoted = (nemoReviews.promoted_evidence || {})[branchId] || {};
      const branchQuestions = questions.filter((question) => question.branch_id === branchId);
      const responseText = confirmation?.response_text || "";
      const promotedFields = ["category_revisions", "relation_candidates", "evidence_needed", "action_recommendation"]
        .filter((field) => promoted[field] !== undefined);
      return `<div class="potential-row">
        <div>
          <div class="ray-contact">${escapeHtml(branchId)}</div>
          <div class="ray-path">${escapeHtml(confirmation?.created_at || "not relayed yet")}</div>
          <div>
            ${confirmation ? chip(confirmation.relay_ok === false ? "relay error" : "relay ok", confirmation.relay_ok === false ? "bad" : "good") : chip("no confirmation", "warn")}
            ${chip(review.review_label || "review open", reviewLabelTone(review.review_label))}
          </div>
        </div>
        <div>
          <div class="ray-path">${escapeHtml(branchQuestions.slice(0, 3).map((question) => question.question_id).join(", ") || "no branch-local questions")}</div>
          <div class="ray-path">${escapeHtml(responseText.slice(0, 360))}</div>
          <div class="ray-path">${promotedFields.length ? `promoted ${escapeHtml(promotedFields.join(", "))}` : "no promoted fields"}</div>
        </div>
        <div>
          <button class="secondary" data-nemo-branch="${escapeHtml(branchId)}" type="button" ${nemoRelayBusy ? "disabled" : ""}>Nemo Relay</button>
        </div>
      </div>
      ${branchReviewControls(branchId, confirmation, review, promoted)}`;
    }

    function branchReviewControls(branchId, confirmation, review, promoted) {
      const flags = review.promotion_flags || {};
      const disabled = confirmation ? "" : "disabled";
      const promotedCount = ["category_revisions", "relation_candidates", "evidence_needed", "action_recommendation"]
        .filter((field) => promoted[field] !== undefined).length;
      return `<div class="nemo-review-block">
        <div class="nemo-review-head">
          <div class="ray-contact">Branch Review</div>
          <div class="potential-vector">
            ${chip(review.review_label || "open", reviewLabelTone(review.review_label))}
            ${chip(`promoted ${promotedCount}`, promotedCount ? "good" : "")}
          </div>
        </div>
        <div class="nemo-review-grid">
          <label><span>Trust Label</span>
            <select data-nemo-review-label="${escapeHtml(branchId)}" ${disabled}>
              ${option("", "", review.review_label)}
              ${option("trust", "trust", review.review_label)}
              ${option("partial", "partial", review.review_label)}
              ${option("reject", "reject", review.review_label)}
              ${option("needs_more", "needs more", review.review_label)}
            </select>
          </label>
          <div class="check-grid nemo-promote-grid">
            ${promotionCheck(branchId, "category_revisions", "categories", flags.category_revisions, disabled)}
            ${promotionCheck(branchId, "relation_candidates", "relations", flags.relation_candidates, disabled)}
            ${promotionCheck(branchId, "evidence_needed", "evidence", flags.evidence_needed, disabled)}
            ${promotionCheck(branchId, "action_recommendation", "action", flags.action_recommendation, disabled)}
          </div>
        </div>
        <label><span>Review Notes</span>
          <textarea class="nemo-review-notes" data-nemo-review-notes="${escapeHtml(branchId)}" ${disabled} placeholder="Nemo branch thoughts">${escapeHtml(review.review_notes || "")}</textarea>
        </label>
        <div class="actions">
          <div class="ray-path" data-nemo-review-status="${escapeHtml(branchId)}"></div>
          <button class="primary" data-nemo-review-branch="${escapeHtml(branchId)}" type="button" ${disabled}>Save Review</button>
        </div>
      </div>`;
    }

    function promotionCheck(branchId, field, text, checked, disabled) {
      return `<label class="check"><input type="checkbox" data-nemo-promote="${escapeHtml(field)}" data-nemo-promote-branch="${escapeHtml(branchId)}" ${checked ? "checked" : ""} ${disabled}>${escapeHtml(text)}</label>`;
    }

    function renderBranchMatrix(sequence, frame) {
      const branches = sequence.branch_matrix || [];
      if (!Array.isArray(branches) || !branches.length) return "";
      const rows = branches.filter((branch) => Number(branch.end_tick) === Number(frame.tick));
      if (!rows.length) return "";
      return `<div class="dream-chrono">
        <div class="ray-contact">Branch Matrix</div>
        <div class="potential-list">
          ${rows.map((branch) => `<div class="potential-row">
            <div>
              <div class="ray-contact">${escapeHtml(branch.branch_id || "branch")}</div>
              <div class="ray-path">${escapeHtml(branch.action_id || "")}</div>
            </div>
            <div>
              <div class="ray-path">support ${escapeHtml((branch.supporting_objects || []).join(", ") || "none")}</div>
              <div class="ray-path">risk ${escapeHtml((branch.risk_objects || []).join(", ") || "none")}</div>
              <div class="ray-path">frame ${escapeHtml(shortHash(branch.frame_hash))}</div>
            </div>
            <div>
              ${chip(`net ${formatNumber(branch.chrono_y_net)}`, potentialTone(branch.chrono_y_net))}
              ${chip(`min ${formatNumber(branch.chrono_y_min)}`, potentialTone(branch.chrono_y_min))}
            </div>
          </div>`).join("")}
        </div>
        ${renderBranchPotentials(sequence, rows.map((branch) => branch.branch_id))}
        ${renderObjectLinks(sequence, rows.map((branch) => branch.branch_id))}
      </div>`;
    }

    function renderBranchPotentials(sequence, branchIds) {
      const potentials = (sequence.branch_potentials || []).filter((row) => branchIds.includes(row.branch_id));
      if (!potentials.length) return "";
      return `<div class="potential-list">
        <div class="ray-contact">Branch Potentials</div>
        ${potentials.slice(0, 18).map((potential) => `<div class="potential-row">
          <div>
            <div class="ray-contact">${escapeHtml(potential.object_id || "unknown")}</div>
            <div class="ray-path">${escapeHtml(potential.category_id || "object.unknown.open")}</div>
          </div>
          <div>
            <div class="ray-path">${escapeHtml((potential.hypothesis || "").slice(0, 180))}</div>
            <div class="ray-path">links ${escapeHtml((potential.relation_candidate_ids || []).slice(0, 4).join(", ") || "none")}</div>
          </div>
          <div>
            ${chip(`p ${formatNumber(potential.outcome_probability)}`, potentialTone(potential.chrono_y_correlation))}
            ${chip(`corr ${formatNumber(potential.chrono_y_correlation)}`, potentialTone(potential.chrono_y_correlation))}
          </div>
        </div>`).join("")}
      </div>`;
    }

    function renderObjectLinks(sequence, branchIds) {
      const links = (sequence.object_link_hypotheses || []).filter((row) => branchIds.includes(row.branch_id));
      if (!links.length) return "";
      return `<div class="potential-list">
        <div class="ray-contact">Object Link Hypotheses</div>
        ${links.slice(0, 16).map((link) => `<div class="potential-row">
          <div>
            <div class="ray-contact">${escapeHtml(link.link_id || "link")}</div>
            <div class="ray-path">${escapeHtml(link.relation_kind || "open_relation")}</div>
          </div>
          <div>
            <div class="ray-path">${escapeHtml(link.source_object_id || "unknown")} -> ${escapeHtml(link.target_object_id || "unknown")}</div>
            <div class="ray-path">${escapeHtml((link.unresolved_questions || []).join(" "))}</div>
          </div>
          <div>
            ${chip(`p ${formatNumber(link.probability)}`, potentialTone(link.chrono_y_correlation))}
            ${chip(`corr ${formatNumber(link.chrono_y_correlation)}`, potentialTone(link.chrono_y_correlation))}
          </div>
        </div>`).join("")}
      </div>`;
    }

    function renderPotentialDatum(datum) {
      const network = datum.network || "neutral";
      const mapCoord = datum.map_coord || datum.position;
      const provenance = datum.provenance || {};
      return `<div class="potential-row">
        <div>
          <div class="ray-contact">${escapeHtml(shortFamily(datum.family || ""))}</div>
          <div class="ray-path">${chip(network, networkTone(network))}</div>
        </div>
        <div>
          <div class="ray-contact">${escapeHtml(datum.object_id || "unknown")}</div>
          <div class="ray-path">${escapeHtml(datum.category_id || "object.unknown.open")}</div>
          <div class="ray-path">map ${escapeHtml(coordText(mapCoord))}</div>
          <div class="ray-path">event ${escapeHtml(eventCoordText(datum.event_coord))} / ${escapeHtml(datum.source || "unknown source")}</div>
          <div class="ray-path">${escapeHtml(provenance.evidence || "unknown")} / conf ${escapeHtml(formatNumber(provenance.confidence ?? 0))} / ${escapeHtml(provenance.branch_id || "no branch")}</div>
        </div>
        <div>
          ${chip(`Y ${formatNumber(datum.chrono_y ?? datum.value ?? 0)}`, potentialTone(datum.chrono_y ?? datum.value ?? 0))}
        </div>
      </div>`;
    }

    function renderDreamRays(rays) {
      if (!Array.isArray(rays) || !rays.length) return `<div class="empty">No rays in this frame.</div>`;
      return rays.map((ray) => {
        const direction = coordText(ray.direction);
        const contact = ray.contact || {};
        const objectId = contact.object_id || contact.label || contact.kind || "unknown";
        const path = Array.isArray(ray.path) ? ray.path.map(coordText).join(" -> ") : "";
        const network = ray.network || "neutral";
        return `<div class="ray-row">
          <div>${escapeHtml(direction)}</div>
          <div>
            <div class="ray-contact">${escapeHtml(objectId)} at ${escapeHtml(coordText(contact.position))}</div>
            <div class="ray-path">${escapeHtml(contact.category_id || "object.unknown.open")} / ${escapeHtml(contact.kind || "unknown")} / ${escapeHtml(contact.label || "unlabeled")} / ${escapeHtml(ray.potential_family || "no family")}</div>
            <div class="ray-path">${escapeHtml(path || "no open cells before contact")}</div>
          </div>
          <div>
            ${chip(network, networkTone(network))}
            ${chip(`y ${formatNumber(ray.signed_potential_y ?? 0)}`, potentialTone(ray.signed_potential_y ?? 0))}
            ${chip(`len ${Array.isArray(ray.path) ? ray.path.length : 0}`, "")}
          </div>
        </div>`;
      }).join("");
    }

    function drawDreamThree(sequence, frame) {
      const canvas = document.getElementById("dreamCanvas");
      if (!canvas || !frame) {
        disposeDreamThree();
        return;
      }
      const rows = frame.render_top_down || [];
      if (!rows.length) return;
      initDreamRenderer(canvas);
      const width = Math.max(...rows.map((row) => String(row).length));
      const height = rows.length;
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x151a1d);
      scene.add(new THREE.HemisphereLight(0xf3f0df, 0x151a1d, 1.8));
      const sun = new THREE.DirectionalLight(0xffffff, 2.8);
      sun.position.set(-3, 8, 4);
      scene.add(sun);
      scene.add(new THREE.GridHelper(Math.max(width, height) + 2, Math.max(width, height) + 2, 0x5d665f, 0x343b39));

      const cellMeshes = new THREE.Group();
      rows.forEach((row, y) => {
        [...String(row)].forEach((ch, x) => {
          const mesh = dreamCellMesh(ch);
          if (!mesh) return;
          const pos = gridToWorld({x, y, z: 0}, width, height, 0);
          mesh.position.set(pos.x, mesh.userData.yOffset || 0, pos.z);
          cellMeshes.add(mesh);
        });
      });
      scene.add(cellMeshes);

      const rayGroup = new THREE.Group();
      (frame.rays || []).forEach((ray) => addDreamRay(rayGroup, ray, width, height));
      scene.add(rayGroup);

      const chronoAxisGroup = new THREE.Group();
      addChronoAxisGuide(chronoAxisGroup, width, height);
      scene.add(chronoAxisGroup);

      const potentialGroup = new THREE.Group();
      (frame.chronometric?.potential_datapoints || []).forEach((datum, index) => {
        addPotentialDatum(potentialGroup, datum, width, height, index);
      });
      scene.add(potentialGroup);

      const linkGroup = new THREE.Group();
      addObjectLinkHypotheses(linkGroup, sequence, frame, width, height);
      scene.add(linkGroup);

      const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
      dreamThree.scene = scene;
      dreamThree.camera = camera;
      updateDreamCamera(width, height);
      resizeDreamRenderer();
      animateDreamThree(width, height);
    }

    function initDreamRenderer(canvas) {
      if (dreamThree.renderer && dreamThree.renderer.domElement === canvas) return;
      disposeDreamThree();
      const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      dreamThree.renderer = renderer;
      canvas.addEventListener("pointerdown", (event) => {
        dreamThree.dragging = true;
        dreamThree.lastX = event.clientX;
        dreamThree.lastY = event.clientY;
        canvas.classList.add("dragging");
        canvas.setPointerCapture(event.pointerId);
      });
      canvas.addEventListener("pointermove", (event) => {
        if (!dreamThree.dragging) return;
        const dx = event.clientX - dreamThree.lastX;
        const dy = event.clientY - dreamThree.lastY;
        dreamThree.lastX = event.clientX;
        dreamThree.lastY = event.clientY;
        dreamThree.yaw += dx * 0.008;
        dreamThree.height = Math.max(2.2, Math.min(12, dreamThree.height + dy * 0.025));
      });
      canvas.addEventListener("pointerup", (event) => {
        dreamThree.dragging = false;
        canvas.classList.remove("dragging");
        canvas.releasePointerCapture(event.pointerId);
      });
      window.addEventListener("resize", resizeDreamRenderer);
    }

    function disposeDreamThree() {
      if (dreamThree.animation) cancelAnimationFrame(dreamThree.animation);
      dreamThree.animation = null;
      if (dreamThree.scene) {
        dreamThree.scene.traverse((object) => {
          if (object.geometry) object.geometry.dispose();
          if (object.material) {
            if (Array.isArray(object.material)) {
              object.material.forEach((material) => material.dispose());
            } else {
              object.material.dispose();
            }
          }
        });
      }
      if (dreamThree.renderer) dreamThree.renderer.dispose();
      dreamThree.renderer = null;
      dreamThree.scene = null;
      dreamThree.camera = null;
    }

    function resizeDreamRenderer() {
      const renderer = dreamThree.renderer;
      const camera = dreamThree.camera;
      if (!renderer || !camera) return;
      const canvas = renderer.domElement;
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(1, Math.floor(rect.width));
      const height = Math.max(1, Math.floor(rect.height));
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }

    function animateDreamThree(mapWidth, mapHeight) {
      if (!dreamThree.renderer || !dreamThree.scene || !dreamThree.camera) return;
      if (!dreamThree.dragging) dreamThree.yaw += 0.0025;
      updateDreamCamera(mapWidth, mapHeight);
      dreamThree.renderer.render(dreamThree.scene, dreamThree.camera);
      dreamThree.animation = requestAnimationFrame(() => animateDreamThree(mapWidth, mapHeight));
    }

    function updateDreamCamera(mapWidth, mapHeight) {
      if (!dreamThree.camera) return;
      const radius = Math.max(mapWidth, mapHeight) * 1.55 + 3.5;
      const x = Math.cos(dreamThree.yaw) * radius;
      const z = Math.sin(dreamThree.yaw) * radius;
      dreamThree.camera.position.set(x, dreamThree.height, z);
      dreamThree.camera.lookAt(0, 0.35, 0);
    }

    function dreamCellMesh(ch) {
      const material = new THREE.MeshStandardMaterial({
        color: dreamColor(ch),
        roughness: 0.74,
        metalness: 0.05
      });
      if (ch === "#") {
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(0.96, 1.0, 0.96), material);
        mesh.userData.yOffset = 0.5;
        return mesh;
      }
      if (ch === "A") {
        const group = new THREE.Group();
        const body = new THREE.Mesh(new THREE.SphereGeometry(0.34, 28, 18), material);
        body.position.y = 0.46;
        group.add(body);
        group.userData.yOffset = 0;
        return group;
      }
      if (ch === "G") {
        const mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.82, 28), material);
        mesh.userData.yOffset = 0.41;
        return mesh;
      }
      if (ch === "H") {
        const mesh = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.86, 4), material);
        mesh.rotation.y = Math.PI / 4;
        mesh.userData.yOffset = 0.43;
        return mesh;
      }
      const floor = new THREE.Mesh(
        new THREE.BoxGeometry(0.92, 0.035, 0.92),
        new THREE.MeshStandardMaterial({color: 0x24282a, roughness: 0.9})
      );
      floor.userData.yOffset = -0.017;
      return floor;
    }

    function addDreamRay(group, ray, mapWidth, mapHeight) {
      const points = [ray.origin, ...(ray.path || [])]
        .filter(Boolean)
        .map((coord) => gridToWorld(coord, mapWidth, mapHeight, 1.08));
      const contact = ray.contact || {};
      if (points.length < 2 && contact.position) {
        points.push(gridToWorld(contact.position, mapWidth, mapHeight, 1.08));
      }
      if (points.length >= 2) {
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({color: networkColor(ray.network)});
        group.add(new THREE.Line(geometry, material));
      }
      if (contact.position) {
        const marker = new THREE.Mesh(
          new THREE.SphereGeometry(0.13, 18, 12),
          new THREE.MeshBasicMaterial({color: contactColor(contact.kind, ray.network)})
        );
        marker.name = contact.object_id || contact.label || contact.kind || "ray_contact";
        const pos = gridToWorld(contact.position, mapWidth, mapHeight, 1.16);
        marker.position.set(pos.x, pos.y, pos.z);
        group.add(marker);
      }
    }

    function addPotentialDatum(group, datum, mapWidth, mapHeight, index) {
      const mapCoord = datum?.map_coord || datum?.position;
      if (!datum || !mapCoord) return;
      const eventCoord = datum.event_coord || {
        t: 0,
        x: mapCoord.x,
        y_chrono: datum.chrono_y ?? datum.value ?? 0,
        z: mapCoord.y
      };
      const value = Number(eventCoord.y_chrono ?? datum.chrono_y ?? datum.value ?? 0);
      const magnitude = Math.min(1, Math.abs(value));
      const color = potentialColor(datum.network, value);
      const radius = 0.16 + magnitude * 0.16;
      const anchor = gridToWorld(mapCoord, mapWidth, mapHeight, 0.08);
      const pos = eventCoordToWorld(eventCoord, mapWidth, mapHeight, index);
      const tetherGeometry = new THREE.BufferGeometry().setFromPoints([anchor, pos]);
      group.add(new THREE.Line(
        tetherGeometry,
        new THREE.LineBasicMaterial({color, transparent: true, opacity: 0.68, depthTest: false})
      ));
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(radius, 20, 14),
        new THREE.MeshBasicMaterial({color, transparent: true, opacity: 0.86, depthTest: false})
      );
      sphere.name = datum.object_id || datum.family || "potential_datum";
      sphere.position.set(pos.x, pos.y, pos.z);
      group.add(sphere);
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(radius + 0.08, 0.018, 8, 28),
        new THREE.MeshBasicMaterial({color, transparent: true, opacity: 0.72, depthTest: false})
      );
      ring.rotation.x = Math.PI / 2;
      ring.position.set(pos.x, pos.y + 0.02, pos.z);
      group.add(ring);
    }

    function addObjectLinkHypotheses(group, sequence, frame, mapWidth, mapHeight) {
      const branchIds = currentBranchIds(sequence, frame);
      if (!branchIds.length) return;
      const registry = new Map((sequence?.object_registry || []).map((entry) => [entry.object_id, entry]));
      const links = (sequence?.object_link_hypotheses || []).filter((link) => branchIds.includes(link.branch_id));
      links.slice(0, 28).forEach((link, index) => {
        const source = registry.get(link.source_object_id)?.map_coord;
        const target = registry.get(link.target_object_id)?.map_coord;
        if (!source || !target) return;
        const lift = chronoYToWorld(link.chrono_y_correlation) + 0.12 + (index % 3) * 0.035;
        const start = gridToWorld(source, mapWidth, mapHeight, lift);
        const end = gridToWorld(target, mapWidth, mapHeight, lift);
        const mid = new THREE.Vector3(
          (start.x + end.x) / 2,
          lift + 0.22,
          (start.z + end.z) / 2
        );
        const geometry = new THREE.BufferGeometry().setFromPoints([start, mid, end]);
        group.add(new THREE.Line(
          geometry,
          new THREE.LineBasicMaterial({
            color: potentialColor("neutral", link.chrono_y_correlation),
            transparent: true,
            opacity: 0.58,
            depthTest: false
          })
        ));
      });
    }

    function addChronoAxisGuide(group, mapWidth, mapHeight) {
      const x = (mapWidth - 1) / 2 + 0.95;
      const z = -(mapHeight - 1) / 2;
      const bottom = new THREE.Vector3(x, chronoYToWorld(-1), z);
      const zero = new THREE.Vector3(x, 0, z);
      const top = new THREE.Vector3(x, chronoYToWorld(1), z);
      group.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([bottom, zero]),
        new THREE.LineBasicMaterial({color: 0xff3b30, transparent: true, opacity: 0.74, depthTest: false})
      ));
      group.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([zero, top]),
        new THREE.LineBasicMaterial({color: 0x38d67a, transparent: true, opacity: 0.74, depthTest: false})
      ));
      const zeroMarker = new THREE.Mesh(
        new THREE.SphereGeometry(0.08, 12, 8),
        new THREE.MeshBasicMaterial({color: 0xf0c94f, depthTest: false})
      );
      zeroMarker.position.set(zero.x, zero.y, zero.z);
      group.add(zeroMarker);
    }

    function gridToWorld(coord, mapWidth, mapHeight, yLift) {
      return new THREE.Vector3(
        Number(coord.x) - (mapWidth - 1) / 2,
        Number(coord.z || 0) + yLift,
        Number(coord.y) - (mapHeight - 1) / 2
      );
    }

    function eventCoordToWorld(coord, mapWidth, mapHeight, index) {
      const jitter = ((index % 5) - 2) * 0.035;
      return new THREE.Vector3(
        Number(coord.x) - (mapWidth - 1) / 2 + jitter,
        chronoYToWorld(coord.y_chrono),
        Number(coord.z) - (mapHeight - 1) / 2 - jitter
      );
    }

    function chronoYToWorld(value) {
      return Number(value || 0) * 1.9;
    }

    function dreamColor(ch) {
      if (ch === "#") return 0xe7e4d7;
      if (ch === "G") return 0x2454a6;
      if (ch === "H") return 0xa82f26;
      if (ch === "A") return 0x12955d;
      return 0x24282a;
    }

    function contactColor(kind, network) {
      if (network === "beneficial") return 0x38d67a;
      if (network === "adversarial") return 0xff3b30;
      if (network === "structural") return 0xe5e8dd;
      if (kind === "hazard") return 0xff3b30;
      if (kind === "goal") return 0x4c8dff;
      if (kind === "wall") return 0xffffff;
      if (kind === "entity") return 0x24d07a;
      return 0xf0c94f;
    }

    function networkColor(network) {
      if (network === "beneficial") return 0x38d67a;
      if (network === "adversarial") return 0xff3b30;
      if (network === "structural") return 0xe5e8dd;
      return 0xf0c94f;
    }

    function potentialColor(network, value) {
      if (network === "beneficial" || value > 0.0001) return 0x38d67a;
      if (network === "adversarial" || value < -0.0001) return 0xff3b30;
      if (network === "structural") return 0xe5e8dd;
      return 0xf0c94f;
    }

    function formPanel(record, label) {
      const failures = new Set(label.failure_modes || []);
      return `<section class="form-panel">
        <div class="form-grid">
          <label><span>Human Label</span>
            <select id="humanLabel">
              ${option("", "", label.human_label)}
              ${option("accept", "accept", label.human_label)}
              ${option("reject", "reject", label.human_label)}
              ${option("unsure", "unsure", label.human_label)}
            </select>
          </label>
          <label><span>Rank</span>
            <select id="rank">
              ${option("", "", label.rank)}
              ${option("1", "1 best", label.rank)}
              ${option("2", "2", label.rank)}
              ${option("3", "3", label.rank)}
              ${option("4", "4", label.rank)}
              ${option("5", "5 worst", label.rank)}
            </select>
          </label>
        </div>
        <label><span>Outcome Label</span>
          <select id="outcomeLabel">
            ${option("", "", label.outcome_label)}
            ${option("sensible_positive", "sensible positive", label.outcome_label)}
            ${option("sensible_negative", "sensible negative", label.outcome_label)}
            ${option("visual_map_failure", "visual map failure", label.outcome_label)}
            ${option("temporal_transition_failure", "temporal transition failure", label.outcome_label)}
            ${option("outcome_sign_failure", "outcome sign failure", label.outcome_label)}
            ${option("outcome_magnitude_failure", "outcome magnitude failure", label.outcome_label)}
            ${option("not_enough_info", "not enough info", label.outcome_label)}
          </select>
        </label>
        <div class="check-grid">
          ${failureModes.map(([value, text]) => `<label class="check"><input type="checkbox" value="${value}" ${failures.has(value) ? "checked" : ""}>${text}</label>`).join("")}
        </div>
        <label><span>Notes</span>
          <textarea id="humanNotes" placeholder="Case thoughts">${escapeHtml(label.human_notes || "")}</textarea>
        </label>
        <div class="actions">
          <button class="secondary" id="clearLabel" type="button">Clear</button>
          <button class="primary" id="saveLabel" type="button">Save</button>
        </div>
      </section>`;
    }

    function bindForm(record) {
      document.getElementById("saveLabel").addEventListener("click", () => saveCurrent(record));
      document.getElementById("clearLabel").addEventListener("click", () => {
        document.getElementById("humanLabel").value = "";
        document.getElementById("rank").value = "";
        document.getElementById("outcomeLabel").value = "";
        document.querySelectorAll(".check input").forEach((input) => input.checked = false);
        document.getElementById("humanNotes").value = "";
        document.querySelectorAll("textarea[data-image-note]").forEach((textarea) => textarea.value = "");
      });
    }

    async function saveCurrent(record) {
      const saveState = document.getElementById("saveState");
      saveState.textContent = "saving";
      const imageNotes = {};
      document.querySelectorAll("textarea[data-image-note]").forEach((textarea) => {
        imageNotes[textarea.dataset.imageNote] = textarea.value;
      });
      const failure_modes = [...document.querySelectorAll(".check input:checked")].map((input) => input.value);
      const payload = {
        case_id: record.state_id,
        human_label: document.getElementById("humanLabel").value,
        rank: document.getElementById("rank").value,
        outcome_label: document.getElementById("outcomeLabel").value,
        failure_modes,
        human_notes: document.getElementById("humanNotes").value,
        image_notes: imageNotes
      };
      const response = await fetch("/api/label", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) {
        saveState.textContent = body.error || "save failed";
        return;
      }
      labels = body.labels || {};
      saveState.textContent = body.label.reviewed_at;
      renderSidebar();
    }

    async function runNemoRelay(branchId) {
      if (!branchId || nemoRelayBusy) return;
      nemoRelayBusy = true;
      renderDetail();
      const response = await fetch("/api/nemo-relay", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({branch_id: branchId})
      });
      const body = await response.json();
      nemoRelayBusy = false;
      if (!response.ok) {
        nemoConfirmations[branchId] = {
          branch_id: branchId,
          created_at: new Date().toISOString(),
          response_text: body.error || "Nemo relay failed"
        };
        renderDetail();
        return;
      }
      nemoConfirmations[branchId] = body.confirmation;
      renderDetail();
    }

    async function saveNemoReview(branchId) {
      if (!branchId) return;
      const status = dataElement("data-nemo-review-status", branchId);
      if (status) status.textContent = "saving";
      const label = dataElement("data-nemo-review-label", branchId);
      const notes = dataElement("data-nemo-review-notes", branchId);
      const flags = {};
      document.querySelectorAll("input[data-nemo-promote]").forEach((input) => {
        if (input.getAttribute("data-nemo-promote-branch") === branchId) {
          flags[input.getAttribute("data-nemo-promote")] = input.checked;
        }
      });
      const response = await fetch("/api/nemo-review", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          branch_id: branchId,
          review_label: label?.value || "",
          promotion_flags: flags,
          review_notes: notes?.value || ""
        })
      });
      const body = await response.json();
      if (!response.ok) {
        if (status) status.textContent = body.error || "review save failed";
        return;
      }
      nemoReviews = body.nemo_reviews || nemoReviews;
      renderDetail();
    }

    function dataElement(attribute, value) {
      return [...document.querySelectorAll(`[${attribute}]`)].find((element) => element.getAttribute(attribute) === value);
    }

    function currentBranchIds(sequence, frame) {
      const branches = sequence?.branch_matrix || [];
      return branches
        .filter((branch) => Number(branch.end_tick) === Number(frame?.tick))
        .map((branch) => branch.branch_id)
        .filter(Boolean);
    }

    function labelColor(value) {
      const item = legend().find((entry) => Number(entry.value) === Number(value));
      if (!item || !Array.isArray(item.rgb)) return "#8a8178";
      return `rgb(${item.rgb[0]}, ${item.rgb[1]}, ${item.rgb[2]})`;
    }

    function labelName(value) {
      const item = legend().find((entry) => Number(entry.value) === Number(value));
      return item ? item.name : String(value);
    }

    function cellText(value) {
      const name = labelName(value);
      if (name.includes("objective")) return "G";
      if (name.includes("self")) return "S";
      if (name.includes("object")) return "S";
      if (name.includes("wall")) return "";
      return "";
    }

    function legend() {
      return session.condition?.labels || [];
    }

    function chip(text, tone) {
      return `<span class="pill ${tone || ""}">${escapeHtml(String(text))}</span>`;
    }

    function fact(label, value) {
      return `<div class="fact"><span class="fact-label">${escapeHtml(label)}</span><span class="fact-value">${escapeHtml(String(value))}</span></div>`;
    }

    function option(value, text, current) {
      const selected = String(current ?? "") === String(value) ? "selected" : "";
      return `<option value="${escapeHtml(value)}" ${selected}>${escapeHtml(text)}</option>`;
    }

    function networkTone(network) {
      if (network === "beneficial") return "network-beneficial";
      if (network === "adversarial") return "network-adversarial";
      if (network === "structural") return "network-structural";
      return "network-neutral";
    }

    function reviewLabelTone(label) {
      if (label === "trust") return "good";
      if (label === "reject") return "bad";
      if (label === "partial" || label === "needs_more") return "warn";
      return "";
    }

    function potentialTone(value) {
      const numeric = Number(value || 0);
      if (numeric > 0.0001) return "good";
      if (numeric < -0.0001) return "bad";
      return "";
    }

    function shortFamily(name) {
      const text = String(name || "");
      if (text === "transition.changed_cells") return "changed";
      if (text === "time_phase.repeated_effect_size") return "phase";
      if (text === "goal_progress.level_delta") return "goal";
      if (text === "stasis.no_change") return "stasis";
      if (text === "loop.repeated_action") return "loop";
      if (text === "mirror.progress_path") return "path";
      if (text === "mirror.progress_blocker") return "blocker";
      if (text === "hazard.env_failure") return "hazard";
      return text;
    }

    function vectorText(value) {
      if (!Array.isArray(value)) return "n/a";
      return `[${value.map(formatNumber).join(", ")}]`;
    }

    function formatNumber(value) {
      const numeric = Number(value || 0);
      if (!Number.isFinite(numeric)) return "0.000";
      return numeric.toFixed(3);
    }

    function shortHash(value) {
      const text = String(value || "none");
      return text.length > 12 ? text.slice(0, 12) : text;
    }

    function fmtPct(value) {
      if (value === null || value === undefined) return "n/a";
      return `${Math.round(Number(value) * 100)}%`;
    }

    function signed(outcome) {
      if (!outcome) return "n/a";
      return `${outcome.signed_y} ${outcome.polarity || ""}`.trim();
    }

    function coordText(coord) {
      if (!coord) return "n/a";
      return `(${coord.x}, ${coord.y}, ${coord.z})`;
    }

    function eventCoordText(coord) {
      if (!coord) return "n/a";
      return `(t ${coord.t}, x ${formatNumber(coord.x)}, Y ${formatNumber(coord.y_chrono)}, z ${formatNumber(coord.z)})`;
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char]));
    }

    boot().catch((error) => {
      document.getElementById("detail").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
