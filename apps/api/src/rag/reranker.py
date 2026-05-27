"""CrossEncoder reranker wrapping BAAI/bge-reranker-base.

Stage 2 of the retrieval pipeline — rescores the top_k_dense candidates
returned by pgvector against the query, then keeps top_k.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from src.config import get_settings

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class Reranker:
    """Lazy CrossEncoder wrapper."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or get_settings().reranker_model
        self._model: CrossEncoder | None = None

    def _load(self) -> CrossEncoder:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            logger.info("Loading reranker model: %s", self.model_name)
            self._model = CrossEncoder(self.model_name)
        return self._model

    def _rerank_sync(
        self, query: str, candidates: list[str], top_k: int
    ) -> list[tuple[int, float]]:
        model = self._load()
        pairs = [(query, c) for c in candidates]
        scores = model.predict(pairs)
        indexed: list[tuple[int, float]] = [(i, float(s)) for i, s in enumerate(scores)]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed[:top_k]

    async def rerank(
        self, query: str, candidates: list[str], top_k: int = 5
    ) -> list[tuple[int, float]]:
        if not candidates:
            return []
        return await asyncio.to_thread(self._rerank_sync, query, candidates, top_k)


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return Reranker()
