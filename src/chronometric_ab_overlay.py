"""A/B-centered open Q/A overlay packets for chronometric planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_POLARITIES = ("helps", "hurts", "conditional", "unknown")
VALID_IMAGINATION_BASES = ("grid2d", "voxel3d", "mesh3d", "latent3d", "semantic3d", "mixed")


@dataclass(frozen=True)
class EvidenceClaim:
    text: str
    confidence: float


@dataclass(frozen=True)
class ABNode:
    description: str
    confidence: float
    evidence: tuple[EvidenceClaim, ...] = ()


@dataclass(frozen=True)
class GridspaceHypothesis:
    dimensions: tuple[str, ...]
    basis: str
    confidence: float


@dataclass(frozen=True)
class OpenQuestion:
    question: str
    why_it_matters: str
    answer: str | None = None
    confidence: float = 0.0


@dataclass(frozen=True)
class ObjectiveModifier:
    name: str
    description: str
    polarity: str = "unknown"
    confidence: float = 0.0
    evidence: tuple[EvidenceClaim, ...] = ()


@dataclass(frozen=True)
class RaytraceProbe:
    probe_id: str
    question: str
    origin: tuple[float, ...] = ()
    direction: tuple[float, ...] = ()
    expected_contact: str | None = None
    confidence: float = 0.0


@dataclass(frozen=True)
class ImaginationFrame:
    representation_basis: str
    description: str
    confidence: float
    artifact_ref: str | None = None
    raytrace_probes: tuple[RaytraceProbe, ...] = ()


@dataclass(frozen=True)
class CandidateBranch:
    candidate_id: str
    action: str
    expected_ab_delta: str
    questions_resolved: tuple[str, ...] = ()
    questions_open: tuple[str, ...] = ()
    nemo_confidence: float = 0.0
    chronometric_score: float | None = None
    chronometric_row_ref: str | None = None


@dataclass(frozen=True)
class ABOverlayPacket:
    state_id: str
    a_self: ABNode
    b_objective: ABNode
    gridspace: GridspaceHypothesis
    imagination_frame: ImaginationFrame | None = None
    open_questions: tuple[OpenQuestion, ...] = ()
    objective_modifiers: tuple[ObjectiveModifier, ...] = ()
    candidate_branches: tuple[CandidateBranch, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.state_id:
            raise ValueError("state_id is required")
        _validate_node("a_self", self.a_self)
        _validate_node("b_objective", self.b_objective)
        _validate_gridspace(self.gridspace)
        if self.imagination_frame is not None:
            _validate_imagination_frame(self.imagination_frame)
        for index, question in enumerate(self.open_questions):
            _validate_question(index, question)
        for index, modifier in enumerate(self.objective_modifiers):
            _validate_modifier(index, modifier)
        for index, branch in enumerate(self.candidate_branches):
            _validate_branch(index, branch)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "state_id": self.state_id,
            "ab_hypothesis": {
                "a_self": _node_to_dict(self.a_self),
                "b_objective": _node_to_dict(self.b_objective),
                "gridspace": {
                    "dimensions": list(self.gridspace.dimensions),
                    "basis": self.gridspace.basis,
                    "confidence": self.gridspace.confidence,
                },
            },
            "open_questions": [_question_to_dict(question) for question in self.open_questions],
            "imagination_frame": (
                _imagination_frame_to_dict(self.imagination_frame) if self.imagination_frame is not None else None
            ),
            "objective_modifiers": [_modifier_to_dict(modifier) for modifier in self.objective_modifiers],
            "candidate_branches": [_branch_to_dict(branch) for branch in self.candidate_branches],
            "metadata": dict(self.metadata),
        }


def packet_from_dict(data: dict[str, Any]) -> ABOverlayPacket:
    hypothesis = _dict(data.get("ab_hypothesis"))
    packet = ABOverlayPacket(
        state_id=str(data.get("state_id", "")),
        a_self=_node_from_dict(_dict(hypothesis.get("a_self"))),
        b_objective=_node_from_dict(_dict(hypothesis.get("b_objective"))),
        gridspace=_gridspace_from_dict(_dict(hypothesis.get("gridspace"))),
        imagination_frame=_optional_imagination_frame_from_dict(data.get("imagination_frame")),
        open_questions=tuple(_question_from_dict(_dict(item)) for item in _list(data.get("open_questions"))),
        objective_modifiers=tuple(
            _modifier_from_dict(_dict(item)) for item in _list(data.get("objective_modifiers"))
        ),
        candidate_branches=tuple(_branch_from_dict(_dict(item)) for item in _list(data.get("candidate_branches"))),
        metadata=_dict(data.get("metadata")),
    )
    packet.validate()
    return packet


def branch_from_planner_score(row: dict[str, Any], *, candidate_id: str | None = None) -> CandidateBranch:
    """Create a candidate branch shell from a V027+ planner-score row."""
    action = str(row.get("action_id", "unknown"))
    score = row.get("planner_pred_signed_y")
    return CandidateBranch(
        candidate_id=candidate_id or str(row.get("transition_id", row.get("planner_row_index", action))),
        action=action,
        expected_ab_delta=str(row.get("control_label", "unknown")),
        nemo_confidence=0.0,
        chronometric_score=float(score) if isinstance(score, (int, float)) and not isinstance(score, bool) else None,
        chronometric_row_ref=str(row.get("transition_id", "")) or None,
    )


def _validate_node(name: str, node: ABNode) -> None:
    if not node.description:
        raise ValueError(f"{name}.description is required")
    _validate_confidence(f"{name}.confidence", node.confidence)
    for index, evidence in enumerate(node.evidence):
        _validate_evidence(f"{name}.evidence[{index}]", evidence)


def _validate_gridspace(gridspace: GridspaceHypothesis) -> None:
    if not gridspace.basis:
        raise ValueError("gridspace.basis is required")
    _validate_confidence("gridspace.confidence", gridspace.confidence)


def _validate_question(index: int, question: OpenQuestion) -> None:
    if not question.question:
        raise ValueError(f"open_questions[{index}].question is required")
    if not question.why_it_matters:
        raise ValueError(f"open_questions[{index}].why_it_matters is required")
    _validate_confidence(f"open_questions[{index}].confidence", question.confidence)


def _validate_modifier(index: int, modifier: ObjectiveModifier) -> None:
    if not modifier.name:
        raise ValueError(f"objective_modifiers[{index}].name is required")
    if not modifier.description:
        raise ValueError(f"objective_modifiers[{index}].description is required")
    if modifier.polarity not in VALID_POLARITIES:
        raise ValueError(f"objective_modifiers[{index}].polarity must be one of {VALID_POLARITIES}")
    _validate_confidence(f"objective_modifiers[{index}].confidence", modifier.confidence)
    for evidence_index, evidence in enumerate(modifier.evidence):
        _validate_evidence(f"objective_modifiers[{index}].evidence[{evidence_index}]", evidence)


def _validate_imagination_frame(frame: ImaginationFrame) -> None:
    if frame.representation_basis not in VALID_IMAGINATION_BASES:
        raise ValueError(f"imagination_frame.representation_basis must be one of {VALID_IMAGINATION_BASES}")
    if not frame.description:
        raise ValueError("imagination_frame.description is required")
    _validate_confidence("imagination_frame.confidence", frame.confidence)
    for index, probe in enumerate(frame.raytrace_probes):
        _validate_raytrace_probe(index, probe)


def _validate_raytrace_probe(index: int, probe: RaytraceProbe) -> None:
    if not probe.probe_id:
        raise ValueError(f"imagination_frame.raytrace_probes[{index}].probe_id is required")
    if not probe.question:
        raise ValueError(f"imagination_frame.raytrace_probes[{index}].question is required")
    _validate_confidence(f"imagination_frame.raytrace_probes[{index}].confidence", probe.confidence)


def _validate_branch(index: int, branch: CandidateBranch) -> None:
    if not branch.candidate_id:
        raise ValueError(f"candidate_branches[{index}].candidate_id is required")
    if not branch.action:
        raise ValueError(f"candidate_branches[{index}].action is required")
    if not branch.expected_ab_delta:
        raise ValueError(f"candidate_branches[{index}].expected_ab_delta is required")
    _validate_confidence(f"candidate_branches[{index}].nemo_confidence", branch.nemo_confidence)


def _validate_evidence(name: str, evidence: EvidenceClaim) -> None:
    if not evidence.text:
        raise ValueError(f"{name}.text is required")
    _validate_confidence(f"{name}.confidence", evidence.confidence)


def _validate_confidence(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def _node_to_dict(node: ABNode) -> dict[str, Any]:
    return {
        "description": node.description,
        "confidence": node.confidence,
        "evidence": [_evidence_to_dict(item) for item in node.evidence],
    }


def _node_from_dict(data: dict[str, Any]) -> ABNode:
    return ABNode(
        description=str(data.get("description", "")),
        confidence=_float(data.get("confidence", 0.0)),
        evidence=tuple(_evidence_from_dict(_dict(item)) for item in _list(data.get("evidence"))),
    )


def _gridspace_from_dict(data: dict[str, Any]) -> GridspaceHypothesis:
    return GridspaceHypothesis(
        dimensions=tuple(str(item) for item in _list(data.get("dimensions"))),
        basis=str(data.get("basis", "")),
        confidence=_float(data.get("confidence", 0.0)),
    )


def _question_to_dict(question: OpenQuestion) -> dict[str, Any]:
    return {
        "question": question.question,
        "why_it_matters": question.why_it_matters,
        "answer": question.answer,
        "confidence": question.confidence,
    }


def _question_from_dict(data: dict[str, Any]) -> OpenQuestion:
    answer = data.get("answer")
    return OpenQuestion(
        question=str(data.get("question", "")),
        why_it_matters=str(data.get("why_it_matters", "")),
        answer=str(answer) if answer is not None else None,
        confidence=_float(data.get("confidence", 0.0)),
    )


def _imagination_frame_to_dict(frame: ImaginationFrame) -> dict[str, Any]:
    return {
        "representation_basis": frame.representation_basis,
        "description": frame.description,
        "confidence": frame.confidence,
        "artifact_ref": frame.artifact_ref,
        "raytrace_probes": [_raytrace_probe_to_dict(probe) for probe in frame.raytrace_probes],
    }


def _optional_imagination_frame_from_dict(value: Any) -> ImaginationFrame | None:
    if value is None:
        return None
    return _imagination_frame_from_dict(_dict(value))


def _imagination_frame_from_dict(data: dict[str, Any]) -> ImaginationFrame:
    return ImaginationFrame(
        representation_basis=str(data.get("representation_basis", "")),
        description=str(data.get("description", "")),
        confidence=_float(data.get("confidence", 0.0)),
        artifact_ref=str(data.get("artifact_ref")) if data.get("artifact_ref") is not None else None,
        raytrace_probes=tuple(_raytrace_probe_from_dict(_dict(item)) for item in _list(data.get("raytrace_probes"))),
    )


def _raytrace_probe_to_dict(probe: RaytraceProbe) -> dict[str, Any]:
    return {
        "probe_id": probe.probe_id,
        "question": probe.question,
        "origin": list(probe.origin),
        "direction": list(probe.direction),
        "expected_contact": probe.expected_contact,
        "confidence": probe.confidence,
    }


def _raytrace_probe_from_dict(data: dict[str, Any]) -> RaytraceProbe:
    expected_contact = data.get("expected_contact")
    return RaytraceProbe(
        probe_id=str(data.get("probe_id", "")),
        question=str(data.get("question", "")),
        origin=tuple(_float(item) for item in _list(data.get("origin"))),
        direction=tuple(_float(item) for item in _list(data.get("direction"))),
        expected_contact=str(expected_contact) if expected_contact is not None else None,
        confidence=_float(data.get("confidence", 0.0)),
    )


def _modifier_to_dict(modifier: ObjectiveModifier) -> dict[str, Any]:
    return {
        "name": modifier.name,
        "description": modifier.description,
        "polarity": modifier.polarity,
        "confidence": modifier.confidence,
        "evidence": [_evidence_to_dict(item) for item in modifier.evidence],
    }


def _modifier_from_dict(data: dict[str, Any]) -> ObjectiveModifier:
    return ObjectiveModifier(
        name=str(data.get("name", "")),
        description=str(data.get("description", "")),
        polarity=str(data.get("polarity", "unknown")),
        confidence=_float(data.get("confidence", 0.0)),
        evidence=tuple(_evidence_from_dict(_dict(item)) for item in _list(data.get("evidence"))),
    )


def _branch_to_dict(branch: CandidateBranch) -> dict[str, Any]:
    return {
        "candidate_id": branch.candidate_id,
        "action": branch.action,
        "expected_ab_delta": branch.expected_ab_delta,
        "questions_resolved": list(branch.questions_resolved),
        "questions_open": list(branch.questions_open),
        "nemo_confidence": branch.nemo_confidence,
        "chronometric_score": branch.chronometric_score,
        "chronometric_row_ref": branch.chronometric_row_ref,
    }


def _branch_from_dict(data: dict[str, Any]) -> CandidateBranch:
    row_ref = data.get("chronometric_row_ref")
    return CandidateBranch(
        candidate_id=str(data.get("candidate_id", "")),
        action=str(data.get("action", "")),
        expected_ab_delta=str(data.get("expected_ab_delta", "")),
        questions_resolved=tuple(str(item) for item in _list(data.get("questions_resolved"))),
        questions_open=tuple(str(item) for item in _list(data.get("questions_open"))),
        nemo_confidence=_float(data.get("nemo_confidence", 0.0)),
        chronometric_score=_optional_float(data.get("chronometric_score")),
        chronometric_row_ref=str(row_ref) if row_ref is not None else None,
    )


def _evidence_to_dict(evidence: EvidenceClaim) -> dict[str, Any]:
    return {"text": evidence.text, "confidence": evidence.confidence}


def _evidence_from_dict(data: dict[str, Any]) -> EvidenceClaim:
    return EvidenceClaim(text=str(data.get("text", "")), confidence=_float(data.get("confidence", 0.0)))


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return _float(value)
