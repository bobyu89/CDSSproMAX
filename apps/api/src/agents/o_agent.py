"""O-Agent — Orchestrator / Session state machine.

Wave 1 shell: just exposes the phase transition logic from Protocol §四.(三).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from src.agents.base import Agent, AgentResult


class Phase(str, Enum):
    SCENARIO = "scenario"
    INQUIRY = "inquiry"
    TRANSITION = "transition"
    EXAMINATION = "examination"
    DIAGNOSIS = "diagnosis"
    REVIEW = "review"


# Exam-mode time limits (seconds), from Protocol §四.(三) / §三 of 技術計畫書
EXAM_TIME_LIMIT_S: dict[Phase, int] = {
    Phase.INQUIRY: 360,
    Phase.TRANSITION: 30,
    Phase.EXAMINATION: 360,
    Phase.DIAGNOSIS: 120,
}

_PHASE_ORDER = [
    Phase.SCENARIO,
    Phase.INQUIRY,
    Phase.TRANSITION,
    Phase.EXAMINATION,
    Phase.DIAGNOSIS,
    Phase.REVIEW,
]


def next_phase(current: Phase) -> Phase:
    """Advance to the next phase, or stay at REVIEW if already there."""
    idx = _PHASE_ORDER.index(current)
    if idx >= len(_PHASE_ORDER) - 1:
        return Phase.REVIEW
    return _PHASE_ORDER[idx + 1]


class OAgentInput(BaseModel):
    session_id: str
    current_phase: Phase
    mode: str  # "practice" | "exam"


class OAgentOutput(AgentResult):
    next_phase: Phase
    time_limit_s: int | None = None


class OAgent(Agent[OAgentInput, OAgentOutput]):
    name = "O-Agent"
    model_id = "rule-based"

    async def run(self, payload: OAgentInput) -> OAgentOutput:
        nxt = next_phase(payload.current_phase)
        limit = EXAM_TIME_LIMIT_S.get(nxt) if payload.mode == "exam" else None
        return OAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            next_phase=nxt,
            time_limit_s=limit,
        )
