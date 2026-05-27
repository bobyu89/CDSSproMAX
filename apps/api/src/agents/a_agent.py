"""A-Agent — Adversarial reviewer (Gemini 3.5 Flash).

Protocol §四.(六): context budget 400-600 tokens per call.
Independently reviews the Evidence Bundle + S-Agent's score and produces
an advocate_score (0-1) signalling how strongly it disagrees.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.agents.base import Agent, AgentResult
from src.config import get_settings


class AAgentInput(BaseModel):
    rubric_item_id: str
    rubric_item_spec: dict[str, Any]
    evidence_bundle: dict[str, Any]
    s_score: int
    s_cot: str


class AAgentOutput(AgentResult):
    rubric_item_id: str
    advocate_report: str
    advocate_score: float  # 0.0 (agree) → 1.0 (strong dissent)
    challenged_points: list[str] = []


class AAgent(Agent[AAgentInput, AAgentOutput]):
    name = "A-Agent"

    def __init__(self) -> None:
        self.model_id = get_settings().a_agent_model

    async def run(self, payload: AAgentInput) -> AAgentOutput:
        # Wave 1 stub. Step 12 wires real Gemini call.
        return AAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            rubric_item_id=payload.rubric_item_id,
            advocate_report="[stub] A-Agent not yet wired to Gemini",
            advocate_score=0.0,
        )
