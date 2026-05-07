#!/usr/bin/env python3
"""Build a Dreamweaver ARC-AGI-3 competition preflight manifest."""

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

from dreamweaver_competition import (  # noqa: E402
    TARGET_KAGGLE_PRIZE,
    TARGET_ONLINE_COMMUNITY,
    config_from_online_scorecard_metrics,
    evaluate_competition_config,
    kaggle_prize_template,
    write_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", type=Path, help="explicit Dreamweaver preflight config JSON")
    source.add_argument(
        "--from-online-scorecard-metrics",
        type=Path,
        help="saved ONLINE metrics.json to classify as the online/community lane",
    )
    source.add_argument(
        "--template",
        choices=[TARGET_KAGGLE_PRIZE, TARGET_ONLINE_COMMUNITY],
        help="emit a template config through the preflight gate",
    )
    parser.add_argument("--out", type=Path, help="manifest output path")
    parser.add_argument(
        "--require-kaggle-eligible",
        action="store_true",
        help="exit non-zero unless the manifest is Kaggle prize eligible",
    )
    args = parser.parse_args()

    if args.config is not None:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    elif args.from_online_scorecard_metrics is not None:
        config = config_from_online_scorecard_metrics(args.from_online_scorecard_metrics)
    elif args.template == TARGET_KAGGLE_PRIZE:
        config = kaggle_prize_template()
    else:
        config = {
            "model_name": "Dreamweaver",
            "target_lane": TARGET_ONLINE_COMMUNITY,
            "operation_mode": "ONLINE",
            "internet_allowed": True,
            "confirmation_backend_kind": "openai-compatible",
            "confirmation_backend_url": "https://example.invalid/v1/responses",
            "confirmation_backend_model": "nemo3-or-compatible",
            "uses_offline_mirror": True,
            "uses_source_env_solver": True,
            "single_scorecard": True,
            "all_environment_runner": False,
            "one_make_per_environment": False,
            "scorecard_reads_during_run": False,
            "secret_sources": ["ARC_API_KEY"],
            "package_includes_requirements": False,
            "open_source_ready": False,
            "implementation_status": "template",
        }

    manifest = evaluate_competition_config(config)
    if args.out is not None:
        write_manifest(args.out, manifest)
    else:
        print(json.dumps(manifest, indent=2, sort_keys=True))

    if args.require_kaggle_eligible and not manifest["kaggle_prize_eligible"]:
        for failure in manifest["failures"]:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
