"""DUAT scoring endpoints — trigger pipeline for one rubric item or all 8."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.e_agent import EAgentInput
from src.agents.pipeline import DuatItemResult, DuatPipeline
from src.db.models import DuatScore, Participant, Session, Transcript
from src.db.session import get_db
from src.routers.auth import get_current_participant
from src.rubric.loader import load_lqqopera_default

router = APIRouter(prefix="/sessions/{session_id}/duat", tags=["duat"])


class ScoreItemRequest(BaseModel):
    rubric_item_id: str
    case_context: str = ""


class ScoreItemResponse(BaseModel):
    rubric_item_id: str
    e_confidence: float
    s_score: int
    s_cot: str
    a_advocate_score: float
    a_advocate_report: str
    arbiter_action: str
    arbiter_confidence: str


class DuatScoreOut(BaseModel):
    id: uuid.UUID
    rubric_item_id: str
    e_confidence: float | None
    s_score: int | None
    a_advocate_score: float | None
    arbiter_decision: str | None
    arbiter_confidence: str | None
    final_score: int | None
    grader_action: str | None


async def _build_transcript_text(db: AsyncSession, session_id: uuid.UUID) -> str:
    rows = (
        await db.execute(
            select(Transcript)
            .where(Transcript.session_id == session_id)
            .order_by(Transcript.created_at.asc())
        )
    ).scalars().all()
    return "\n".join(f"({t.speaker}) {t.text}" for t in rows)


async def _persist(
    db: AsyncSession,
    session_id: uuid.UUID,
    result: DuatItemResult,
) -> DuatScore:
    row = DuatScore(
        session_id=session_id,
        rubric_item_id=result.rubric_item_id,
        e_evidence_json=result.evidence.as_bundle(),
        e_confidence=result.evidence.confidence,
        s_score=result.score.score,
        s_cot_json={
            "cot_reasoning": result.score.cot_reasoning,
            "cited_evidence_ids": result.score.cited_evidence_ids,
        },
        a_advocate_json={
            "advocate_report": result.advocate.advocate_report,
            "challenged_points": result.advocate.challenged_points,
        },
        a_advocate_score=result.advocate.advocate_score,
        arbiter_decision=result.arbiter.action,
        arbiter_confidence=result.arbiter.confidence,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


def _assert_can_score(participant: Participant, session: Session) -> None:
    """Students may trigger DUAT scoring only on their own sessions.
    Teachers and admins may score any session (for review / re-grading)."""
    if participant.role in ("teacher", "admin"):
        return
    if session.participant_id != participant.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="students may only score their own sessions",
        )


@router.post("/score-item", response_model=ScoreItemResponse)
async def score_item(
    session_id: uuid.UUID,
    payload: ScoreItemRequest,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> ScoreItemResponse:
    session = await db.scalar(select(Session).where(Session.id == session_id))
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    _assert_can_score(participant, session)

    rubric = load_lqqopera_default()
    item = next((it for it in rubric.items if it.id == payload.rubric_item_id), None)
    if item is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"rubric item '{payload.rubric_item_id}' not in LQQOPERA",
        )

    transcript_text = await _build_transcript_text(db, session_id)
    pipeline = DuatPipeline()
    result = await pipeline.score_item(
        session_id=session.id,
        rubric_item=item.model_dump(),
        evidence_inputs=EAgentInput(
            rubric_item_id=payload.rubric_item_id,
            transcript_text=transcript_text,
            case_context=payload.case_context,
        ),
    )

    await _persist(db, session_id, result)

    return ScoreItemResponse(
        rubric_item_id=result.rubric_item_id,
        e_confidence=result.evidence.confidence,
        s_score=result.score.score,
        s_cot=result.score.cot_reasoning,
        a_advocate_score=result.advocate.advocate_score,
        a_advocate_report=result.advocate.advocate_report,
        arbiter_action=result.arbiter.action,
        arbiter_confidence=result.arbiter.confidence,
    )


@router.post("/score-all-lqqopera", response_model=list[ScoreItemResponse])
async def score_all_lqqopera(
    session_id: uuid.UUID,
    payload: ScoreItemRequest | None = None,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> list[ScoreItemResponse]:
    """Score all 8 LQQOPERA dimensions in parallel."""
    session = await db.scalar(select(Session).where(Session.id == session_id))
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    _assert_can_score(participant, session)

    transcript_text = await _build_transcript_text(db, session_id)
    case_context = payload.case_context if payload else ""

    rubric = load_lqqopera_default()
    pipeline = DuatPipeline()

    async def _one(item: Any) -> DuatItemResult:
        return await pipeline.score_item(
            session_id=session.id,
            rubric_item=item.model_dump(),
            evidence_inputs=EAgentInput(
                rubric_item_id=item.id,
                transcript_text=transcript_text,
                case_context=case_context,
            ),
        )

    results = await asyncio.gather(*(_one(it) for it in rubric.items))

    out: list[ScoreItemResponse] = []
    for r in results:
        await _persist(db, session_id, r)
        out.append(
            ScoreItemResponse(
                rubric_item_id=r.rubric_item_id,
                e_confidence=r.evidence.confidence,
                s_score=r.score.score,
                s_cot=r.score.cot_reasoning,
                a_advocate_score=r.advocate.advocate_score,
                a_advocate_report=r.advocate.advocate_report,
                arbiter_action=r.arbiter.action,
                arbiter_confidence=r.arbiter.confidence,
            )
        )
    return out


@router.get("/scores", response_model=list[DuatScoreOut])
async def list_scores(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> list[DuatScoreOut]:
    session = await db.scalar(select(Session).where(Session.id == session_id))
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    if participant.role == "student" and session.participant_id != participant.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your session")

    rows = (
        await db.execute(
            select(DuatScore)
            .where(DuatScore.session_id == session_id)
            .order_by(DuatScore.created_at.asc())
        )
    ).scalars().all()
    return [
        DuatScoreOut(
            id=r.id,
            rubric_item_id=r.rubric_item_id,
            e_confidence=r.e_confidence,
            s_score=r.s_score,
            a_advocate_score=r.a_advocate_score,
            arbiter_decision=r.arbiter_decision,
            arbiter_confidence=r.arbiter_confidence,
            final_score=r.final_score,
            grader_action=r.grader_action,
        )
        for r in rows
    ]
