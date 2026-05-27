"""Bibliotheke — knowledge base retrieval for E-Agent.

Two-stage retrieval:
  Stage 1  pgvector cosine distance search on ``BibliothekeChunk.embedding``
           returning ``top_k_dense`` candidates (default 20).
  Stage 2  CrossEncoder rerank, keep ``top_k_final`` (default 5).

E-Agent is the *only* consumer (Protocol §四 唯一存取原則).
"""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import BaseModel
from sqlalchemy import select

from src.db.models import BibliothekeChunk
from src.db.session import AsyncSessionLocal
from src.rag.embedder import Embedder, get_embedder
from src.rag.reranker import Reranker, get_reranker

logger = logging.getLogger(__name__)


class RagHit(BaseModel):
    """One retrieved + reranked chunk surfaced to the E-Agent."""

    chunk_id: str
    source: str
    content: str
    cosine_similarity: float
    rerank_score: float


def confidence_from_hits(hits: list[RagHit]) -> float:
    """Weighted average of rerank scores.

    Weights are the rerank scores themselves — top hits dominate the average,
    matching the Protocol §四.(三) intent of "高信心 = 強且一致的證據".
    Returns 0.0 if there are no hits.
    """
    if not hits:
        return 0.0
    weights = [max(h.rerank_score, 0.0) for h in hits]
    total_weight = sum(weights)
    if total_weight <= 0:
        # All scores zero/negative — fall back to simple mean of raw scores
        return sum(h.rerank_score for h in hits) / len(hits)
    weighted_sum = sum(w * h.rerank_score for w, h in zip(weights, hits, strict=False))
    return weighted_sum / total_weight


class Bibliotheke:
    """RAG facade. Inject mocks via ``embedder`` / ``reranker`` for tests."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.embedder = embedder or get_embedder()
        self.reranker = reranker or get_reranker()

    async def search(
        self,
        query: str,
        top_k_dense: int = 20,
        top_k_final: int = 5,
    ) -> list[RagHit]:
        if not query.strip():
            return []

        query_vec = await self.embedder.embed_one(query)

        # Stage 1: pgvector cosine search
        async with AsyncSessionLocal() as session:
            cosine_distance = BibliothekeChunk.embedding.cosine_distance(query_vec)
            stmt = (
                select(
                    BibliothekeChunk.id,
                    BibliothekeChunk.source,
                    BibliothekeChunk.content,
                    cosine_distance.label("distance"),
                )
                .where(BibliothekeChunk.embedding.is_not(None))
                .order_by(cosine_distance)
                .limit(top_k_dense)
            )
            result = await session.execute(stmt)
            rows = result.all()

        if not rows:
            return []

        # Stage 2: rerank
        candidates = [r.content for r in rows]
        ranked = await self.reranker.rerank(query, candidates, top_k=top_k_final)

        hits: list[RagHit] = []
        for original_idx, rerank_score in ranked:
            row = rows[original_idx]
            cosine_sim = 1.0 - float(row.distance)
            hits.append(
                RagHit(
                    chunk_id=str(row.id),
                    source=row.source,
                    content=row.content,
                    cosine_similarity=cosine_sim,
                    rerank_score=rerank_score,
                )
            )
        return hits


@lru_cache(maxsize=1)
def get_bibliotheke() -> Bibliotheke:
    return Bibliotheke()
