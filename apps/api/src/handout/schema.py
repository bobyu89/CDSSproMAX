"""Pydantic schemas for the personal-handout API surface.

These types are the contract with the Next.js frontend. All user-visible
strings are 繁體中文 (the LLM generators are prompted accordingly).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ─── Building blocks ─────────────────────────────────────────────────────


class RadarPoint(BaseModel):
    dimension: str
    score: int
    max_score: int


class HrvTimePoint(BaseModel):
    timestamp_ms: int
    heart_rate: int | None = None
    rmssd_window: float | None = None


FlowZone = Literal["flow", "anxiety", "boredom", "apathy"]


class FlowPoint(BaseModel):
    timestamp_ms: int
    challenge: float = Field(..., ge=0.0, le=1.0)
    skill: float = Field(..., ge=0.0, le=1.0)
    zone: FlowZone


class MindMapNode(BaseModel):
    id: str
    label: str
    level: int
    parent_id: str | None = None
    kind: Literal["key_concept", "weakness", "action", "reference"]


class DiscussionPrompt(BaseModel):
    question: str
    why: str
    related_dimension: str | None = None


class StudyNoteSection(BaseModel):
    heading: str
    body: str
    citations: list[str] = Field(default_factory=list)


class SpacedRepetitionItem(BaseModel):
    topic: str
    dimension: str
    next_review_date: str  # ISO 8601 date
    iteration: int


# ─── Self-assessment ─────────────────────────────────────────────────────


class SelfAssessmentRequest(BaseModel):
    """Likert items: 1 (strongly disagree) – 5 (strongly agree)."""

    q_handled_stress: int | None = Field(None, ge=1, le=5)
    q_learned_from_mistakes: int | None = Field(None, ge=1, le=5)
    q_uncertainty_tolerance: int | None = Field(None, ge=1, le=5)
    q_recovery_speed: int | None = Field(None, ge=1, le=5)
    q_growth_orientation: int | None = Field(None, ge=1, le=5)
    narrative_strengths: str | None = None
    narrative_growth: str | None = None
    narrative_supervisor_question: str | None = None


class SelfAssessmentResponse(SelfAssessmentRequest):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    participant_id: uuid.UUID
    created_at: datetime


# ─── Confidence calibration ──────────────────────────────────────────────


class ConfidenceCalibrationRequest(BaseModel):
    predicted_score_0_5: int = Field(..., ge=0, le=5)
    predicted_at_phase: str = "review"


class ConfidenceCalibrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    participant_id: uuid.UUID
    created_at: datetime
    predicted_score_0_5: int
    predicted_at_phase: str
    actual_score_0_5: int | None = None
    calibration_gap: int | None = None  # predicted - actual


# ─── Aggregated handout ──────────────────────────────────────────────────


class HrvSummary(BaseModel):
    mean_hr: float
    sdnn: float
    rmssd: float
    state: str


class HandoutResponse(BaseModel):
    session_id: uuid.UUID
    participant_code: str
    case_title: str
    mode: str
    started_at: datetime
    ended_at: datetime | None = None

    total_score_0_5: int
    dimension_scores: dict[str, int]
    radar: list[RadarPoint]

    hrv_timeseries: list[HrvTimePoint] = Field(default_factory=list)
    hrv_summary: HrvSummary | None = None

    flow_curve: list[FlowPoint] = Field(default_factory=list)

    mindmap: list[MindMapNode] = Field(default_factory=list)
    study_notes: list[StudyNoteSection] = Field(default_factory=list)
    discussion_prompts: list[DiscussionPrompt] = Field(default_factory=list)
    spaced_repetition: list[SpacedRepetitionItem] = Field(default_factory=list)

    self_assessment: SelfAssessmentResponse | None = None
    confidence_calibration: ConfidenceCalibrationResponse | None = None
