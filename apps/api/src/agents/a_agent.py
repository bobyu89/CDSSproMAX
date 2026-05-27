"""A-Agent — Adversarial reviewer (Gemini 3.5 Flash).

Protocol §四.(六): context budget 400-600 tokens per call.

Per docs/architecture/duat-pipeline.md the A-Agent reviews the Evidence
Bundle INDEPENDENTLY of the S-Agent and runs in parallel with it. The
Consensus Arbiter (rule-based) is what compares the two outputs.

For backward compatibility with earlier shell tests, `s_score` and `s_cot`
remain optional input fields but are NOT included in the prompt sent to
the model — A-Agent must reach its own verdict from the Evidence Bundle.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.agents.base import Agent, AgentResult
from src.config import get_settings
from src.services.llm_clients import gemini_generate_json, prompt_hash

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3].parent / "packages" / "shared-prompts"


def _load_system_prompt() -> str:
    path = _PROMPTS_DIR / "a_agent.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("a_agent.txt not found at %s — using minimal fallback", path)
        return (
            "You are the A-Agent. Critically review the Evidence Bundle against "
            "the rubric item and reply with JSON "
            '{"advocate_report": str, "advocate_score": float, "challenged_points": [str]}.'
        )


class AAgentInput(BaseModel):
    rubric_item_id: str
    rubric_item_spec: dict[str, Any]
    evidence_bundle: dict[str, Any]
    # Kept optional for back-compat; A-Agent does NOT consume these in its prompt
    # (it reviews the evidence independently — Arbiter is what compares S vs A).
    s_score: int | None = None
    s_cot: str | None = None


class AAgentOutput(AgentResult):
    rubric_item_id: str
    advocate_report: str
    advocate_score: float  # 0.0 (agree) → 1.0 (strong dissent)
    challenged_points: list[str] = []


def _clamp_unit(value: Any) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


class AAgent(Agent[AAgentInput, AAgentOutput]):
    name = "A-Agent"

    def __init__(self) -> None:
        self.model_id = get_settings().a_agent_model
        self._system_prompt = _load_system_prompt()

    async def run(self, payload: AAgentInput) -> AAgentOutput:
        user_prompt = (
            f"Rubric item id: {payload.rubric_item_id}\n\n"
            f"Rubric item spec:\n{json.dumps(payload.rubric_item_spec, ensure_ascii=False)}\n\n"
            f"Evidence bundle:\n{json.dumps(payload.evidence_bundle, ensure_ascii=False)}\n\n"
            "Challenge whether the evidence justifies a high score on this item."
        )

        data = await gemini_generate_json(
            model=self.model_id,
            prompt=user_prompt,
            system_instruction=self._system_prompt,
        )

        challenged_raw = data.get("challenged_points", []) or []
        challenged = [str(p)[:120] for p in challenged_raw if p]

        return AAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            prompt_hash=prompt_hash(self._system_prompt, user_prompt),
            rubric_item_id=payload.rubric_item_id,
            advocate_report=str(data.get("advocate_report", ""))[:600],
            advocate_score=_clamp_unit(data.get("advocate_score", 0.0)),
            challenged_points=challenged,
        )
