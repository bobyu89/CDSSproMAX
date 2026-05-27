"""RAG (Retrieval-Augmented Generation) subsystem for E-Agent.

Per Protocol §四 / docs/architecture/duat-pipeline.md, ONLY the E-Agent
accesses this module. Two-stage retrieval: pgvector cosine dense → CrossEncoder rerank.
"""

from src.rag.bibliotheke import Bibliotheke, RagHit, confidence_from_hits, get_bibliotheke
from src.rag.embedder import Embedder, get_embedder
from src.rag.reranker import Reranker, get_reranker

__all__ = [
    "Bibliotheke",
    "RagHit",
    "Embedder",
    "Reranker",
    "confidence_from_hits",
    "get_bibliotheke",
    "get_embedder",
    "get_reranker",
]
