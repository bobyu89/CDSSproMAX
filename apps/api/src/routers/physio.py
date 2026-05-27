"""Physiological signal endpoints — HRV skeleton (Wave 3).

  POST   /physio/sessions/{sid}/samples   — bulk ingest RR intervals (BLE batch)
  GET    /physio/sessions/{sid}/hrv       — windowed time-domain HRV summary
  GET    /physio/sessions/{sid}/timeseries — last N raw RR samples
  DELETE /physio/sessions/{sid}/samples   — admin wipe
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit import AuditEventType, get_audit_logger
from src.db.models import Participant, PhysioSample, Session as DbSession
from src.db.session import get_db
from src.physio import TimeDomainSummary, state_proxy_from_hrv, time_domain_summary
from src.routers.auth import get_current_participant, require_role

router = APIRouter(prefix="/physio", tags=["physio"])


# ─── Schemas ──────────────────────────────────────────────────────────────


class PhysioSampleIn(BaseModel):
    timestamp_ms: int = Field(..., description="Epoch milliseconds")
    r_to_r_ms: int = Field(..., description="RR interval (ms)")
    heart_rate: int | None = None
    quality_flag: str = "good"  # 'good' | 'noisy' | 'gap'


class IngestRequest(BaseModel):
    device_id: str
    samples: list[PhysioSampleIn]


class IngestResponse(BaseModel):
    inserted: int
    first_timestamp_ms: int | None = None
    last_timestamp_ms: int | None = None


class HrvWindowResponse(BaseModel):
    window_seconds: int
    end_timestamp_ms: int
    summary: TimeDomainSummary | None
    state_proxy: str  # 'flow' | 'anxious' | 'low_engagement' | 'ambiguous' | 'no_data'


class PhysioSampleOut(BaseModel):
    timestamp_ms: int
    r_to_r_ms: int
    heart_rate: int | None
    quality_flag: str


# ─── Routes ───────────────────────────────────────────────────────────────


async def _require_session(db: AsyncSession, session_id: uuid.UUID) -> DbSession:
    s = await db.scalar(select(DbSession).where(DbSession.id == session_id))
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")
    return s


@router.post(
    "/sessions/{session_id}/samples",
    response_model=IngestResponse,
)
async def ingest_samples(
    session_id: uuid.UUID,
    payload: IngestRequest,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> IngestResponse:
    """Bulk-ingest RR samples from a BLE chest-strap session.

    Polar H10 fires several HRM notifications per second (each containing
    1-3 RR intervals), so the frontend buffers ~5 s of samples and posts
    them as one batch.
    """
    await _require_session(db, session_id)

    if not payload.samples:
        return IngestResponse(inserted=0)

    rows = [
        PhysioSample(
            session_id=session_id,
            device_id=payload.device_id,
            timestamp_ms=s.timestamp_ms,
            r_to_r_ms=s.r_to_r_ms,
            heart_rate=s.heart_rate,
            quality_flag=s.quality_flag if s.quality_flag in {"good", "noisy", "gap"} else "good",
        )
        for s in payload.samples
    ]
    db.add_all(rows)
    await db.flush()

    timestamps = [s.timestamp_ms for s in payload.samples]
    first = min(timestamps)
    last = max(timestamps)

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.PHYSIO_SAMPLES_INGESTED,
        payload={
            "device_id": payload.device_id,
            "count": len(rows),
            "first_timestamp_ms": first,
            "last_timestamp_ms": last,
        },
        db=db,
    )

    return IngestResponse(
        inserted=len(rows),
        first_timestamp_ms=first,
        last_timestamp_ms=last,
    )


@router.get(
    "/sessions/{session_id}/hrv",
    response_model=HrvWindowResponse,
)
async def windowed_hrv(
    session_id: uuid.UUID,
    window_seconds: int = Query(60, ge=5, le=600),
    end_timestamp_ms: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> HrvWindowResponse:
    """Compute time-domain HRV over [end - window, end]."""
    await _require_session(db, session_id)

    end_ms = end_timestamp_ms if end_timestamp_ms is not None else int(time.time() * 1000)
    start_ms = end_ms - window_seconds * 1000

    rows = (
        await db.execute(
            select(PhysioSample)
            .where(
                PhysioSample.session_id == session_id,
                PhysioSample.timestamp_ms >= start_ms,
                PhysioSample.timestamp_ms <= end_ms,
            )
            .order_by(PhysioSample.timestamp_ms.asc())
        )
    ).scalars().all()

    rr = [r.r_to_r_ms for r in rows if r.quality_flag != "gap"]

    if not rr:
        return HrvWindowResponse(
            window_seconds=window_seconds,
            end_timestamp_ms=end_ms,
            summary=None,
            state_proxy="no_data",
        )

    summary = time_domain_summary(rr)
    state = state_proxy_from_hrv(summary)

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.PHYSIO_HRV_COMPUTED,
        payload={
            "window_seconds": window_seconds,
            "end_timestamp_ms": end_ms,
            "n_samples": summary.n_samples,
            "mean_hr": summary.mean_hr,
            "sdnn": summary.sdnn,
            "rmssd": summary.rmssd,
            "pnn50": summary.pnn50,
            "state_proxy": state,
        },
        db=db,
    )

    return HrvWindowResponse(
        window_seconds=window_seconds,
        end_timestamp_ms=end_ms,
        summary=summary,
        state_proxy=state,
    )


@router.get(
    "/sessions/{session_id}/timeseries",
    response_model=list[PhysioSampleOut],
)
async def timeseries(
    session_id: uuid.UUID,
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> list[PhysioSampleOut]:
    """Last N RR samples for chart rendering, chronological order."""
    await _require_session(db, session_id)

    rows = (
        await db.execute(
            select(PhysioSample)
            .where(PhysioSample.session_id == session_id)
            .order_by(PhysioSample.timestamp_ms.desc())
            .limit(limit)
        )
    ).scalars().all()

    rows_sorted = sorted(rows, key=lambda r: r.timestamp_ms)
    return [
        PhysioSampleOut(
            timestamp_ms=r.timestamp_ms,
            r_to_r_ms=r.r_to_r_ms,
            heart_rate=r.heart_rate,
            quality_flag=r.quality_flag,
        )
        for r in rows_sorted
    ]


@router.delete("/sessions/{session_id}/samples")
async def wipe_samples(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(require_role("admin")),
) -> dict[str, Any]:
    """Admin-only: remove all physio samples for a session (test cleanup)."""
    await _require_session(db, session_id)
    result = await db.execute(
        delete(PhysioSample).where(PhysioSample.session_id == session_id)
    )
    await db.flush()
    return {"status": "ok", "deleted": result.rowcount or 0}
