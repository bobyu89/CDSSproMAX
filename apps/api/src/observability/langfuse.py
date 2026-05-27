"""Langfuse client + thin tracing helpers.

Wave 1 design choice: Langfuse is **optional** — if no public/secret key is
configured, calls become no-ops. This keeps tests and CI from needing a live
Langfuse instance, while production deploys get full traces.

We expose ``trace_span`` as the only entry point so individual Agents don't
import the Langfuse SDK directly.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from src.config import get_settings

try:
    from langfuse import Langfuse  # type: ignore[import-untyped]
except Exception:  # pragma: no cover — Langfuse SDK optional at import time
    Langfuse = None  # type: ignore[assignment, misc]


@lru_cache
def get_langfuse() -> Any | None:
    """Return a configured Langfuse client, or None if disabled.

    Disabled when:
      - the SDK is not installed, OR
      - public_key / secret_key are blank (default in .env.example)
    """
    settings = get_settings()
    if Langfuse is None:
        return None
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


@contextlib.contextmanager
def trace_span(
    name: str,
    *,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    input_data: Any = None,
) -> Iterator[Any]:
    """Context manager that emits a Langfuse span when configured, else no-op.

    Usage::

        with trace_span("e_agent.run", session_id=sid, input_data=payload) as span:
            result = await agent.run(payload)
            if span is not None:
                span.update(output=result.model_dump())
    """
    client = get_langfuse()
    if client is None:
        yield None
        return

    span = client.span(
        name=name,
        session_id=session_id,
        metadata=metadata or {},
        input=input_data,
    )
    try:
        yield span
    finally:
        span.end()
