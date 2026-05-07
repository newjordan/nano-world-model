"""Dreamweaver ARC-AGI-3 competition-lane preflight.

This module is intentionally small and fail-closed. It does not make a run
legal by itself; it records whether a proposed Dreamweaver harness config meets
the current ARC-AGI-3 lane constraints we care about before packaging or
submission.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "dreamweaver.arc_agi3_competition_preflight.v001"
TARGET_ONLINE_COMMUNITY = "online_community"
TARGET_KAGGLE_PRIZE = "kaggle_prize"
ALLOWED_TARGET_LANES = {TARGET_ONLINE_COMMUNITY, TARGET_KAGGLE_PRIZE}

EXTERNAL_CONFIRMATION_BACKENDS = {
    "external-api",
    "live-relay",
    "nemo-api",
    "nvidia-api",
    "openai-compatible",
    "openrouter",
}
LOCAL_CONFIRMATION_BACKENDS = {
    "bundled-local-model",
    "contract-local",
    "deterministic",
    "local",
    "local-nemo",
}
NO_INTERNET_OPERATION_MODES = {"COMPETITION"}

REQUIRED_FIELDS = (
    "target_lane",
    "operation_mode",
    "internet_allowed",
    "confirmation_backend_kind",
    "uses_offline_mirror",
    "uses_source_env_solver",
    "single_scorecard",
    "all_environment_runner",
    "one_make_per_environment",
    "scorecard_reads_during_run",
    "secret_sources",
    "package_includes_requirements",
    "open_source_ready",
)


def evaluate_competition_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return a redacted preflight manifest for a Dreamweaver submission config."""

    cfg = dict(config)
    failures: list[str] = []
    warnings: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if field not in cfg]
    for field in missing:
        failures.append(f"missing required field: {field}")

    target_lane = str(cfg.get("target_lane", "")).strip()
    operation_mode = str(cfg.get("operation_mode", "")).strip().upper()
    backend_kind = str(cfg.get("confirmation_backend_kind", "")).strip().lower()
    backend_url = str(cfg.get("confirmation_backend_url", "") or "").strip()
    internet_allowed = _bool(cfg.get("internet_allowed"))
    uses_offline_mirror = _bool(cfg.get("uses_offline_mirror"))
    uses_source_env_solver = _bool(cfg.get("uses_source_env_solver"))
    single_scorecard = _bool(cfg.get("single_scorecard"))
    all_environment_runner = _bool(cfg.get("all_environment_runner"))
    one_make_per_environment = _bool(cfg.get("one_make_per_environment"))
    scorecard_reads_during_run = _bool(cfg.get("scorecard_reads_during_run"))
    package_includes_requirements = _bool(cfg.get("package_includes_requirements"))
    open_source_ready = _bool(cfg.get("open_source_ready"))
    implementation_status = str(cfg.get("implementation_status", "implemented")).strip().lower()

    if target_lane and target_lane not in ALLOWED_TARGET_LANES:
        failures.append(f"target_lane must be one of {sorted(ALLOWED_TARGET_LANES)}")
    if not operation_mode:
        failures.append("operation_mode is required")
    if not backend_kind:
        failures.append("confirmation_backend_kind is required")

    external_backend = backend_kind in EXTERNAL_CONFIRMATION_BACKENDS or _looks_external_backend_url(backend_url)
    local_backend = backend_kind in LOCAL_CONFIRMATION_BACKENDS and not external_backend
    secret_sources = _string_list(cfg.get("secret_sources"))
    api_secret_sources = [item for item in secret_sources if "api" in item.lower() or "key" in item.lower()]

    if target_lane == TARGET_KAGGLE_PRIZE:
        if operation_mode not in NO_INTERNET_OPERATION_MODES:
            failures.append("Kaggle prize lane requires operation_mode=COMPETITION")
        if internet_allowed:
            failures.append("Kaggle prize lane cannot require internet access")
        if external_backend:
            failures.append("Kaggle prize lane cannot use external/API confirmation backends")
        if not local_backend:
            failures.append("Kaggle prize lane requires a local, bundled, or deterministic confirmation backend")
        if uses_offline_mirror:
            failures.append("Kaggle prize lane cannot depend on an offline mirror/source environment")
        if uses_source_env_solver:
            failures.append("Kaggle prize lane cannot depend on source-env/game-specific solver internals")
        if not single_scorecard:
            failures.append("Kaggle prize lane must use one scorecard")
        if not all_environment_runner:
            failures.append("Kaggle prize lane must run all available environments")
        if not one_make_per_environment:
            failures.append("Kaggle prize lane must call make at most once per environment")
        if scorecard_reads_during_run:
            failures.append("Kaggle prize lane cannot read inflight scorecard state")
        if api_secret_sources:
            failures.append("Kaggle prize package must not depend on API-key secret sources")
        if not package_includes_requirements:
            failures.append("Kaggle prize package must include reproducible requirements")
        if not open_source_ready:
            failures.append("Kaggle prize eligibility requires open-source-ready code and methods")
        if implementation_status != "implemented":
            failures.append("Kaggle prize lane cannot pass from a template or planned-only config")
    elif target_lane == TARGET_ONLINE_COMMUNITY:
        if operation_mode == "COMPETITION" and internet_allowed:
            warnings.append("COMPETITION mode with internet_allowed=true is not Kaggle-prize compatible")
        if external_backend:
            warnings.append("external confirmation backend is online/community only, not Kaggle prize eligible")
        if uses_offline_mirror:
            warnings.append("offline mirror is development evidence only, not hidden Kaggle evaluation proof")
        if uses_source_env_solver:
            warnings.append("source-env solver use is game-specific proof, not hidden Kaggle generalization")

    if not package_includes_requirements:
        warnings.append("package does not declare reproducible requirements")
    if not open_source_ready:
        warnings.append("code/methods are not marked open-source ready")

    kaggle_prize_eligible = target_lane == TARGET_KAGGLE_PRIZE and not failures
    online_community_valid = target_lane == TARGET_ONLINE_COMMUNITY and not missing
    manifest = {
        "schema": SCHEMA,
        "created_at_utc": _now_iso(),
        "model_name": str(cfg.get("model_name", "Dreamweaver")),
        "target_lane": target_lane,
        "operation_mode": operation_mode,
        "internet_allowed": internet_allowed,
        "confirmation_backend": {
            "kind": backend_kind,
            "url": _redacted_backend_url(backend_url),
            "model": str(cfg.get("confirmation_backend_model", "") or ""),
            "external_api": external_backend,
            "local_or_bundled": local_backend,
        },
        "uses_offline_mirror": uses_offline_mirror,
        "uses_source_env_solver": uses_source_env_solver,
        "single_scorecard": single_scorecard,
        "all_environment_runner": all_environment_runner,
        "one_make_per_environment": one_make_per_environment,
        "scorecard_reads_during_run": scorecard_reads_during_run,
        "secret_sources": [_redact_secret_source(item) for item in secret_sources],
        "package_includes_requirements": package_includes_requirements,
        "open_source_ready": open_source_ready,
        "implementation_status": implementation_status,
        "scorecard_proof": {
            "saved": _bool(cfg.get("scorecard_proof_saved")),
            "path": str(cfg.get("scorecard_proof_path", "") or ""),
            "scorecard_id": str(cfg.get("scorecard_id", "") or ""),
            "operation_mode": str(cfg.get("scorecard_operation_mode", "") or ""),
            "official_arc_solve_claim": _bool(cfg.get("official_arc_solve_claim")),
        },
        "kaggle_prize_eligible": kaggle_prize_eligible,
        "online_community_valid": online_community_valid,
        "failures": failures,
        "warnings": warnings,
    }
    return manifest


