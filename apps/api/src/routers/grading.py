"""Grading — teacher's Accept/Modify/Reject decision on a DUAT score row."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit import AuditEventType, get_audit_logger
from src.db.models import DuatScore, Participant
from src.db.session import get_db
from src.routers.auth import require_role

router = APIRouter(prefix="/sessions/{session_id}/scores", tags=["grading"])


class GradeRequest(BaseModel):
    action: str  # "accept" | "modify" | "reject"
    final_score: int | None = Field(default=None, ge=0, le=5)
    reason: str | None = None


class GradeResponse(BaseModel):
    score_id: uuid.UUID
    action: str
    final_score: int | None
    grader_id: uuid.UUID


@router.post("/{score_id}/grade", response_model=GradeResponse)
async def grade_item(
    session_id: uuid.UUID,
    score_id: uuid.UUID,
    payload: GradeRequest,
    db: AsyncSession = Depends(get_db),
    grader: Participant = Depends(require_role("teacher", "admin")),
) -> GradeResponse:
    if payload.action not in ("accept", "modify", "reject"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="action must be accept|modify|reject"
        )
    if payload.action == "modify" and payload.final_score is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="final_score required when action=modify",
        )
    if payload.action in ("modify", "reject") and not (payload.reason and payload.reason.strip()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="reason required when action=modify|reject",
        )

    row = await db.scalar(
        select(DuatScore).where(
            DuatScore.id == score_id,
            DuatScore.session_id == session_id,
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="duat score not found")

    if payload.action == "accept":
        row.final_score = row.s_score
    elif payload.action == "modify":
        row.final_score = payload.final_score
    else:  # reject
        row.final_score = None

    row.grader_action = payload.action
    row.grader_reason = payload.reason
    row.grader_id = grader.id
    await db.flush()

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.GRADER_ACTION,
        rubric_item_id=row.rubric_item_id,
        payload={
            "score_id": str(score_id),
            "action": payload.action,
            "final_score": row.final_score,
            "reason": payload.reason,
            "grader_id": str(grader.id),
        },
        db=db,
    )
    return GradeResponse(
        score_id=row.id,
        action=payload.action,
        final_score=row.final_score,
        grader_id=grader.id,
    )
