import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_harness_module():
    path = ROOT / "scripts" / "launch_human_eval_harness.py"
    spec = importlib.util.spec_from_file_location("launch_human_eval_harness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run_smattering(out_dir: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_chronometric_sensory_smattering.py",
            "--run-label",
            "test_v034_harness",
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_harness_loads_legacy_records_and_saves_review_labels(tmp_path):
    harness = _load_harness_module()
    out_dir = tmp_path / "smattering"
    _run_smattering(out_dir)

    records_path = out_dir / "sensory_records.jsonl"
    legacy_rows = []
    for line in records_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        row.pop("review_assets")
        legacy_rows.append(row)
    records_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in legacy_rows),
        encoding="utf-8",
    )
    (out_dir / "dream_sequence.json").write_text(
        json.dumps(
            {
                "schema": "dream_kernel.sequence.v003",
                "integrity": {
                    "sequence_hash": "testhash",
                    "frame_count": 1,
                    "invariant_passed": True,
                    "invariant_errors": [],
                },
                "object_registry": [
                    {
                        "object_id": "agent",
                        "kind": "agent",
                        "category_id": "entity.agent.self",
                        "category_confidence": 1.0,
                        "open_tags": ["entity", "self_anchor"],
                        "hypothesis_refs": ["link:tick0_wait:wall_2_1_0:agent"],
                        "map_coord": {"x": 1, "y": 1, "z": 0},
                        "extent": [{"x": 1, "y": 1, "z": 0}],
                        "source": "sim_state.entity",
                        "confidence": 1.0,
                        "dynamic": True,
                    },
                    {
                        "object_id": "wall:2:1:0",
                        "kind": "wall",
                        "category_id": "map.structural.wall",
                        "category_confidence": 1.0,
                        "open_tags": ["map_cell", "structural"],
                        "hypothesis_refs": ["bp:tick0_wait:wall_2_1_0:0"],
                        "map_coord": {"x": 2, "y": 1, "z": 0},
                        "extent": [{"x": 2, "y": 1, "z": 0}],
                        "source": "known_map.static_cell",
                        "confidence": 1.0,
                        "dynamic": False,
                    }
                ],
                "branch_matrix": [
                    {
                        "branch_id": "tick0.wait",
                        "action_id": "wait",
                        "start_tick": 0,
                        "end_tick": 0,
                        "map_anchor": {"x": 1, "y": 1, "z": 0},
                        "chrono_y_net": -0.25,
                        "chrono_y_min": -0.25,
                        "positive_mass": 0.0,
                        "negative_exposure": -0.25,
                        "supporting_objects": [],
                        "risk_objects": ["wall:2:1:0"],
                        "frame_hash": "abc123",
                    }
                ],
                "branch_potentials": [
                    {
                        "potential_id": "bp:tick0_wait:wall_2_1_0:0",
                        "branch_id": "tick0.wait",
                        "object_id": "wall:2:1:0",
                        "category_id": "map.structural.wall",
                        "event_coord": {"t": 0, "x": 2, "y_chrono": -0.25, "z": 1},
                        "outcome_probability": 0.625,
                        "positive_probability": 0.375,
                        "negative_probability": 0.625,
                        "chrono_y_correlation": -0.25,
                        "uncertainty": 0.0,
                        "probability_source": "chrono_y_linear_projection_v001",
                        "relation_candidate_ids": ["link:tick0_wait:wall_2_1_0:agent"],
                        "evidence_sources": ["ray_contact"],
                        "hypothesis": "wall may block wait",
                        "nemo_relay_required": True,
                    }
                ],
                "object_link_hypotheses": [
                    {
                        "link_id": "link:tick0_wait:wall_2_1_0:agent",
                        "branch_id": "tick0.wait",
                        "source_object_id": "wall:2:1:0",
                        "target_object_id": "agent",
                        "relation_kind": "branch.coactivation.open_relation",
                        "probability": 0.625,
                        "chrono_y_correlation": -0.25,
                        "evidence_sources": ["bp:tick0_wait:wall_2_1_0:0"],
                        "unresolved_questions": ["what relation exists?"],
                        "nemo_relay_required": True,
                    }
                ],
                "nemo_relay": {
                    "schema": "dream_kernel.nemo_relay.v001",
                    "relay_id": "dream_kernel.branch_potential_relay.v001",
                    "required_model": "nemotron_3_nano_omni",
                    "model_role": "semantic_thinking_relay_for_open_world_object_relations",
                    "relay_status": "packet_ready_model_not_called",
                    "branch_potential_ids": ["bp:tick0_wait:wall_2_1_0:0"],
                    "object_link_ids": ["link:tick0_wait:wall_2_1_0:agent"],
                    "open_questions": [
                        {
                            "question_id": "nq:tick0_wait_wall",
                            "branch_id": "tick0.wait",
                            "object_id": "wall:2:1:0",
                            "link_id": None,
                            "prompt": "confirm open relation",
                            "hypothesis_refs": ["bp:tick0_wait:wall_2_1_0:0"],
                            "expected_answer_shape": "json",
                        }
                    ],
                },
                "frames": [
                    {
                        "tick": 0,
                        "render_top_down": ["###", "#A#", "###"],
                        "rays": [
                            {
                                "origin": {"x": 1, "y": 1, "z": 0},
                                "direction": {"x": 1, "y": 0, "z": 0},
                                "path": [{"x": 2, "y": 1, "z": 0}],
                                "contact": {
                                    "object_id": "wall:2:1:0",
                                    "category_id": "map.structural.wall",
                                    "position": {"x": 2, "y": 1, "z": 0},
                                    "kind": "wall",
                                    "label": "wall",
                                },
                            }
                        ],
                        "outcome": None,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    session = harness.load_session(out_dir)
    first = session["records"][0]
    assert first["review_assets"]["predicted_grid"][1][1] == 2
    assert first["review_assets"]["truth_grid"][1][3] == 3
    assert session["dream_sequence"]["schema"] == "dream_kernel.sequence.v003"
    assert session["nemo_confirmations"]["schema"] == "dream_kernel.nemo_relay_confirmations.v001"
    assert session["dream_sequence"]["frames"][0]["render_top_down"][1] == "#A#"
    assert harness.THREE_MODULE_PATH.exists()
    packet = harness._nemo_branch_packet(session["dream_sequence"], "tick0.wait")
    assert packet["branch"]["branch_id"] == "tick0.wait"
    assert packet["branch_potentials"][0]["category_id"] == "map.structural.wall"
    assert packet["open_questions"][0]["question_id"] == "nq:tick0_wait_wall"
    (out_dir / "nemo_relay_confirmations.json").write_text(
        json.dumps(
            {
                "schema": "dream_kernel.nemo_relay_confirmations.v001",
                "confirmations": {
                    "tick0.wait": {
                        "schema": "dream_kernel.nemo_branch_confirmation.v001",
                        "branch_id": "tick0.wait",
                        "created_at": "2026-05-06T00:00:00+00:00",
                        "model": "nemotron_3_nano_omni",
                        "relay_url": "http://127.0.0.1:8000/v1/responses",
                        "relay_ok": True,
                        "relay_error": None,
                        "response_text": json.dumps(
                            {
                                "branch_id": "tick0.wait",
                                "category_revisions": [
                                    {"object_id": "wall:2:1:0", "category_id": "map.structural.wall"}
                                ],
                                "relation_candidates": [
                                    {
                                        "source_object_id": "wall:2:1:0",
                                        "target_object_id": "agent",
                                        "relation_kind": "blocks_motion",
                                    }
                                ],
                                "confidence": 0.72,
                                "evidence_needed": ["second ray observation"],
                                "action_recommendation": "do not promote without branch review",
                            }
                        ),
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    session = harness.load_session(out_dir)
    review = harness.sanitize_nemo_review(
        {
            "branch_id": "tick0.wait",
            "review_label": "partial",
            "promotion_flags": {
                "category_revisions": True,
                "relation_candidates": True,
                "evidence_needed": False,
                "action_recommendation": True,
            },
            "review_notes": "Relations are plausible but still need more evidence.",
        },
        {"tick0.wait"},
    )
    reviews_payload = harness.save_nemo_review(out_dir, review, session)
    promoted = reviews_payload["promoted_evidence"]["tick0.wait"]
    assert reviews_payload["reviews"]["tick0.wait"]["review_label"] == "partial"
    assert promoted["category_revisions"][0]["object_id"] == "wall:2:1:0"
    assert promoted["relation_candidates"][0]["relation_kind"] == "blocks_motion"
    assert promoted["action_recommendation"] == "do not promote without branch review"
    assert "evidence_needed" not in promoted
    assert (out_dir / "nemo_relay_reviews.json").exists()
    assert (out_dir / "nemo_relay_review_events.jsonl").exists()

    label = harness.sanitize_label(
        {
            "case_id": first["state_id"],
            "human_label": "accept",
            "rank": "1",
            "outcome_label": "sensible_positive",
            "failure_modes": [],
            "human_notes": "Looks aligned.",
            "image_notes": {"predicted_grid": "start map reads cleanly"},
        },
        {record["state_id"] for record in session["records"]},
    )
    payload = harness.save_label(out_dir, label, session)

    assert payload["labels"][first["state_id"]]["rank"] == 1
    assert (out_dir / "human_labels.json").exists()
    assert (out_dir / "human_label_events.jsonl").exists()
    markdown = (out_dir / "HUMAN_LABELS.md").read_text(encoding="utf-8")
    assert first["state_id"] in markdown
    assert "Looks aligned." in markdown
    assert "start map reads cleanly" in markdown


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema": "dream_kernel.sequence.v003", "frames": []}, "object_registry"),
        (
            {
                "schema": "dream_kernel.sequence.v003",
                "integrity": {
                    "sequence_hash": "testhash",
                    "frame_count": 1,
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
                    }
                ],
                "branch_matrix": [],
                "branch_potentials": [
                    {
                        "potential_id": "bp:bad",
                        "branch_id": "missing.branch",
                        "object_id": "agent",
                        "outcome_probability": 0.5,
                        "positive_probability": 0.5,
                        "negative_probability": 0.5,
                        "uncertainty": 0.0,
                        "chrono_y_correlation": 0.0,
                    }
                ],
                "object_link_hypotheses": [],
                "nemo_relay": {},
                "frames": [{"tick": 1, "rays": [], "chronometric": {}, "outcome": None}],
            },
            "missing.branch",
        ),
    ],
)
def test_harness_rejects_malformed_dream_sequences(tmp_path, payload, message):
    harness = _load_harness_module()
    (tmp_path / "dream_sequence.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        harness.load_dream_sequence(tmp_path)
