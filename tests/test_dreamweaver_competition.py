import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dreamweaver_competition import (  # noqa: E402
    TARGET_KAGGLE_PRIZE,
    TARGET_ONLINE_COMMUNITY,
    config_from_online_scorecard_metrics,
    evaluate_competition_config,
    kaggle_prize_template,
)


def _kaggle_config(**overrides):
    config = {
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
        "implementation_status": "implemented",
    }
    config.update(overrides)
    return config


def test_online_api_scorecard_lane_is_valid_but_not_prize_eligible():
    manifest = evaluate_competition_config(
        {
            "model_name": "Dreamweaver",
            "target_lane": TARGET_ONLINE_COMMUNITY,
            "operation_mode": "ONLINE",
            "internet_allowed": True,
            "confirmation_backend_kind": "openai-compatible",
            "confirmation_backend_url": "https://openrouter.ai/api/v1/responses",
            "confirmation_backend_model": "nemo3-compatible",
            "uses_offline_mirror": True,
            "uses_source_env_solver": True,
            "single_scorecard": True,
            "all_environment_runner": False,
            "one_make_per_environment": False,
            "scorecard_reads_during_run": False,
            "secret_sources": ["ARC_API_KEY"],
            "package_includes_requirements": False,
            "open_source_ready": False,
            "implementation_status": "implemented",
        }
    )

    assert manifest["online_community_valid"] is True
    assert manifest["kaggle_prize_eligible"] is False
    assert manifest["confirmation_backend"]["external_api"] is True
    assert "external confirmation backend is online/community only" in " ".join(manifest["warnings"])


def test_kaggle_config_with_external_api_fails_closed():
    manifest = evaluate_competition_config(
        _kaggle_config(
            internet_allowed=True,
            confirmation_backend_kind="openrouter",
            confirmation_backend_url="https://openrouter.ai/api/v1/responses",
            secret_sources=["ARC_API_KEY"],
        )
    )

    assert manifest["kaggle_prize_eligible"] is False
    failures = " ".join(manifest["failures"])
    assert "cannot require internet access" in failures
    assert "cannot use external/API confirmation backends" in failures
    assert "must not depend on API-key secret sources" in failures


def test_kaggle_config_with_mirror_or_source_solver_fails_closed():
    manifest = evaluate_competition_config(
        _kaggle_config(
            uses_offline_mirror=True,
            uses_source_env_solver=True,
        )
    )

    assert manifest["kaggle_prize_eligible"] is False
    failures = " ".join(manifest["failures"])
    assert "cannot depend on an offline mirror" in failures
    assert "cannot depend on source-env/game-specific solver internals" in failures


def test_minimal_no_internet_local_all_env_config_passes_gate():
    manifest = evaluate_competition_config(_kaggle_config())

    assert manifest["kaggle_prize_eligible"] is True
    assert manifest["failures"] == []
    assert manifest["confirmation_backend"]["local_or_bundled"] is True


def test_kaggle_template_is_not_accidentally_marked_implemented():
    manifest = evaluate_competition_config(kaggle_prize_template())

    assert manifest["kaggle_prize_eligible"] is False
    assert "template or planned-only config" in " ".join(manifest["failures"])


def test_scorecard_metrics_config_keeps_online_proof_non_prize(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "scorecard_id": "scorecard-001",
                "official_arc_solve_claim": False,
                "condition": {
                    "model_name": "Dreamweaver",
                    "operation_mode": "ONLINE",
                    "mirror_operation_mode": "OFFLINE",
                    "nemo_mode": "live-relay",
                    "nemo_relay_url": "http://127.0.0.1:8000/v1/responses",
                    "nemo_model": "nemotron_3_nano_omni",
                    "compile_kernel_policy": "mandatory_dream_kernel_ls20_simulation_review_before_online_action",
                    "scorecard_id": "scorecard-001",
                    "arc_api_key_source": "arc_env_file",
                    "selected_game": {"name": "ls20"},
                },
            }
        ),
        encoding="utf-8",
    )

    config = config_from_online_scorecard_metrics(metrics_path)
    manifest = evaluate_competition_config(config)

    assert config["target_lane"] == TARGET_ONLINE_COMMUNITY
    assert manifest["online_community_valid"] is True
    assert manifest["kaggle_prize_eligible"] is False
    assert manifest["scorecard_proof"]["scorecard_id"] == "scorecard-001"
    assert manifest["uses_source_env_solver"] is True


def test_manifest_cli_writes_online_scorecard_manifest(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    out_path = tmp_path / "manifest.json"
    metrics_path.write_text(
        json.dumps(
            {
                "scorecard_id": "scorecard-001",
                "condition": {
                    "operation_mode": "ONLINE",
                    "mirror_operation_mode": "OFFLINE",
                    "nemo_mode": "live-relay",
                    "scorecard_id": "scorecard-001",
                    "arc_api_key_source": "arc_env_file",
                },
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_dreamweaver_competition_manifest.py"),
            "--from-online-scorecard-metrics",
            str(metrics_path),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    manifest = json.loads(out_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "dreamweaver.arc_agi3_competition_preflight.v001"
    assert manifest["target_lane"] == TARGET_ONLINE_COMMUNITY
    assert manifest["kaggle_prize_eligible"] is False
