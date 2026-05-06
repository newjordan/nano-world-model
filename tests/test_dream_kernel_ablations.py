import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_ablation_module():
    path = ROOT / "scripts" / "run_dream_kernel_ablations.py"
    spec = importlib.util.spec_from_file_location("run_dream_kernel_ablations", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dream_kernel_ablation_runner_writes_condition_metrics_and_rows(tmp_path):
    module = _load_ablation_module()
    sequence_path = tmp_path / "dream_sequence.json"
    confirmations_path = tmp_path / "nemo_relay_confirmations.json"
    reviews_path = tmp_path / "nemo_relay_reviews.json"
    out_dir = tmp_path / "ablations"
    sequence_path.write_text(json.dumps(_sequence(), sort_keys=True) + "\n", encoding="utf-8")
    confirmations_path.write_text(
        json.dumps(
            {
                "schema": "dream_kernel.nemo_relay_confirmations.v001",
                "confirmations": {
                    "tick0.right": {
                        "relay_ok": True,
                        "response_text": json.dumps({"branch_id": "tick0.right", "confidence": 0.8}),
                    },
                    "tick1.wait": {
                        "relay_ok": True,
                        "response_text": json.dumps({"branch_id": "tick1.wait", "confidence": 0.7}),
                    },
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    reviews_path.write_text(
        json.dumps({"schema": "dream_kernel.nemo_relay_reviews.v001", "reviews": {}, "promoted_evidence": {}})
        + "\n",
        encoding="utf-8",
    )

    metrics = module.run(
        argparse.Namespace(
            sequence=sequence_path,
            confirmations=confirmations_path,
            reviews=reviews_path,
            out_dir=out_dir,
            run_label="test_dream_kernel_ablation",
        )
    )

    assert metrics["source_summary"]["branches"] == 2
    assert metrics["source_summary"]["nemo_confirmations"] == 2
    assert metrics["compression_summary"]["high_value_layers"]
    assert (out_dir / "condition.json").exists()
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "ablation_rows.jsonl").exists()
    assert (out_dir / "object_value_rows.jsonl").exists()
    assert "drop_object_links" in (out_dir / "RESULTS.md").read_text(encoding="utf-8")


def _sequence():
    return {
        "schema": "dream_kernel.sequence.v003",
        "integrity": {"sequence_hash": "testhash"},
        "object_registry": [
            {
                "object_id": "agent",
                "category_id": "entity.agent.self",
                "open_tags": ["self_anchor"],
                "map_coord": {"x": 1, "y": 1, "z": 0},
            },
            {
                "object_id": "goal:2:1:0",
                "category_id": "map.terminal.positive",
                "open_tags": ["terminal", "branch_reward_candidate"],
                "map_coord": {"x": 2, "y": 1, "z": 0},
            },
            {
                "object_id": "wall:0:0:0",
                "category_id": "map.structural.wall",
                "open_tags": ["structural", "blocks_motion"],
                "map_coord": {"x": 0, "y": 0, "z": 0},
            },
        ],
        "branch_matrix": [
            {
                "branch_id": "tick0.right",
                "end_tick": 1,
                "chrono_y_net": 0.8,
                "supporting_objects": ["agent", "goal:2:1:0"],
                "risk_objects": [],
            },
            {
                "branch_id": "tick1.wait",
                "end_tick": 2,
                "chrono_y_net": -0.4,
                "supporting_objects": ["agent"],
                "risk_objects": ["wall:0:0:0"],
            },
        ],
        "branch_potentials": [
            {
                "branch_id": "tick0.right",
                "object_id": "goal:2:1:0",
                "chrono_y_correlation": 0.8,
            },
            {
                "branch_id": "tick1.wait",
                "object_id": "wall:0:0:0",
                "chrono_y_correlation": -0.4,
            },
        ],
        "object_link_hypotheses": [
            {
                "branch_id": "tick0.right",
                "source_object_id": "agent",
                "target_object_id": "goal:2:1:0",
                "probability": 0.8,
                "chrono_y_correlation": 0.8,
            },
            {
                "branch_id": "tick1.wait",
                "source_object_id": "agent",
                "target_object_id": "wall:0:0:0",
                "probability": 0.4,
                "chrono_y_correlation": -0.4,
            },
        ],
        "nemo_relay": {
            "open_questions": [
                {"branch_id": "tick0.right", "object_id": "goal:2:1:0"},
                {"branch_id": "tick1.wait", "object_id": "wall:0:0:0"},
            ]
        },
        "frames": [
            {
                "tick": 1,
                "rays": [
                    {
                        "signed_potential_y": 0.8,
                        "contact": {"object_id": "goal:2:1:0"},
                    }
                ],
                "chronometric": {
                    "potential_datapoints": [
                        {"object_id": "goal:2:1:0", "chrono_y": 0.8}
                    ]
                },
                "outcome": {"terminal": True},
            },
            {
                "tick": 2,
                "rays": [
                    {
                        "signed_potential_y": -0.4,
                        "contact": {"object_id": "wall:0:0:0"},
                    }
                ],
                "chronometric": {
                    "potential_datapoints": [
                        {"object_id": "wall:0:0:0", "chrono_y": -0.4}
                    ]
                },
                "outcome": {"terminal": False},
            },
        ],
    }
