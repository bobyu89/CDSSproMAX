"""Transcripts — append student/patient utterances during inquiry phase."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit import AuditEventType, get_audit_logger
from src.db.models import Participant, Session, Transcript
from src.db.session import get_db
from src.routers.auth import get_current_participant

router = APIRouter(prefix="/sessions/{session_id}/transcripts", tags=["transcripts"])


class TranscriptAppend(BaseModel):
    speaker: str  # "student" | "patient"
    text: str
    audio_path: str | None = None
    started_ms: int = 0
    ended_ms: int = 0


class TranscriptOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    speaker: str
    text: str
    audio_path: str | None
    started_ms: int
    ended_ms: int
    created_at: datetime


async def _own_or_403(db: AsyncSession, session_id: uuid.UUID, p: Participant) -> Session:
    s = await db.scalar(select(Session).where(Session.id == session_id))
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    if p.role == "student" and s.participant_id != p.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your session")
    return s


@router.post("", response_model=TranscriptOut, status_code=status.HTTP_201_CREATED)
async def append_transcript(
    session_id: uuid.UUID,
    payload: TranscriptAppend,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> TranscriptOut:
    await _own_or_403(db, session_id, participant)
    if payload.speaker not in ("student", "patient"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="speaker must be student|patient"
        )

    t = Transcript(
        session_id=session_id,
        speaker=payload.speaker,
        text=payload.text,
        audio_path=payload.audio_path,
        started_ms=payload.started_ms,
        ended_ms=payload.ended_ms,
    )
    db.add(t)
    await db.flush()
    await db.refresh(t)

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.TRANSCRIPT_APPENDED,
        payload={
            "speaker": payload.speaker,
            "text_length": len(payload.text),
            "transcript_id": str(t.id),
        },
        db=db,
    )

    return TranscriptOut(
        id=t.id,
        session_id=t.session_id,
        speaker=t.speaker,
        text=t.text,
        audio_path=t.audio_path,
        started_ms=t.started_ms,
        ended_ms=t.ended_ms,
        created_at=t.created_at,
    )


@router.get("", response_model=list[TranscriptOut])
async def list_transcripts(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> list[TranscriptOut]:
    await _own_or_403(db, session_id, participant)
    rows = (
        await db.execute(
            select(Transcript)
            .where(Transcript.session_id == session_id)
            .order_by(Transcript.created_at.asc())
        )
    ).scalars().all()
    return [
        TranscriptOut(
            id=t.id,
            session_id=t.session_id,
            speaker=t.speaker,
            text=t.text,
            audio_path=t.audio_path,
            started_ms=t.started_ms,
            ended_ms=t.ended_ms,
            created_at=t.created_at,
        )
        for t in rows
    ]
