"""S-Agent — Scorer with G-Eval CoT (Claude Opus 4.7).

Protocol §四.(六): context budget 600-800 tokens per call.
Receives ONLY the Evidence Bundle + rubric item spec — never raw transcript.

Step 12: wired to Claude via anthropic SDK. Returns score / CoT / cited
evidence indices parsed from the model's JSON output.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.agents.base import Agent, AgentResult
from src.config import get_settings
from src.services.llm_clients import claude_generate_json, prompt_hash

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3].parent / "packages" / "shared-prompts"


def _load_system_prompt() -> str:
    path = _PROMPTS_DIR / "s_agent.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("s_agent.txt not found at %s — using minimal fallback", path)
        return (
            "You are the S-Agent. Score one rubric item 0-5 and reply with JSON "
            '{"score": int, "cot_reasoning": str, "cited_evidence_ids": [int]}.'
        )


class SAgentInput(BaseModel):
    rubric_item_id: str
    rubric_item_spec: dict[str, Any]
    evidence_bundle: dict[str, Any]


class SAgentOutput(AgentResult):
    rubric_item_id: str
    score: int  # 0-5
    cot_reasoning: str
    cited_evidence_ids: list[int] = []


def _clamp_score(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, n))


class SAgent(Agent[SAgentInput, SAgentOutput]):
    name = "S-Agent"

    def __init__(self) -> None:
        self.model_id = get_settings().s_agent_model
        self._system_prompt = _load_system_prompt()

    async def run(self, payload: SAgentInput) -> SAgentOutput:
        user_message = (
            f"Rubric item id: {payload.rubric_item_id}\n\n"
            f"Rubric item spec:\n{json.dumps(payload.rubric_item_spec, ensure_ascii=False)}\n\n"
            f"Evidence bundle:\n{json.dumps(payload.evidence_bundle, ensure_ascii=False)}\n\n"
            "Score this rubric item now."
        )

        data = await claude_generate_json(
            model=self.model_id,
            system=self._system_prompt,
            user_message=user_message,
        )

        cited_raw = data.get("cited_evidence_ids", []) or []
        cited: list[int] = []
        for v in cited_raw:
            try:
                cited.append(int(v))
            except (TypeError, ValueError):
                continue

        return SAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            prompt_hash=prompt_hash(self._system_prompt, user_message),
            rubric_item_id=payload.rubric_item_id,
            score=_clamp_score(data.get("score", 0)),
            cot_reasoning=str(data.get("cot_reasoning", ""))[:600],
            cited_evidence_ids=cited,
        )
