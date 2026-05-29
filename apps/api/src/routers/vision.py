"""Vision endpoints — marker stream + V-Agent invocation.

Wave 1.5 shell:
  POST /vision/markers/detect      — single frame → ArUco detections
  POST /vision/markers/track       — append a sample to per-session tracker
  POST /vision/sessions/{sid}/v-agent  — run V-Agent on keyframes
  GET  /vision/anatomy-map         — list 15 markers + regions
  GET  /vision/health              — backend / opencv status
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.pipeline import apply_pe_fusion
from src.agents.v_agent import VAgent, VAgentInput
from src.audit import AuditEventType, get_audit_logger
from src.db.models import DuatScore, Participant, PeObservation, Session as DbSession
from src.db.session import get_db
from src.routers.auth import get_current_participant
from src.vision import (
    ANATOMY_MARKERS,
    AnatomyRegion,
    decode_frame,
    frame_dims,
    get_marker_detector,
)
from src.vision.marker_detector import DetectionResult, occluded_regions

router = APIRouter(prefix="/vision", tags=["vision"])


# ─────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────


class MarkerDetectionOut(BaseModel):
    aruco_id: int
    region: str | None  # AnatomyRegion value or None
    center_x: float
    center_y: float
    corners: list[list[float]]  # [[x,y], …]


class FrameDetectRequest(BaseModel):
    frame_b64: str  # data URL or raw base64 JPEG/PNG


class FrameDetectResponse(BaseModel):
    detections: list[MarkerDetectionOut]
    frame_w: int
    frame_h: int
    backend: str  # 'opencv' | 'stub'


class TrackSampleRequest(BaseModel):
    visible_marker_ids: list[int]
    timestamp: float | None = None  # seconds; defaults to server time


class TrackSampleResponse(BaseModel):
    touched_regions: list[str]  # AnatomyRegion values currently occluded ≥ threshold
    last_seen: dict[int, float]


class AnatomyMarkerOut(BaseModel):
    aruco_id: int
    region: str
    label_zh: str
    print_hint: str


class VAgentRequest(BaseModel):
    rubric_item_id: str
    target_action: str
    target_region: str
    student_intent: str = ""
    detected_regions: list[str] = Field(default_factory=list)
    keyframes_b64: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class VAgentResponse(BaseModel):
    rubric_item_id: str
    action_correct: bool
    technique_score: float
    duration_adequate: bool
    evidence_frames: list[int]
    notes: str
    model_version: str
    # Fused PE score (0-5) — what gets written to duat_scores
    fused_score: int | None = None
    fusion_rationale: str | None = None


# ─────────────────────────────────────────────────────────────────────────
# In-memory marker tracker (per session)
#
# Wave 1.5 keeps this in-process — Wave 2 will move to Redis when we need
# multi-worker tracking. Each session_id maps to {aruco_id: epoch_ts}.
# ─────────────────────────────────────────────────────────────────────────

_TRACKERS: dict[uuid.UUID, dict[int, float]] = {}
_OCCLUSION_THRESHOLD_S = 1.5
_MAX_TOUCH_WINDOW_S = 8.0  # upper bound — see marker_detector.occluded_regions


def _tracker(session_id: uuid.UUID) -> dict[int, float]:
    return _TRACKERS.setdefault(session_id, {})


# ─────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────


@router.get("/health")
async def vision_health() -> dict[str, Any]:
    det = get_marker_detector()
    available = det._ensure_loaded()  # noqa: SLF001 — internal flag is fine here
    return {
        "status": "ok",
        "opencv_available": available,
        "anatomy_markers": len(ANATOMY_MARKERS),
        "occlusion_threshold_s": _OCCLUSION_THRESHOLD_S,
    }


@router.get("/anatomy-map", response_model=list[AnatomyMarkerOut])
async def anatomy_map() -> list[AnatomyMarkerOut]:
    return [
        AnatomyMarkerOut(
            aruco_id=spec.aruco_id,
            region=spec.region.value,
            label_zh=spec.label_zh,
            print_hint=spec.print_hint,
        )
        for spec in ANATOMY_MARKERS.values()
    ]


@router.post("/markers/detect", response_model=FrameDetectResponse)
async def detect_markers(
    payload: FrameDetectRequest,
    _: Participant = Depends(get_current_participant),
) -> FrameDetectResponse:
    """Single-frame detection — used for live preview overlay in the UI."""
    frame = decode_frame(payload.frame_b64)
    dims = frame_dims(frame)
    if frame is None or dims is None:
        # Still return an empty result so the UI doesn't fail — backend
        # might not have OpenCV installed yet during Wave 1.5 dev.
        return FrameDetectResponse(detections=[], frame_w=0, frame_h=0, backend="stub")

    result: DetectionResult = get_marker_detector().detect(frame)
    h, w = dims
    return FrameDetectResponse(
        detections=[
            MarkerDetectionOut(
                aruco_id=d.aruco_id,
                region=d.region.value if d.region else None,
                center_x=d.center[0],
                center_y=d.center[1],
                corners=[[x, y] for x, y in d.corners],
            )
            for d in result.detections
        ],
        frame_w=result.frame_w or w,
        frame_h=result.frame_h or h,
        backend=result.backend,
    )


@router.post(
    "/sessions/{session_id}/track",
    response_model=TrackSampleResponse,
)
async def track_sample(
    session_id: uuid.UUID,
    payload: TrackSampleRequest,
    _: Participant = Depends(get_current_participant),
) -> TrackSampleResponse:
    """Append a tracking sample (which markers were visible this tick).

    Caller can either send the visible IDs (cheap — frontend already has
    them from /markers/detect), OR upload a frame to /markers/detect first.
    """
    now = float(payload.timestamp) if payload.timestamp is not None else time.time()
    tracker = _tracker(session_id)
    for aid in payload.visible_marker_ids:
        tracker[aid] = now

    touched = occluded_regions(
        tracker,
        now,
        occlusion_threshold_s=_OCCLUSION_THRESHOLD_S,
        max_touch_window_s=_MAX_TOUCH_WINDOW_S,
    )
    return TrackSampleResponse(
        touched_regions=[r.value for r in touched],
        last_seen={aid: ts for aid, ts in tracker.items()},
    )


@router.post(
    "/sessions/{session_id}/v-agent",
    response_model=VAgentResponse,
)
async def run_v_agent(
    session_id: uuid.UUID,
    payload: VAgentRequest,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> VAgentResponse:
    """Run V-Agent on a captured keyframe burst.

    On every call we:
      1. Validate the session exists.
      2. Run V-Agent (real Gemini Vision when keyframes + API key present;
         deterministic stub otherwise — see v_agent.py).
      3. Persist a PeObservation row (so /history can replay later).
      4. Emit a vision.v_agent_scored audit event.
    """
    from sqlalchemy import select

    db_session = await db.scalar(select(DbSession).where(DbSession.id == session_id))
    if db_session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")

    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id=payload.rubric_item_id,
            target_action=payload.target_action,
            target_region=payload.target_region,
            student_intent=payload.student_intent,
            detected_regions=payload.detected_regions,
            keyframes_b64=payload.keyframes_b64,
            duration_seconds=payload.duration_seconds,
        )
    )

    # Persist keyframes to object storage (Wave 1.7 — MinIO / S3). If
    # storage isn't configured, falls back to an empty list and the
    # observation is still written.
    keyframe_paths: list[str] = []
    if payload.keyframes_b64:
        try:
            from src.services.storage import get_storage_client

            storage = get_storage_client()
            keyframe_paths = await storage.put_keyframes(
                session_id=session_id,
                rubric_item_id=payload.rubric_item_id,
                images_b64=payload.keyframes_b64,
            )
        except Exception as exc:  # pragma: no cover — storage backend optional
            logger = __import__("logging").getLogger(__name__)
            logger.warning("keyframe storage failed: %s", exc)

    # Persist as PeObservation.
    obs = PeObservation(
        session_id=session_id,
        rubric_item_id=payload.rubric_item_id,
        student_intent=payload.student_intent or None,
        target_region=payload.target_region,
        detected_regions=list(payload.detected_regions),
        duration_seconds=payload.duration_seconds,
        v_action_correct=out.action_correct,
        v_technique_score=out.technique_score,
        v_duration_adequate=out.duration_adequate,
        v_notes=out.notes,
        keyframe_paths=keyframe_paths,
    )
    db.add(obs)
    await db.flush()

    # ── Fuse markers + V-Agent → DuatScore upsert
    # (single source of truth lives in agents/pipeline.py:apply_pe_fusion)
    fusion, arbiter_decision, arbiter_confidence, cot_json = apply_pe_fusion(
        target_region=payload.target_region,
        detected_regions=payload.detected_regions,
        v_agent=out,
    )

    from sqlalchemy import select as _select

    existing = await db.scalar(
        _select(DuatScore).where(
            DuatScore.session_id == session_id,
            DuatScore.rubric_item_id == payload.rubric_item_id,
        )
    )
    e_confidence = (
        1.0 if fusion.position_correct
        else (0.5 if payload.detected_regions else 0.0)
    )
    e_evidence = {
        "target_region": payload.target_region,
        "detected_regions": list(payload.detected_regions),
        "duration_seconds": payload.duration_seconds,
        "student_intent": payload.student_intent or None,
    }
    if existing is None:
        db.add(
            DuatScore(
                session_id=session_id,
                rubric_item_id=payload.rubric_item_id,
                e_evidence_json=e_evidence,
                e_confidence=e_confidence,
                s_score=fusion.score_0_5,
                s_cot_json=cot_json,
                a_advocate_score=0.0,
                arbiter_decision=arbiter_decision,
                arbiter_confidence=arbiter_confidence,
            )
        )
    else:
        existing.s_score = fusion.score_0_5
        existing.s_cot_json = cot_json
        existing.e_confidence = e_confidence
        existing.e_evidence_json = e_evidence
        existing.arbiter_decision = arbiter_decision
        existing.arbiter_confidence = arbiter_confidence
    await db.flush()

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.VISION_V_AGENT_SCORED,
        rubric_item_id=payload.rubric_item_id,
        prompt_hash=out.prompt_hash,
        model_version=out.model_version,
        payload={
            "observation_id": str(obs.id),
            "action_correct": out.action_correct,
            "technique_score": out.technique_score,
            "duration_adequate": out.duration_adequate,
            "n_keyframes": len(payload.keyframes_b64),
            "duration_seconds": payload.duration_seconds,
        },
        db=db,
    )

    return VAgentResponse(
        rubric_item_id=out.rubric_item_id,
        action_correct=out.action_correct,
        technique_score=out.technique_score,
        duration_adequate=out.duration_adequate,
        evidence_frames=out.evidence_frames,
        notes=out.notes,
        model_version=out.model_version,
        fused_score=fusion.score_0_5,
        fusion_rationale=fusion.rationale,
    )


@router.post(
    "/sessions/{session_id}/observations/{observation_id}/re-score",
    response_model=VAgentResponse,
)
async def re_score_observation(
    session_id: uuid.UUID,
    observation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> VAgentResponse:
    """Re-run V-Agent + fusion on an existing PeObservation.

    Useful when the V-Agent prompt or model is updated and we want to
    reconcile historical scores without asking the student to perform
    the action again. Keyframes are fetched from object storage (no
    re-upload from the browser).
    """
    from sqlalchemy import select

    obs = await db.scalar(
        select(PeObservation).where(
            PeObservation.id == observation_id,
            PeObservation.session_id == session_id,
        )
    )
    if obs is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="observation not found")

    # Fetch keyframes back from S3 if we have URLs.
    keyframes_b64: list[str] = []
    if obs.keyframe_paths:
        try:
            from src.services.storage import get_storage_client

            storage = get_storage_client()
            keyframes_b64 = await storage.fetch_keyframes_b64(list(obs.keyframe_paths))
        except Exception as exc:  # pragma: no cover - storage optional
            import logging
            logging.getLogger(__name__).warning(
                "re-score: fetch_keyframes_b64 failed: %s", exc
            )

    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id=obs.rubric_item_id,
            target_action="",  # routes have target_action only on initial call;
            # leave blank for re-score and let V-Agent infer from rubric / notes
            target_region=obs.target_region,
            student_intent=obs.student_intent or "",
            detected_regions=list(obs.detected_regions or []),
            keyframes_b64=keyframes_b64,
            duration_seconds=obs.duration_seconds,
        )
    )

    # Apply fusion + upsert DuatScore (same pipeline helper as live scoring)
    fusion, arbiter_decision, arbiter_confidence, cot_json = apply_pe_fusion(
        target_region=obs.target_region,
        detected_regions=obs.detected_regions or [],
        v_agent=out,
    )

    existing = await db.scalar(
        select(DuatScore).where(
            DuatScore.session_id == session_id,
            DuatScore.rubric_item_id == obs.rubric_item_id,
        )
    )
    e_confidence = (
        1.0 if fusion.position_correct
        else (0.5 if obs.detected_regions else 0.0)
    )
    e_evidence = {
        "target_region": obs.target_region,
        "detected_regions": list(obs.detected_regions or []),
        "duration_seconds": obs.duration_seconds,
        "student_intent": obs.student_intent,
        "re_scored_from_observation_id": str(obs.id),
    }
    if existing is None:
        db.add(
            DuatScore(
                session_id=session_id,
                rubric_item_id=obs.rubric_item_id,
                e_evidence_json=e_evidence,
                e_confidence=e_confidence,
                s_score=fusion.score_0_5,
                s_cot_json=cot_json,
                a_advocate_score=0.0,
                arbiter_decision=arbiter_decision,
                arbiter_confidence=arbiter_confidence,
            )
        )
    else:
        existing.s_score = fusion.score_0_5
        existing.s_cot_json = cot_json
        existing.e_confidence = e_confidence
        existing.e_evidence_json = e_evidence
        existing.arbiter_decision = arbiter_decision
        existing.arbiter_confidence = arbiter_confidence

    # Update the observation row to reflect the new verdict.
    obs.v_action_correct = out.action_correct
    obs.v_technique_score = out.technique_score
    obs.v_duration_adequate = out.duration_adequate
    obs.v_notes = out.notes

    await db.flush()

    await get_audit_logger().log(
        session_id=session_id,
        event_type=AuditEventType.VISION_V_AGENT_SCORED,
        rubric_item_id=obs.rubric_item_id,
        prompt_hash=out.prompt_hash,
        model_version=out.model_version,
        payload={
            "observation_id": str(obs.id),
            "re_score": True,
            "n_keyframes": len(keyframes_b64),
            "fused_score": fusion.score_0_5,
            "arbiter_decision": arbiter_decision,
        },
        db=db,
    )

    return VAgentResponse(
        rubric_item_id=out.rubric_item_id,
        action_correct=out.action_correct,
        technique_score=out.technique_score,
        duration_adequate=out.duration_adequate,
        evidence_frames=out.evidence_frames,
        notes=out.notes,
        model_version=out.model_version,
        fused_score=fusion.score_0_5,
        fusion_rationale=fusion.rationale,
    )


@router.get(
    "/sessions/{session_id}/observations",
    response_model=list[dict[str, Any]],
)
async def list_observations(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Participant = Depends(get_current_participant),
) -> list[dict[str, Any]]:
    """List all PE observations recorded for a session."""
    from sqlalchemy import select

    rows = (
        await db.execute(
            select(PeObservation)
            .where(PeObservation.session_id == session_id)
            .order_by(PeObservation.created_at.asc())
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "rubric_item_id": r.rubric_item_id,
            "student_intent": r.student_intent,
            "target_region": r.target_region,
            "detected_regions": r.detected_regions,
            "duration_seconds": r.duration_seconds,
            "v_action_correct": r.v_action_correct,
            "v_technique_score": r.v_technique_score,
            "v_duration_adequate": r.v_duration_adequate,
            "v_notes": r.v_notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.delete("/sessions/{session_id}/track")
async def reset_tracker(
    session_id: uuid.UUID,
    _: Participant = Depends(get_current_participant),
) -> dict[str, str]:
    """Wipe the in-memory marker tracker for a session (e.g. on station reset)."""
    _TRACKERS.pop(session_id, None)
    return {"status": "ok"}


# Defensive: don't let stale trackers grow without bound.
# Wave 2 should move to a TTL store; for now we expose a manual cleanup endpoint.
@router.delete("/markers/trackers")
async def reset_all_trackers(
    p: Participant = Depends(get_current_participant),
) -> dict[str, int]:
    if p.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="admin only")
    n = len(_TRACKERS)
    _TRACKERS.clear()
    return {"cleared": n}