def config_from_online_scorecard_metrics(metrics_path: Path) -> dict[str, Any]:
    """Build a preflight config from a saved Dreamweaver ONLINE scorecard metrics file."""

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    condition = metrics.get("condition") if isinstance(metrics.get("condition"), dict) else {}
    loader_settings = condition.get("loader_settings") if isinstance(condition.get("loader_settings"), dict) else {}
    return {
        "model_name": condition.get("model_name", "Dreamweaver"),
        "target_lane": TARGET_ONLINE_COMMUNITY,
        "operation_mode": condition.get("operation_mode", ""),
        "internet_allowed": True,
        "confirmation_backend_kind": condition.get("nemo_mode", ""),
        "confirmation_backend_url": condition.get("nemo_relay_url", ""),
        "confirmation_backend_model": condition.get("nemo_model", ""),
        "uses_offline_mirror": condition.get("mirror_operation_mode") == "OFFLINE",
        "uses_source_env_solver": "ls20" in str(condition.get("compile_kernel_policy", "")).lower(),
        "single_scorecard": bool(condition.get("scorecard_id")),
        "all_environment_runner": False,
        "one_make_per_environment": False,
        "scorecard_reads_during_run": False,
        "secret_sources": [condition.get("arc_api_key_source", "unknown")],
        "package_includes_requirements": False,
        "open_source_ready": False,
        "implementation_status": "implemented",
        "scorecard_proof_saved": True,
        "scorecard_proof_path": str(metrics_path.parent),
        "scorecard_id": metrics.get("scorecard_id", ""),
        "scorecard_operation_mode": condition.get("operation_mode", ""),
        "official_arc_solve_claim": metrics.get("official_arc_solve_claim", False),
        "max_real_steps": condition.get("max_real_steps"),
        "game": (condition.get("selected_game") or {}).get("name") if isinstance(condition.get("selected_game"), dict) else None,
        "save_recording": loader_settings.get("save_recording"),
    }


def kaggle_prize_template() -> dict[str, Any]:
    """Return the required shape for the future no-internet prize package."""

    return {
        "model_name": "Dreamweaver",
        "target_lane": TARGET_KAGGLE_PRIZE,
        "operation_mode": "COMPETITION",
        "internet_allowed": False,
        "confirmation_backend_kind": "deterministic",
        "confirmation_backend_url": "",
        "confirmation_backend_model": "dreamweaver-local-confirmation",
        "uses_offline_mirror": False,
        "uses_source_env_solver": False,
        "single_scorecard": True,
        "all_environment_runner": True,
        "one_make_per_environment": True,
        "scorecard_reads_during_run": False,
        "secret_sources": [],
        "package_includes_requirements": True,
        "open_source_ready": True,
        "implementation_status": "template",
        "scorecard_proof_saved": False,
        "scorecard_proof_path": "",
        "scorecard_id": "",
        "scorecard_operation_mode": "",
        "official_arc_solve_claim": False,
    }


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _looks_external_backend_url(value: str) -> bool:
    if not value:
        return False
    lowered = value.lower()
    if lowered.startswith("http://127.0.0.1") or lowered.startswith("http://localhost"):
        return False
    return lowered.startswith("http://") or lowered.startswith("https://")


def _redacted_backend_url(value: str) -> str:
    if not value:
        return ""
    lowered = value.lower()
    if "api_key=" in lowered or "token=" in lowered or "key=" in lowered:
        return value.split("?", 1)[0] + "?REDACTED"
    return value


def _redact_secret_source(value: str) -> str:
    lowered = value.lower()
    if "arc_api_key" in lowered or "api_key" in lowered:
        return "api_key_source_redacted"
    return value


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
