"""E-Agent — Evidence extractor (sole RAG accessor).

Protocol §四.(六): context budget 300-500 tokens per call.
Wave 1 shell returns a stub Evidence Bundle so downstream Agents can run.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import Agent, AgentResult
from src.config import get_settings


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


class RagHit(BaseModel):
    chunk_id: str
    source: str
    cosine_similarity: float
    rerank_score: float


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


class EAgent(Agent[EAgentInput, EAgentOutput]):
    name = "E-Agent"

    def __init__(self) -> None:
        self.model_id = get_settings().e_agent_model

    async def run(self, payload: EAgentInput) -> EAgentOutput:
        # Wave 1 stub. Step 12 wires real Gemini + pgvector RAG.
        return EAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            rubric_item_id=payload.rubric_item_id,
            confidence=0.0,
            extraction_notes="[stub] E-Agent not yet wired to LLM or RAG",
        )
