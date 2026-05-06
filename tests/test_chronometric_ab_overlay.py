import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_ab_overlay import (  # noqa: E402
    ABNode,
    ABOverlayPacket,
    CandidateBranch,
    EvidenceClaim,
    GridspaceHypothesis,
    ImaginationFrame,
    ObjectiveModifier,
    OpenQuestion,
    RaytraceProbe,
    branch_from_planner_score,
    packet_from_dict,
)


def test_ab_overlay_packet_roundtrips_unrestricted_questions_and_modifiers():
    packet = ABOverlayPacket(
        state_id="state-1",
        a_self=ABNode(
            description="controllable object hypothesis",
            confidence=0.8,
            evidence=(EvidenceClaim(text="moves after ACTION4 in prior frame", confidence=0.7),),
        ),
        b_objective=ABNode(description="increase signed-Y outcome", confidence=0.65),
        gridspace=GridspaceHypothesis(dimensions=("x", "y", "t", "latent_rule"), basis="mixed", confidence=0.6),
        imagination_frame=ImaginationFrame(
            representation_basis="voxel3d",
            description="internal 3D map of self, surfaces, and candidate contacts",
            confidence=0.58,
            artifact_ref="memory://state-1/imagination/voxel",
            raytrace_probes=(
                RaytraceProbe(
                    probe_id="r0",
                    question="Does the imagined branch contact a blocking surface before B?",
                    origin=(0.0, 0.0, 0.0),
                    direction=(1.0, 0.0, 0.0),
                    expected_contact="unknown surface",
                    confidence=0.45,
                ),
            ),
        ),
        open_questions=(
            OpenQuestion(
                question="What relation could make the direct A-to-B branch fail or become suboptimal?",
                why_it_matters="the answer changes which branch should be scored first",
                answer=None,
                confidence=0.4,
            ),
        ),
        objective_modifiers=(
            ObjectiveModifier(
                name="wall-bump alignment hypothesis",
                description="emergent relation between contact and future movement",
                polarity="conditional",
                confidence=0.55,
            ),
        ),
        candidate_branches=(
            CandidateBranch(
                candidate_id="c0",
                action="ACTION4",
                expected_ab_delta="moves A closer to B under current hypothesis",
                questions_open=("q0",),
                nemo_confidence=0.5,
                chronometric_score=0.25,
            ),
        ),
    )

    data = packet.to_dict()
    restored = packet_from_dict(data)

    assert restored == packet
    assert data["imagination_frame"]["representation_basis"] == "voxel3d"
    assert data["imagination_frame"]["raytrace_probes"][0]["probe_id"] == "r0"
    assert data["objective_modifiers"][0]["name"] == "wall-bump alignment hypothesis"
    assert data["open_questions"][0]["question"].startswith("What relation")


def test_ab_overlay_rejects_out_of_range_confidence():
    packet = ABOverlayPacket(
        state_id="state-1",
        a_self=ABNode(description="self", confidence=1.2),
        b_objective=ABNode(description="objective", confidence=0.5),
        gridspace=GridspaceHypothesis(dimensions=("x",), basis="grid", confidence=0.5),
    )

    with pytest.raises(ValueError, match="a_self.confidence"):
        packet.validate()


def test_objective_modifier_names_are_not_taxonomy_limited():
    packet = ABOverlayPacket(
        state_id="state-2",
        a_self=ABNode(description="self", confidence=0.5),
        b_objective=ABNode(description="objective", confidence=0.5),
        gridspace=GridspaceHypothesis(dimensions=("semantic_axis_17",), basis="semantic", confidence=0.5),
        objective_modifiers=(
            ObjectiveModifier(
                name="the blue count changes after the second hesitation",
                description="free-form discovered rule",
                polarity="unknown",
                confidence=0.25,
            ),
        ),
    )

    packet.validate()
    assert packet.objective_modifiers[0].name.startswith("the blue count")


def test_candidate_branch_can_reference_planner_score_row():
    row = {
        "transition_id": "run:000003",
        "action_id": "ACTION3",
        "control_label": "dominant_group:translation",
        "planner_pred_signed_y": 0.125,
    }

    branch = branch_from_planner_score(row)

    assert branch.candidate_id == "run:000003"
    assert branch.action == "ACTION3"
    assert branch.expected_ab_delta == "dominant_group:translation"
    assert branch.chronometric_score == 0.125


def test_imagination_frame_rejects_unknown_representation_basis():
    packet = ABOverlayPacket(
        state_id="state-3",
        a_self=ABNode(description="self", confidence=0.5),
        b_objective=ABNode(description="objective", confidence=0.5),
        gridspace=GridspaceHypothesis(dimensions=("x",), basis="grid", confidence=0.5),
        imagination_frame=ImaginationFrame(
            representation_basis="hardcoded_trap_taxonomy",
            description="bad basis",
            confidence=0.5,
        ),
    )

    with pytest.raises(ValueError, match="imagination_frame.representation_basis"):
        packet.validate()
