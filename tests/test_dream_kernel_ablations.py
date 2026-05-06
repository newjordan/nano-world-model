import argparse
import importlib.util
import json
from pathlib import Path

import pytest


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
    assert metrics["source_summary"]["sequence_bytes"] > 0
    assert metrics["source_summary"]["ray_count"] == 2
    assert metrics["source_summary"]["potential_datapoint_count"] == 2
    assert metrics["source_summary"]["max_object_links_per_branch"] == 1
    assert metrics["compression_summary"]["high_value_layers"]
    assert metrics["compression_summary"]["high_value_layer_evidence"]
    assert (out_dir / "condition.json").exists()
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "ablation_rows.jsonl").exists()
    assert (out_dir / "object_value_rows.jsonl").exists()
    results = (out_dir / "RESULTS.md").read_text(encoding="utf-8")
    assert "drop_object_links" in results
    assert "training_data_promoted: `False`" in results
    assert "High-Value Evidence" in results
    assert "sequence bytes" in results


def test_dream_kernel_ablation_custom_sequence_does_not_pull_default_sidecars(tmp_path):
    module = _load_ablation_module()
    sequence_path = tmp_path / "custom" / "dream_sequence.json"
    out_dir = tmp_path / "ablations"
    sequence_path.parent.mkdir()
    sequence_path.write_text(json.dumps(_sequence(), sort_keys=True) + "\n", encoding="utf-8")

    metrics = module.run(
        argparse.Namespace(
            sequence=sequence_path,
            confirmations=None,
            reviews=None,
            out_dir=out_dir,
            run_label="test_custom_sequence_no_default_sidecars",
        )
    )

    assert metrics["source_summary"]["nemo_confirmations"] == 0
    assert metrics["source_summary"]["nemo_reviews"] == 0
    assert metrics["condition"]["nemo_confirmations"] is None
    assert metrics["condition"]["nemo_reviews"] is None


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda sequence: sequence.pop("frames"), "frames"),
        (lambda sequence: sequence.pop("object_registry"), "object_registry"),
        (
            lambda sequence: sequence["branch_potentials"][0].update({"branch_id": "missing.branch"}),
            "unknown id missing.branch",
        ),
        (
            lambda sequence: sequence["object_link_hypotheses"][0].update({"probability": 1.5}),
            "probability",
        ),
    ],
)
def test_dream_kernel_ablation_runner_rejects_malformed_sequences(tmp_path, mutate, message):
    module = _load_ablation_module()
    sequence = _sequence()
    mutate(sequence)
    sequence_path = tmp_path / "dream_sequence.json"
    sequence_path.write_text(json.dumps(sequence, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        module.run(
            argparse.Namespace(
                sequence=sequence_path,
                confirmations=tmp_path / "missing_confirmations.json",
                reviews=tmp_path / "missing_reviews.json",
                out_dir=tmp_path / "ablations",
                run_label="test_bad_sequence",
            )
        )


def _sequence():
    return {
        "schema": "dream_kernel.sequence.v003",
        "integrity": {
            "sequence_hash": "testhash",
            "frame_count": 2,
            "invariant_passed": True,
            "invariant_errors": [],
        },
        "object_registry": [
            {
                "object_id": "agent",
                "kind": "agent",
                "category_id": "entity.agent.self",
                "category_confidence": 1.0,
                "open_tags": ["self_anchor"],
                "map_coord": {"x": 1, "y": 1, "z": 0},
                "source": "sim_state.entity",
                "confidence": 1.0,
                "dynamic": True,
            },
            {
                "object_id": "goal:2:1:0",
                "kind": "goal",
                "category_id": "map.terminal.positive",
                "category_confidence": 1.0,
                "open_tags": ["terminal", "branch_reward_candidate"],
                "map_coord": {"x": 2, "y": 1, "z": 0},
                "source": "known_map.static_cell",
                "confidence": 1.0,
                "dynamic": False,
            },
            {
                "object_id": "wall:0:0:0",
                "kind": "wall",
                "category_id": "map.structural.wall",
                "category_confidence": 1.0,
                "open_tags": ["structural", "blocks_motion"],
                "map_coord": {"x": 0, "y": 0, "z": 0},
                "source": "known_map.static_cell",
                "confidence": 1.0,
                "dynamic": False,
            },
        ],
        "branch_matrix": [
            {
                "branch_id": "tick0.right",
                "action_id": "right",
                "end_tick": 1,
                "chrono_y_net": 0.8,
                "supporting_objects": ["agent", "goal:2:1:0"],
                "risk_objects": [],
            },
            {
                "branch_id": "tick1.wait",
                "action_id": "wait",
                "end_tick": 2,
                "chrono_y_net": -0.4,
                "supporting_objects": ["agent"],
                "risk_objects": ["wall:0:0:0"],
            },
        ],
        "branch_potentials": [
            {
                "potential_id": "bp:tick0_right_goal",
                "branch_id": "tick0.right",
                "object_id": "goal:2:1:0",
                "outcome_probability": 0.9,
                "positive_probability": 0.9,
                "negative_probability": 0.1,
                "chrono_y_correlation": 0.8,
                "uncertainty": 0.0,
            },
            {
                "potential_id": "bp:tick1_wait_wall",
                "branch_id": "tick1.wait",
                "object_id": "wall:0:0:0",
                "outcome_probability": 0.7,
                "positive_probability": 0.3,
                "negative_probability": 0.7,
                "chrono_y_correlation": -0.4,
                "uncertainty": 0.0,
            },
        ],
        "object_link_hypotheses": [
            {
                "link_id": "link:tick0_right_agent_goal",
                "branch_id": "tick0.right",
                "source_object_id": "agent",
                "target_object_id": "goal:2:1:0",
                "probability": 0.8,
                "chrono_y_correlation": 0.8,
                "evidence_sources": ["bp:tick0_right_goal"],
            },
            {
                "link_id": "link:tick1_wait_agent_wall",
                "branch_id": "tick1.wait",
                "source_object_id": "agent",
                "target_object_id": "wall:0:0:0",
                "probability": 0.4,
                "chrono_y_correlation": -0.4,
                "evidence_sources": ["bp:tick1_wait_wall"],
            },
        ],
        "nemo_relay": {
            "open_questions": [
                {
                    "branch_id": "tick0.right",
                    "object_id": "goal:2:1:0",
                    "hypothesis_refs": ["bp:tick0_right_goal"],
                },
                {
                    "branch_id": "tick1.wait",
                    "object_id": "wall:0:0:0",
                    "hypothesis_refs": ["bp:tick1_wait_wall"],
                },
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
                        {
                            "object_id": "goal:2:1:0",
                            "chrono_y": 0.8,
                            "provenance": {"branch_id": "tick0.right", "confidence": 1.0},
                        }
                    ]
                },
                "outcome": {"branch_id": "tick0.right", "terminal": True},
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
                        {
                            "object_id": "wall:0:0:0",
                            "chrono_y": -0.4,
                            "provenance": {"branch_id": "tick1.wait", "confidence": 1.0},
                        }
                    ]
                },
                "outcome": {"branch_id": "tick1.wait", "terminal": False},
            },
        ],
    }
