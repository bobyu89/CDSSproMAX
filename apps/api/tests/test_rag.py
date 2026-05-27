"""Tests for the RAG subsystem and its integration with E-Agent."""

from __future__ import annotations

import pytest

from src.agents import e_agent as e_module
from src.agents.e_agent import EAgent, EAgentInput
from src.rag.bibliotheke import Bibliotheke, RagHit, confidence_from_hits

pytestmark = pytest.mark.asyncio


# === confidence_from_hits =================================================

def test_confidence_from_hits_empty():
    assert confidence_from_hits([]) == 0.0


def test_confidence_from_hits_weighted_average():
    """Weighted avg of rerank scores: sum(w*s) / sum(w) where w == s."""
    hits = [
        RagHit(chunk_id="a", source="s", content="c", cosine_similarity=0.5, rerank_score=0.9),
        RagHit(chunk_id="b", source="s", content="c", cosine_similarity=0.5, rerank_score=0.5),
        RagHit(chunk_id="c", source="s", content="c", cosine_similarity=0.5, rerank_score=0.1),
    ]
    # numerator = 0.9*0.9 + 0.5*0.5 + 0.1*0.1 = 0.81 + 0.25 + 0.01 = 1.07
    # denominator = 0.9 + 0.5 + 0.1 = 1.5
    # expected ≈ 0.7133
    assert confidence_from_hits(hits) == pytest.approx(1.07 / 1.5, rel=1e-6)


def test_confidence_from_hits_single():
    hits = [
        RagHit(chunk_id="a", source="s", content="c", cosine_similarity=0.7, rerank_score=0.8)
    ]
    assert confidence_from_hits(hits) == pytest.approx(0.8)


def test_confidence_from_hits_zero_weights_fallback():
    """If all rerank scores are 0, weighted avg falls back to simple mean."""
    hits = [
        RagHit(chunk_id="a", source="s", content="c", cosine_similarity=0.5, rerank_score=0.0),
        RagHit(chunk_id="b", source="s", content="c", cosine_similarity=0.5, rerank_score=0.0),
    ]
    assert confidence_from_hits(hits) == 0.0


# === Bibliotheke.search ===================================================

class _FakeEmbedder:
    def __init__(self):
        self.calls: list[str] = []

    async def embed_one(self, text: str) -> list[float]:
        self.calls.append(text)
        return [0.1] * 768


class _FakeReranker:
    def __init__(self):
        self.calls: list[tuple[str, list[str]]] = []

    async def rerank(self, query, candidates, top_k=5):  # noqa: ARG002
        self.calls.append((query, candidates))
        # reverse order to prove rerank actually reorders
        return [(i, 1.0 - 0.1 * i) for i in range(len(candidates) - 1, -1, -1)][:top_k]


class _Row:
    """Stand-in for a SQLAlchemy Row with .id/.source/.content/.distance."""

    def __init__(self, idx: int):
        self.id = f"chunk-{idx}"
        self.source = f"src-{idx}"
        self.content = f"content {idx}"
        self.distance = 0.1 * idx  # cosine_distance


async def test_bibliotheke_two_stage_retrieval(monkeypatch):
    """Verifies pgvector stage → rerank stage pipeline is invoked end-to-end."""
    embedder = _FakeEmbedder()
    reranker = _FakeReranker()
    biblio = Bibliotheke(embedder=embedder, reranker=reranker)

    # Mock the AsyncSessionLocal context manager to return our fake rows
    fake_rows = [_Row(i) for i in range(3)]

    class _FakeResult:
        def all(self):
            return fake_rows

    class _FakeSession:
        async def execute(self, _stmt):
            return _FakeResult()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(
        "src.rag.bibliotheke.AsyncSessionLocal",
        lambda: _FakeSession(),
    )

    hits = await biblio.search("test query", top_k_dense=3, top_k_final=2)

    # Stage 1: embedder was called once with the query
    assert embedder.calls == ["test query"]
    # Stage 2: reranker received the dense candidates
    assert len(reranker.calls) == 1
    rerank_query, rerank_candidates = reranker.calls[0]
    assert rerank_query == "test query"
    assert rerank_candidates == ["content 0", "content 1", "content 2"]

    # Final hits: top_k_final=2, reranker reversed order so we expect indices 2 then 1
    assert len(hits) == 2
    assert hits[0].chunk_id == "chunk-2"
    assert hits[1].chunk_id == "chunk-1"
    # cosine_similarity = 1 - distance
    assert hits[0].cosine_similarity == pytest.approx(1.0 - 0.2)


async def test_bibliotheke_empty_query():
    biblio = Bibliotheke(embedder=_FakeEmbedder(), reranker=_FakeReranker())
    assert await biblio.search("   ") == []


# === E-Agent graceful RAG failure =========================================

async def test_e_agent_handles_rag_failure(monkeypatch):
    """If Bibliotheke.search raises (e.g. DB down), E-Agent still runs."""

    class _BrokenBibliotheke:
        async def search(self, *args, **kwargs):  # noqa: ARG002
            raise RuntimeError("DB unavailable")

    async def fake_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "rubric_item_id": "lqqopera.location",
            "evidence_segments": [],
            "confidence": 0.42,
            "extraction_notes": "no rag",
        }

    monkeypatch.setattr(e_module, "gemini_generate_json", fake_gemini)

    e = EAgent(bibliotheke=_BrokenBibliotheke())
    out = await e.run(
        EAgentInput(
            rubric_item_id="lqqopera.location",
            transcript_text="(student): 哪裡痛？",
            case_context="chest pain",
        )
    )
    assert out.rag_hits == []
    # No hits → fall back to model-reported confidence
    assert out.confidence == pytest.approx(0.42)


async def test_e_agent_uses_confidence_from_hits(monkeypatch):
    """When RAG returns hits, E-Agent overrides model confidence with hit-derived value."""

    hits = [
        RagHit(chunk_id="a", source="s", content="c", cosine_similarity=0.9, rerank_score=0.9),
        RagHit(chunk_id="b", source="s", content="c", cosine_similarity=0.7, rerank_score=0.7),
    ]

    class _GoodBibliotheke:
        async def search(self, *args, **kwargs):  # noqa: ARG002
            return hits

    async def fake_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "rubric_item_id": "lqqopera.location",
            "evidence_segments": [],
            "confidence": 0.1,  # should be ignored
            "extraction_notes": "with rag",
        }

    monkeypatch.setattr(e_module, "gemini_generate_json", fake_gemini)

    e = EAgent(bibliotheke=_GoodBibliotheke())
    out = await e.run(
        EAgentInput(
            rubric_item_id="lqqopera.location",
            transcript_text="(student): 哪裡痛？",
            case_context="chest pain",
        )
    )
    assert len(out.rag_hits) == 2
    assert out.confidence == pytest.approx(confidence_from_hits(hits))
    assert out.confidence != pytest.approx(0.1)
