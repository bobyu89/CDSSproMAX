"""Cases — read-only catalogue."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Case, Participant
from src.db.session import get_db
from src.routers.auth import get_current_participant

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseSummary(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    chief_complaint: str


class CaseDetail(CaseSummary):
    scenario_json: dict


@router.get("", response_model=list[CaseSummary])
async def list_cases(
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> list[CaseSummary]:
    rows = (await db.execute(select(Case).order_by(Case.code.asc()))).scalars().all()
    return [
        CaseSummary(
            id=c.id, code=c.code, title=c.title, chief_complaint=c.chief_complaint
        )
        for c in rows
    ]


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> CaseDetail:
    c = await db.scalar(select(Case).where(Case.id == case_id))
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="case not found")
    return CaseDetail(
        id=c.id,
        code=c.code,
        title=c.title,
        chief_complaint=c.chief_complaint,
        scenario_json=c.scenario_json,
    )
