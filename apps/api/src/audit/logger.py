"""Audit Logger — writes JSONL per session, mirrors to DB for indexing.

Design:
  - JSONL is the source of truth (immutable, append-only, M-Agent replayable).
  - DB row in `audit_events` is a denormalized index for SQL queries.
  - If DB write fails, JSONL write must still succeed — never lose audit data.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from functools import lru_cache
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.schema import AuditEventType, AuditPayload
from src.config import get_settings
from src.db.models import AuditEvent


class AuditLogger:
    """Per-session JSONL writer with optional DB indexing."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # One asyncio.Lock per session to serialize JSONL appends
        self._locks: dict[uuid.UUID, asyncio.Lock] = {}

    def _path(self, session_id: uuid.UUID) -> Path:
        return self.log_dir / f"{session_id}.jsonl"

    def _lock(self, session_id: uuid.UUID) -> asyncio.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    async def log(
        self,
        *,
        session_id: uuid.UUID,
        event_type: AuditEventType,
        payload: dict | None = None,
        rubric_item_id: str | None = None,
        prompt_hash: str | None = None,
        model_version: str | None = None,
        db: AsyncSession | None = None,
    ) -> AuditPayload:
        event = AuditPayload(
            session_id=session_id,
            event_type=event_type,
            payload=payload or {},
            rubric_item_id=rubric_item_id,
            prompt_hash=prompt_hash,
            model_version=model_version,
        )

        # 1) Append JSONL — source of truth
        async with self._lock(session_id):
            await asyncio.to_thread(self._append_jsonl, event)

        # 2) Mirror to DB index (best effort)
        if db is not None:
            try:
                db.add(
                    AuditEvent(
                        id=event.event_id,
                        session_id=session_id,
                        event_type=str(event.event_type),
                        event_json=json.loads(event.model_dump_json()),
                        prompt_hash=prompt_hash,
                        model_version=model_version,
                    )
                )
                await db.flush()
            except Exception as exc:  # noqa: BLE001
                # JSONL already written — DB miss is recoverable later by re-indexing
                # the source-of-truth file. Don't raise.
                print(f"[audit] DB index failed for {event.event_id}: {exc}")

        return event

    def _append_jsonl(self, event: AuditPayload) -> None:
        path = self._path(event.session_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(event.as_jsonl())
            f.write("\n")


@lru_cache
def get_audit_logger() -> AuditLogger:
    return AuditLogger(log_dir=get_settings().audit_log_dir)
