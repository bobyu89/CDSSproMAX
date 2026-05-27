"""Sentence-Transformers embedding wrapper for BAAI/bge-base-zh-v1.5.

The model is heavy to load (~400MB). We lazy-load on first encode and reuse
the same instance via the ``get_embedder`` singleton.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from src.config import get_settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768  # BAAI/bge-base-zh-v1.5


class Embedder:
    """Lazy wrapper around a sentence-transformers model."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or get_settings().embedding_model
        self._model: SentenceTransformer | None = None

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _encode_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        # normalize_embeddings=True so cosine similarity == dot product
        arr = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        vectors = arr.tolist()
        for v in vectors:
            assert len(v) == EMBEDDING_DIM, (
                f"Expected dim {EMBEDDING_DIM}, got {len(v)} from {self.model_name}"
            )
        return vectors

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._encode_sync, texts)

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder()
