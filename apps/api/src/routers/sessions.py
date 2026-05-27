"""Sessions router — list / create / fetch / advance phase."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.o_agent import OAgent, OAgentInput, Phase
from src.audit import AuditEventType, get_audit_logger
from src.db.models import Case, Participant, Session
from src.db.session import get_db
from src.routers.auth import get_current_participant

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    case_id: uuid.UUID
    mode: str  # "practice" | "exam"


class SessionOut(BaseModel):
    id: uuid.UUID
    participant_id: uuid.UUID
    case_id: uuid.UUID
    case_title: str | None = None
    mode: str
    phase: str
    started_at: datetime
    ended_at: datetime | None


class PhaseAdvanceOut(BaseModel):
    session_id: uuid.UUID
    new_phase: str
    time_limit_s: int | None


def _serialize(s: Session, case_title: str | None = None) -> SessionOut:
    return SessionOut(
        id=s.id,
        participant_id=s.participant_id,
        case_id=s.case_id,
        case_title=case_title,
        mode=s.mode,
        phase=s.phase,
        started_at=s.started_at,
        ended_at=s.ended_at,
    )


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> list[SessionOut]:
    """Teachers see all sessions; students see only their own."""
    stmt = select(Session, Case.title).join(Case, Case.id == Session.case_id)
    if participant.role == "student":
        stmt = stmt.where(Session.participant_id == participant.id)
    stmt = stmt.order_by(Session.started_at.desc())
    rows = (await db.execute(stmt)).all()
    return [_serialize(s, title) for s, title in rows]


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> SessionOut:
    case = await db.scalar(select(Case).where(Case.id == payload.case_id))
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="case not found")
    if payload.mode not in ("practice", "exam"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="mode must be practice|exam")

    session = Session(
        participant_id=participant.id,
        case_id=case.id,
        mode=payload.mode,
        phase=Phase.SCENARIO.value,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    await get_audit_logger().log(
        session_id=session.id,
        event_type=AuditEventType.SESSION_STARTED,
        payload={"case_id": str(case.id), "mode": payload.mode},
        db=db,
    )
    return _serialize(session, case.title)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> SessionOut:
    row = (
        await db.execute(
            select(Session, Case.title)
            .join(Case, Case.id == Session.case_id)
            .where(Session.id == session_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    session, title = row
    if participant.role == "student" and session.participant_id != participant.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your session")
    return _serialize(session, title)


@router.post("/{session_id}/advance", response_model=PhaseAdvanceOut)
async def advance_phase(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> PhaseAdvanceOut:
    session = await db.scalar(select(Session).where(Session.id == session_id))
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    if participant.role == "student" and session.participant_id != participant.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your session")

    o = OAgent()
    result = await o.run(
        OAgentInput(
            session_id=str(session.id),
            current_phase=Phase(session.phase),
            mode=session.mode,
        )
    )
    session.phase = result.next_phase.value
    await db.flush()
    return PhaseAdvanceOut(
        session_id=session.id,
        new_phase=result.next_phase.value,
        time_limit_s=result.time_limit_s,
    )
