"""Admin router — dashboard, participant management, case visibility.

All endpoints require role 'admin' (gated via require_role from auth.py).
Wave 1 scope: aggregated stats, participant CRUD, case withheld toggle.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Case, DuatScore, Participant, Session
from src.db.session import get_db
from src.routers.auth import ParticipantPublic, require_role

router = APIRouter(prefix="/admin", tags=["admin"])

# Participant codes: leading uppercase letter, then 2-11 uppercase alphanumerics.
PARTICIPANT_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]{2,11}$")


# === Schemas ==============================================================


class ParticipantScoreSummary(BaseModel):
    participant_id: uuid.UUID
    participant_code: str
    name: str
    role: str
    session_count: int
    mean_score: float | None


class ParticipantSummaryWithLogin(ParticipantScoreSummary):
    # TODO: track real last_login_at — for now we return created_at as placeholder.
    last_login_at: datetime | None


class DashboardResponse(BaseModel):
    total_participants: int
    total_sessions: int
    mean_score: float | None  # avg of final_score across all duat_scores
    completion_rate: float  # fraction of sessions with ended_at IS NOT NULL
    per_participant_scores: list[ParticipantScoreSummary]


class CreateParticipantRequest(BaseModel):
    participant_code: str = Field(..., min_length=3, max_length=12)
    name: str = Field(..., min_length=1, max_length=120)
    role: Literal["student", "teacher", "admin"]
    password: str = Field(..., min_length=8)
    email: str | None = None

    @field_validator("participant_code")
    @classmethod
    def _check_code(cls, v: str) -> str:
        if not PARTICIPANT_CODE_RE.match(v):
            raise ValueError(
                "participant_code must be uppercase alphanumeric, 3-12 chars, starting with a letter"
            )
        return v


class WithheldUpdateRequest(BaseModel):
    is_withheld: bool


class CaseAdminOut(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    chief_complaint: str
    scenario_json: dict
    is_withheld: bool


# === Helpers ==============================================================


def _participant_scores_query(role_filter: str | None):
    """Build aggregation query: per-participant session count + mean final_score.

    LEFT JOIN sessions and duat_scores so participants with no sessions still show.
    mean_score is AVG over duat_scores.final_score (NULL-tolerant — AVG ignores NULLs).
    """
    stmt = (
        select(
            Participant.id,
            Participant.participant_code,
            Participant.name,
            Participant.role,
            Participant.created_at,
            func.count(func.distinct(Session.id)).label("session_count"),
            func.avg(DuatScore.final_score).label("mean_score"),
        )
        .select_from(Participant)
        .join(Session, Session.participant_id == Participant.id, isouter=True)
        .join(DuatScore, DuatScore.session_id == Session.id, isouter=True)
        .group_by(Participant.id)
        .order_by(Participant.participant_code.asc())
    )
    if role_filter is not None:
        stmt = stmt.where(Participant.role == role_filter)
    return stmt


# === Endpoints ============================================================


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(require_role("admin")),
) -> DashboardResponse:
    total_participants = (
        await db.scalar(select(func.count()).select_from(Participant))
    ) or 0
    total_sessions = (await db.scalar(select(func.count()).select_from(Session))) or 0
    completed_sessions = (
        await db.scalar(
            select(func.count())
            .select_from(Session)
            .where(Session.ended_at.is_not(None))
        )
    ) or 0
    mean_score = await db.scalar(select(func.avg(DuatScore.final_score)))

    completion_rate = (
        float(completed_sessions) / float(total_sessions) if total_sessions else 0.0
    )

    rows = (await db.execute(_participant_scores_query(role_filter="student"))).all()
    per_participant = [
        ParticipantScoreSummary(
            participant_id=row.id,
            participant_code=row.participant_code,
            name=row.name,
            role=row.role,
            session_count=int(row.session_count or 0),
            mean_score=float(row.mean_score) if row.mean_score is not None else None,
        )
        for row in rows
    ]

    return DashboardResponse(
        total_participants=int(total_participants),
        total_sessions=int(total_sessions),
        mean_score=float(mean_score) if mean_score is not None else None,
        completion_rate=completion_rate,
        per_participant_scores=per_participant,
    )


@router.get("/participants", response_model=list[ParticipantSummaryWithLogin])
async def list_participants(
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(require_role("admin")),
) -> list[ParticipantSummaryWithLogin]:
    rows = (await db.execute(_participant_scores_query(role_filter=None))).all()
    return [
        ParticipantSummaryWithLogin(
            participant_id=row.id,
            participant_code=row.participant_code,
            name=row.name,
            role=row.role,
            session_count=int(row.session_count or 0),
            mean_score=float(row.mean_score) if row.mean_score is not None else None,
            # TODO: track real last_login_at on the participant; using created_at as placeholder.
            last_login_at=row.created_at,
        )
        for row in rows
    ]


@router.post(
    "/participants",
    response_model=ParticipantPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_participant(
    payload: CreateParticipantRequest,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(require_role("admin")),
) -> ParticipantPublic:
    existing = await db.scalar(
        select(Participant).where(Participant.participant_code == payload.participant_code)
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"participant_code '{payload.participant_code}' already exists",
        )

    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    p = Participant(
        participant_code=payload.participant_code,
        name=payload.name,
        role=payload.role,
        email=payload.email,
        hashed_password=hashed,
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return ParticipantPublic(
        id=p.id,
        participant_code=p.participant_code,
        role=p.role,
        name=p.name,
    )


@router.patch("/cases/{case_id}/withheld", response_model=CaseAdminOut)
async def set_case_withheld(
    case_id: uuid.UUID,
    payload: WithheldUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(require_role("admin")),
) -> CaseAdminOut:
    """Toggle case visibility via scenario_json["meta"]["is_withheld"].

    NOTE: this lives inside scenario_json until we add a dedicated column,
    so queries that need to filter withheld cases must read the JSON.
    """
    case = await db.scalar(select(Case).where(Case.id == case_id))
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="case not found")

    # Pydantic mutated copies don't auto-flag JSON column dirty; rebuild + reassign.
    scenario = dict(case.scenario_json or {})
    meta = dict(scenario.get("meta") or {})
    meta["is_withheld"] = payload.is_withheld
    scenario["meta"] = meta
    case.scenario_json = scenario
    await db.flush()
    await db.refresh(case)

    return CaseAdminOut(
        id=case.id,
        code=case.code,
        title=case.title,
        chief_complaint=case.chief_complaint,
        scenario_json=case.scenario_json,
        is_withheld=bool(
            (case.scenario_json.get("meta") or {}).get("is_withheld", False)
        ),
    )
