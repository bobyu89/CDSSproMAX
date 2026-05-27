"""AuditLogger — JSONL append + concurrency."""

import asyncio
import json
import uuid
from pathlib import Path

import pytest

from src.audit.logger import AuditLogger
from src.audit.schema import AuditEventType


pytestmark = pytest.mark.asyncio


async def test_log_appends_jsonl(tmp_path: Path):
    logger = AuditLogger(log_dir=tmp_path)
    session_id = uuid.uuid4()

    event = await logger.log(
        session_id=session_id,
        event_type=AuditEventType.DUAT_E_EXTRACTED,
        payload={"confidence": 0.85},
        rubric_item_id="lqqopera.location",
        model_version="gemini-3.5-flash",
    )

    log_file = tmp_path / f"{session_id}.jsonl"
    assert log_file.exists()

    line = log_file.read_text(encoding="utf-8").strip()
    data = json.loads(line)
    assert data["event_type"] == "duat.e_extracted"
    assert data["session_id"] == str(session_id)
    assert data["rubric_item_id"] == "lqqopera.location"
    assert data["payload"]["confidence"] == 0.85
    assert event.event_id is not None


async def test_concurrent_appends_dont_interleave(tmp_path: Path):
    """100 parallel writes — all 100 lines must be valid JSON, no partial writes."""
    logger = AuditLogger(log_dir=tmp_path)
    session_id = uuid.uuid4()

    async def write(i: int):
        await logger.log(
            session_id=session_id,
            event_type=AuditEventType.TRANSCRIPT_APPENDED,
            payload={"i": i},
        )

    await asyncio.gather(*(write(i) for i in range(100)))

    lines = (tmp_path / f"{session_id}.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 100
    ids_seen = set()
    for line in lines:
        data = json.loads(line)  # must parse — no torn writes
        ids_seen.add(data["payload"]["i"])
    assert ids_seen == set(range(100))


async def test_separate_sessions_get_separate_files(tmp_path: Path):
    logger = AuditLogger(log_dir=tmp_path)
    s1 = uuid.uuid4()
    s2 = uuid.uuid4()

    await logger.log(session_id=s1, event_type=AuditEventType.SESSION_STARTED)
    await logger.log(session_id=s2, event_type=AuditEventType.SESSION_STARTED)

    assert (tmp_path / f"{s1}.jsonl").exists()
    assert (tmp_path / f"{s2}.jsonl").exists()
