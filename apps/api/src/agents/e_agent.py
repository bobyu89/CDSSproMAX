"""E-Agent — Evidence extractor (sole RAG accessor).

Protocol §四.(六): context budget 300-500 tokens per call.

Wired to Gemini 3.5 Flash and to the Bibliotheke RAG (pgvector + CrossEncoder).
Per Protocol §四 唯一存取原則 — only the E-Agent calls ``Bibliotheke.search``.
RAG failures (e.g. DB unavailable) degrade gracefully: the agent still emits
an Evidence Bundle with ``rag_hits=[]`` and the LLM-reported confidence.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import Agent, AgentResult
from src.config import get_settings
from src.rag.bibliotheke import Bibliotheke, RagHit, confidence_from_hits, get_bibliotheke
from src.services.llm_clients import gemini_generate_json, prompt_hash

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3].parent / "packages" / "shared-prompts"


def _load_system_prompt() -> str:
    path = _PROMPTS_DIR / "e_agent.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("e_agent.txt not found at %s — using minimal fallback", path)
        return "You are the E-Agent. Extract evidence and reply in JSON."


class EAgentInput(BaseModel):
    rubric_item_id: str
    transcript_text: str
    case_context: str = ""


class EvidenceSegment(BaseModel):
    transcript_id: str | None = None
    start_ms: int = 0
    end_ms: int = 0
    speaker: str = "student"
    text: str
    relevance_score: float = 0.0


class EAgentOutput(AgentResult):
    rubric_item_id: str
    evidence_segments: list[EvidenceSegment] = Field(default_factory=list)
    rag_hits: list[RagHit] = Field(default_factory=list)
    confidence: float = 0.0
    extraction_notes: str = ""

    def as_bundle(self) -> dict[str, Any]:
        """Serialize as the Evidence Bundle JSON consumed by S-Agent / A-Agent."""
        return {
            "rubric_item_id": self.rubric_item_id,
            "evidence_segments": [s.model_dump() for s in self.evidence_segments],
            "rag_hits": [h.model_dump() for h in self.rag_hits],
            "confidence": self.confidence,
            "extraction_notes": self.extraction_notes,
        }


def _format_rag_context(hits: list[RagHit]) -> str:
    if not hits:
        return "(no reference knowledge retrieved)"
    lines = []
    for i, h in enumerate(hits, start=1):
        lines.append(f"[Ref {i}] {h.source} (rerank={h.rerank_score:.2f})\n{h.content}")
    return "\n\n".join(lines)


class EAgent(Agent[EAgentInput, EAgentOutput]):
    name = "E-Agent"

    def __init__(self, bibliotheke: Bibliotheke | None = None) -> None:
        self.model_id = get_settings().e_agent_model
        self._system_prompt = _load_system_prompt()
        self._bibliotheke = bibliotheke or get_bibliotheke()

    async def _retrieve(self, payload: EAgentInput) -> list[RagHit]:
        query = f"{payload.rubric_item_id} {payload.case_context[:200]}".strip()
        try:
            return await self._bibliotheke.search(query, top_k_final=5)
        except Exception as exc:  # pragma: no cover - graceful degradation
            logger.warning("Bibliotheke.search failed (%s) — proceeding without RAG", exc)
            return []

    async def run(self, payload: EAgentInput) -> EAgentOutput:
        rag_hits = await self._retrieve(payload)
        rag_block = _format_rag_context(rag_hits)

        user_prompt = (
            f"Rubric item id: {payload.rubric_item_id}\n\n"
            f"Case context:\n{payload.case_context or '(none)'}\n\n"
            f"Student transcript:\n{payload.transcript_text}\n\n"
            f"Reference knowledge base extracts (ground truth):\n{rag_block}\n\n"
            "Extract evidence for the rubric item above."
        )

        data = await gemini_generate_json(
            model=self.model_id,
            prompt=user_prompt,
            system_instruction=self._system_prompt,
        )

        segments_raw = data.get("evidence_segments", [])
        segments = [
            EvidenceSegment(
                speaker=s.get("speaker", "student"),
                text=str(s.get("text", "")),
                relevance_score=float(s.get("relevance_score", 0.0)),
            )
            for s in segments_raw
            if isinstance(s, dict)
        ]

        model_confidence = float(data.get("confidence", 0.0))
        # If we have RAG hits, derive confidence from them (Protocol §四.(三)).
        confidence = confidence_from_hits(rag_hits) if rag_hits else model_confidence

        return EAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            prompt_hash=prompt_hash(self._system_prompt, user_prompt),
            rubric_item_id=str(data.get("rubric_item_id", payload.rubric_item_id)),
            evidence_segments=segments,
            rag_hits=rag_hits,
            confidence=confidence,
            extraction_notes=str(data.get("extraction_notes", ""))[:200],
        )
