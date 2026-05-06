import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sensory_smattering_script_writes_human_eval_artifacts(tmp_path):
    out_dir = tmp_path / "smattering"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_chronometric_sensory_smattering.py",
            "--run-label",
            "test_v034_smattering",
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    condition = json.loads((out_dir / "condition.json").read_text(encoding="utf-8"))
    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (out_dir / "sensory_records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    human_eval = (out_dir / "HUMAN_EVAL.md").read_text(encoding="utf-8")

    assert condition["run_type"] == "chronometric_sensory_smattering_v034"
    assert condition["training_data_promoted"] is False
    assert condition["human_eval_required"] is True
    assert metrics["case_count"] == 5
    assert metrics["trusted_count"] == 2
    assert metrics["sensory_trusted_count"] == 3
    assert metrics["outcome_imagination_trusted_count"] == 2
    assert metrics["failed_by_reason"]["temporal.transition"] == 1
    assert metrics["failed_by_reason"]["visual.map"] == 1
    assert metrics["failed_by_reason"]["outcome.outcome_polarity_match"] == 3
    assert len(rows) == 5
    assert rows[0]["review_assets"]["predicted_grid"][1][1] == 2
    assert rows[0]["review_assets"]["truth_grid"][1][3] == 3
    assert rows[0]["review_assets"]["predicted_after_grid"][1][2] == 2
    assert rows[0]["review_assets"]["actual_after_grid"][1][2] == 2
    assert "v034_case_001_direct_positive" in human_eval
    assert "- human_label:" in human_eval
    assert (out_dir / "RESULTS.md").exists()
