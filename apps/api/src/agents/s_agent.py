"""S-Agent — Scorer with G-Eval CoT (Claude Opus 4.7).

Protocol §四.(六): context budget 600-800 tokens per call.
Receives ONLY the Evidence Bundle + rubric item spec — never raw transcript.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.agents.base import Agent, AgentResult
from src.config import get_settings


class SAgentInput(BaseModel):
    rubric_item_id: str
    rubric_item_spec: dict[str, Any]
    evidence_bundle: dict[str, Any]


class SAgentOutput(AgentResult):
    rubric_item_id: str
    score: int  # 0-5
    cot_reasoning: str
    cited_evidence_ids: list[int] = []


class SAgent(Agent[SAgentInput, SAgentOutput]):
    name = "S-Agent"

    def __init__(self) -> None:
        self.model_id = get_settings().s_agent_model

    async def run(self, payload: SAgentInput) -> SAgentOutput:
        # Wave 1 stub. Step 12 wires real Anthropic SDK call.
        return SAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            rubric_item_id=payload.rubric_item_id,
            score=0,
            cot_reasoning="[stub] S-Agent not yet wired to Claude",
        )
