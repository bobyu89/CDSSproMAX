"""M-Agent — Drift monitor.

Protocol §四.(七): continuously tracks override rate per rubric item across
sessions; alerts when sustained > 30% (auto-pause auto-scoring for that item).

This is mostly rule-based; LLM may be invoked occasionally to summarize
drift patterns for the M-Agent governance report.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.agents.base import Agent, AgentResult

OVERRIDE_RATE_ALERT_THRESHOLD = 0.30


class MAgentInput(BaseModel):
    rubric_item_id: str
    total_scored: int
    total_overridden: int  # grader Modify + Reject count


class MAgentOutput(AgentResult):
    rubric_item_id: str
    override_rate: float
    alert: bool
    alert_reason: str | None = None


class MAgent(Agent[MAgentInput, MAgentOutput]):
    name = "M-Agent"
    model_id = "rule-based"

    async def run(self, payload: MAgentInput) -> MAgentOutput:
        if payload.total_scored == 0:
            rate = 0.0
        else:
            rate = payload.total_overridden / payload.total_scored

        alert = rate > OVERRIDE_RATE_ALERT_THRESHOLD and payload.total_scored >= 10
        reason = (
            f"override_rate={rate:.2%} exceeds threshold "
            f"({OVERRIDE_RATE_ALERT_THRESHOLD:.0%})"
            if alert
            else None
        )
        return MAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            rubric_item_id=payload.rubric_item_id,
            override_rate=rate,
            alert=alert,
            alert_reason=reason,
        )
