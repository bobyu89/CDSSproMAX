"""ORM models for TICDSS Wave 1.

Schema deliberately mirrors Protocol §四 vocabulary: participants, sessions,
transcripts, duat_scores, audit_events, bibliotheke_chunks.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# === Participants =========================================================

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    participant_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum("student", "teacher", "admin", name="participant_role"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sessions: Mapped[list[Session]] = relationship(back_populates="participant")


# === Cases and Rubrics =====================================================

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rubrics: Mapped[list[Rubric]] = relationship(back_populates="case")


class Rubric(Base):
    __tablename__ = "rubrics"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        SAEnum("lqqopera", "pe", name="rubric_type"),
        nullable=False,
    )
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    items_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    case: Mapped[Case] = relationship(back_populates="rubrics")


# === Sessions and transcripts ==============================================

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    participant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    mode: Mapped[str] = mapped_column(
        SAEnum("practice", "exam", name="session_mode"), nullable=False
    )
    phase: Mapped[str] = mapped_column(
        SAEnum(
            "scenario", "inquiry", "transition", "examination", "diagnosis", "review",
            name="session_phase",
        ),
        nullable=False,
        default="scenario",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Wave-4 handout cache: stores the JSON-serialised HandoutResponse so that
    # repeated GETs don't re-burn Claude/Gemini quota. Cleared by the
    # /handout/regenerate endpoint.
    generated_handout_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    participant: Mapped[Participant] = relationship(back_populates="sessions")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    speaker: Mapped[str] = mapped_column(
        SAEnum("student", "patient", name="transcript_speaker"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ended_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# === DUAT scores ===========================================================

class DuatScore(Base):
    """One row per (session, rubric_item) — the unit of DUAT evaluation."""

    __tablename__ = "duat_scores"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    rubric_item_id: Mapped[str] = mapped_column(String(120), nullable=False)

    # E-Agent output
    e_evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    e_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # S-Agent output
    s_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    s_cot_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # A-Agent output
    a_advocate_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    a_advocate_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Arbiter
    arbiter_decision: Mapped[str | None] = mapped_column(
        SAEnum("accept", "flag", "force_human", name="arbiter_decision"), nullable=True
    )
    arbiter_confidence: Mapped[str | None] = mapped_column(
        SAEnum("high", "medium", "low", name="arbiter_confidence"), nullable=True
    )

    # Final human decision
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grader_action: Mapped[str | None] = mapped_column(
        SAEnum("accept", "modify", "reject", name="grader_action"), nullable=True
    )
    grader_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    grader_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("participants.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# === Audit log =============================================================

class AuditEvent(Base):
    """Indexed mirror of audit_logs/*.jsonl for SQL queries.

    The source of truth is the JSONL file (so M-Agent can replay history),
    but this table makes per-session queries fast.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    prompt_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# === Physio / HRV (Wave 3) =================================================


class PhysioSample(Base):
    """A single RR-interval sample from a heart-rate monitor (Polar H10, etc.).

    Wave 3: HRV is one of three signals (with prosody and expression) that the
    future Fusion Engine will combine to estimate learner cognitive state. For
    now we just persist the stream and expose summary endpoints; Fusion wiring
    lives outside this skeleton.

    timestamp_ms is epoch milliseconds (BigInteger) because consumer-grade
    chest straps fire several notifications per second and Postgres `Integer`
    overflows around year 2038 when you store ms. RR interval is in milliseconds.
    """

    __tablename__ = "physio_samples"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(String(120), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    r_to_r_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_flag: Mapped[str] = mapped_column(
        SAEnum("good", "noisy", "gap", name="physio_quality_flag"),
        nullable=False,
        default="good",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("physio_samples_session_ts_idx", "session_id", "timestamp_ms"),
    )


# === Handout (Wave 4) =====================================================


class SelfAssessment(Base):
    """反脆弱 self-assessment form filled by the student after a session.

    Five Likert-1-5 items + three narrative free-text fields. Stored once per
    (session, participant) — the POST endpoint upserts.
    """

    __tablename__ = "self_assessments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    q_handled_stress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    q_learned_from_mistakes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    q_uncertainty_tolerance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    q_recovery_speed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    q_growth_orientation: Mapped[int | None] = mapped_column(Integer, nullable=True)

    narrative_strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative_growth: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative_supervisor_question: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("self_assessments_session_idx", "session_id"),
    )


class ConfidenceCalibration(Base):
    """Pre-reveal score prediction → calibration-gap analysis.

    Student records their predicted-self-score *before* the DUAT results are
    shown. After scoring, ``actual_score_0_5`` and ``calibration_gap`` are
    computed and persisted; later reads return them as-is.
    """

    __tablename__ = "confidence_calibrations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    predicted_score_0_5: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_at_phase: Mapped[str] = mapped_column(String(40), nullable=False)
    actual_score_0_5: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calibration_gap: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("confidence_calibrations_session_idx", "session_id"),
    )


# === RAG: Bibliotheke ======================================================

class BibliothekeChunk(Base):
    """Knowledge base chunks for E-Agent RAG retrieval."""

    __tablename__ = "bibliotheke_chunks"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # BAAI/bge-base-zh-v1.5 = 768 dims
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
