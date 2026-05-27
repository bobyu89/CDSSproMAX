"""Personal-handout endpoints (Wave 4).

  GET  /sessions/{sid}/handout
  POST /sessions/{sid}/handout/regenerate
  GET  /sessions/{sid}/self-assessment
  POST /sessions/{sid}/self-assessment
  GET  /sessions/{sid}/confidence-prediction
  POST /sessions/{sid}/confidence-prediction
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit import AuditEventType, get_audit_logger
from src.db.models import (
    Case,
    ConfidenceCalibration,
    DuatScore,
    Participant,
    SelfAssessment,
    Session as DbSession,
    Transcript,
)
from src.db.session import get_db
from src.handout.aggregator import (
    compute_flow_curve,
    compute_hrv_timeseries,
    compute_radar,
    compute_spaced_repetition,
    weak_dimensions_from_radar,
)
from src.handout.generators import (
    generate_discussion_prompts,
    generate_mindmap,
    generate_study_notes,
)
from src.handout.schema import (
    ConfidenceCalibrationRequest,
    ConfidenceCalibrationResponse,
    HandoutResponse,
    HrvSummary,
    SelfAssessmentRequest,
    SelfAssessmentResponse,
)
from src.db.models import PhysioSample
from src.physio.hrv import state_proxy_from_hrv, time_domain_summary
from src.routers.auth import get_current_participant, require_role
from src.rubric.loader import load_lqqopera_default

router = APIRouter(tags=["handout"])


# ─── Helpers ──────────────────────────────────────────────────────────────


async def _load_session(db: AsyncSession, session_id: uuid.UUID) -> DbSession:
    s = await db.scalar(select(DbSession).where(DbSession.id == session_id))
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    return s


def _check_session_access(session: DbSession, participant: Participant) -> None:
    if participant.role == "student" and session.participant_id != participant.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your session")


def _resolved_score(row: DuatScore) -> int | None:
    if row.final_score is not None:
        return int(row.final_score)
    if row.s_score is not None:
        return int(row.s_score)
    return None


async def _build_handout(
    db: AsyncSession,
    session: DbSession,
) -> HandoutResponse:
    """Aggregate + generate the full handout from scratch (no cache check)."""
    rubric = load_lqqopera_default()

    # Load all source rows in parallel where possible
    scores = (
        await db.execute(
            select(DuatScore).where(DuatScore.session_id == session.id)
        )
    ).scalars().all()
    physio_rows = (
        await db.execute(
            select(PhysioSample)
            .where(PhysioSample.session_id == session.id)
            .order_by(PhysioSample.timestamp_ms.asc())
        )
    ).scalars().all()
    self_assess = await db.scalar(
        select(SelfAssessment)
        .where(SelfAssessment.session_id == session.id)
        .order_by(SelfAssessment.created_at.desc())
    )
    calib = await db.scalar(
        select(ConfidenceCalibration)
        .where(ConfidenceCalibration.session_id == session.id)
        .order_by(ConfidenceCalibration.created_at.desc())
    )
    case = await db.scalar(select(Case).where(Case.id == session.case_id))
    participant = await db.scalar(
        select(Participant).where(Participant.id == session.participant_id)
    )
    transcripts = (
        await db.execute(
            select(Transcript)
            .where(Transcript.session_id == session.id)
            .order_by(Transcript.created_at.asc())
            .limit(40)
        )
    ).scalars().all()

    # Pure-Python aggregation
    radar = compute_radar(scores, rubric)
    dimension_scores = {p.dimension: p.score for p in radar}
    weak = weak_dimensions_from_radar(radar)

    total = (
        round(sum(p.score for p in radar) / len(radar)) if radar else 0
    )

    hrv_timeseries = compute_hrv_timeseries(list(physio_rows))
    hrv_summary: HrvSummary | None = None
    rr_all = [r.r_to_r_ms for r in physio_rows if r.quality_flag != "gap" and r.r_to_r_ms > 0]
    if len(rr_all) >= 2:
        tds = time_domain_summary(rr_all)
        hrv_summary = HrvSummary(
            mean_hr=tds.mean_hr,
            sdnn=tds.sdnn,
            rmssd=tds.rmssd,
            state=state_proxy_from_hrv(tds),
        )

    flow_curve = compute_flow_curve(list(physio_rows), list(scores), rubric)
    spaced_rep = compute_spaced_repetition(weak)

    transcript_excerpt = "\n".join(
        f"({t.speaker}) {t.text}" for t in transcripts
    )[:1200]

    # LLM-driven generators in parallel
    notes, mindmap, prompts = await asyncio.gather(
        generate_study_notes(
            case_title=case.title if case else "",
            weak_dimensions=weak,
            dimension_scores=dimension_scores,
            transcript_excerpt=transcript_excerpt,
        ),
        generate_mindmap(
            case_title=case.title if case else "",
            weak_dimensions=weak,
            dimension_scores=dimension_scores,
        ),
        generate_discussion_prompts(
            case_title=case.title if case else "",
            weak_dimensions=weak,
            dimension_scores=dimension_scores,
            narrative_growth=(self_assess.narrative_growth if self_assess else None),
        ),
    )

    self_assess_resp = (
        SelfAssessmentResponse.model_validate(self_assess) if self_assess else None
    )
    calib_resp = (
        ConfidenceCalibrationResponse.model_validate(calib) if calib else None
    )

    return HandoutResponse(
        session_id=session.id,
        participant_code=participant.participant_code if participant else "",
        case_title=case.title if case else "",
        mode=session.mode,
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_score_0_5=total,
        dimension_scores=dimension_scores,
        radar=radar,
        hrv_timeseries=hrv_timeseries,
        hrv_summary=hrv_summary,
        flow_curve=flow_curve,
        mindmap=mindmap,
        study_notes=notes,
        discussion_prompts=prompts,
        spaced_repetition=spaced_rep,
        self_assessment=self_assess_resp,
        confidence_calibration=calib_resp,
    )


def _serialise_cache(resp: HandoutResponse) -> dict[str, Any]:
    return json.loads(resp.model_dump_json())


# ─── Handout endpoints ────────────────────────────────────────────────────


@router.get(
    "/sessions/{session_id}/handout",
    response_model=HandoutResponse,
)
async def get_handout(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> HandoutResponse:
    session = await _load_session(db, session_id)
    _check_session_access(session, participant)

    # Cache hit — short-circuit and avoid burning LLM quota.
    if session.generated_handout_json:
        try:
            return HandoutResponse.model_validate(session.generated_handout_json)
        except Exception:
            # Stale schema → fall through and regenerate
            pass

    resp = await _build_handout(db, session)
    session.generated_handout_json = _serialise_cache(resp)
    await db.flush()

    await get_audit_logger().log(
        session_id=session.id,
        event_type=AuditEventType.HANDOUT_GENERATED,
        payload={
            "cached": False,
            "total_score_0_5": resp.total_score_0_5,
            "weak_dimension_count": len(
                [p for p in resp.radar if p.score / max(p.max_score, 1) < 0.6]
            ),
        },
        db=db,
    )
    return resp


@router.post(
    "/sessions/{session_id}/handout/regenerate",
    response_model=HandoutResponse,
)
async def regenerate_handout(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(require_role("teacher", "admin")),
) -> HandoutResponse:
    """Force-rebuild the handout, busting the cached JSON blob."""
    session = await _load_session(db, session_id)
    session.generated_handout_json = None
    await db.flush()

    resp = await _build_handout(db, session)
    session.generated_handout_json = _serialise_cache(resp)
    await db.flush()

    await get_audit_logger().log(
        session_id=session.id,
        event_type=AuditEventType.HANDOUT_GENERATED,
        payload={"cached": False, "forced": True},
        db=db,
    )
    return resp


# ─── Self-assessment endpoints ────────────────────────────────────────────


@router.get(
    "/sessions/{session_id}/self-assessment",
    response_model=SelfAssessmentResponse | None,
)
async def get_self_assessment(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> SelfAssessmentResponse | None:
    session = await _load_session(db, session_id)
    _check_session_access(session, participant)
    row = await db.scalar(
        select(SelfAssessment)
        .where(SelfAssessment.session_id == session_id)
        .order_by(SelfAssessment.created_at.desc())
    )
    if row is None:
        return None
    return SelfAssessmentResponse.model_validate(row)


@router.post(
    "/sessions/{session_id}/self-assessment",
    response_model=SelfAssessmentResponse,
)
async def upsert_self_assessment(
    session_id: uuid.UUID,
    payload: SelfAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> SelfAssessmentResponse:
    session = await _load_session(db, session_id)
    _check_session_access(session, participant)

    existing = await db.scalar(
        select(SelfAssessment)
        .where(
            SelfAssessment.session_id == session_id,
            SelfAssessment.participant_id == participant.id,
        )
    )
    if existing is None:
        row = SelfAssessment(
            session_id=session_id,
            participant_id=participant.id,
            **payload.model_dump(),
        )
        db.add(row)
    else:
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        row = existing
    await db.flush()
    await db.refresh(row)

    # Self-assessment changes invalidate the cached handout (because
    # narrative_growth feeds the discussion-prompt generator).
    session.generated_handout_json = None
    await db.flush()

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.SELF_ASSESSMENT_SUBMITTED,
        payload={"participant_id": str(participant.id)},
        db=db,
    )
    return SelfAssessmentResponse.model_validate(row)


# ─── Confidence calibration endpoints ─────────────────────────────────────


def _compute_actual_score(scores: list[DuatScore]) -> int | None:
    vals = [
        _resolved_score(r) for r in scores if _resolved_score(r) is not None
    ]
    if not vals:
        return None
    return round(sum(vals) / len(vals))  # type: ignore[arg-type]


@router.get(
    "/sessions/{session_id}/confidence-prediction",
    response_model=ConfidenceCalibrationResponse | None,
)
async def get_confidence(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> ConfidenceCalibrationResponse | None:
    session = await _load_session(db, session_id)
    _check_session_access(session, participant)

    row = await db.scalar(
        select(ConfidenceCalibration)
        .where(ConfidenceCalibration.session_id == session_id)
        .order_by(ConfidenceCalibration.created_at.desc())
    )
    if row is None:
        return None

    # Recompute actual_score / gap on read so it always reflects latest grading.
    scores = (
        await db.execute(
            select(DuatScore).where(DuatScore.session_id == session_id)
        )
    ).scalars().all()
    actual = _compute_actual_score(list(scores))
    if actual is not None:
        row.actual_score_0_5 = actual
        row.calibration_gap = int(row.predicted_score_0_5) - actual
        await db.flush()

    return ConfidenceCalibrationResponse.model_validate(row)


@router.post(
    "/sessions/{session_id}/confidence-prediction",
    response_model=ConfidenceCalibrationResponse,
)
async def record_confidence(
    session_id: uuid.UUID,
    payload: ConfidenceCalibrationRequest,
    db: AsyncSession = Depends(get_db),
    participant: Participant = Depends(get_current_participant),
) -> ConfidenceCalibrationResponse:
    session = await _load_session(db, session_id)
    _check_session_access(session, participant)

    scores = (
        await db.execute(
            select(DuatScore).where(DuatScore.session_id == session_id)
        )
    ).scalars().all()
    actual = _compute_actual_score(list(scores))
    gap = (
        payload.predicted_score_0_5 - actual if actual is not None else None
    )

    row = ConfidenceCalibration(
        session_id=session_id,
        participant_id=participant.id,
        predicted_score_0_5=payload.predicted_score_0_5,
        predicted_at_phase=payload.predicted_at_phase,
        actual_score_0_5=actual,
        calibration_gap=gap,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.CONFIDENCE_PREDICTED,
        payload={
            "predicted_score_0_5": payload.predicted_score_0_5,
            "predicted_at_phase": payload.predicted_at_phase,
            "actual_score_0_5": actual,
            "calibration_gap": gap,
        },
        db=db,
    )
    return ConfidenceCalibrationResponse.model_validate(row)
