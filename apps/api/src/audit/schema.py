"""Audit event Pydantic schemas — matches docs/architecture/audit-log-spec.md."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventType(str, Enum):
    SESSION_STARTED = "session.started"
    SESSION_COMPLETED = "session.completed"
    TRANSCRIPT_APPENDED = "transcript.appended"
    DUAT_E_EXTRACTED = "duat.e_extracted"
    DUAT_S_SCORED = "duat.s_scored"
    DUAT_A_REVIEWED = "duat.a_reviewed"
    DUAT_ARBITER_DECIDED = "duat.arbiter_decided"
    DUAT_SCORE_COMPUTED = "duat.score_computed"
    GRADER_ACTION = "grader.action"
    MDRIFT_ALERT = "mdrift.alert"
    # Wave 1.5 — vision layer events
    VISION_FRAME_DETECTED = "vision.frame_detected"
    VISION_REGION_TOUCHED = "vision.region_touched"
    VISION_V_AGENT_SCORED = "vision.v_agent_scored"
    # Wave 3 — physiological signals (HRV skeleton)
    PHYSIO_SAMPLES_INGESTED = "physio.samples_ingested"
    PHYSIO_HRV_COMPUTED = "physio.hrv_computed"
    PHYSIO_DEVICE_CONNECTED = "physio.device_connected"


class AuditPayload(BaseModel):
    """A single audit event — one line of JSONL."""

    model_config = ConfigDict(use_enum_values=True)

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    event_type: AuditEventType
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    payload: dict[str, Any] = Field(default_factory=dict)
    prompt_hash: str | None = None
    model_version: str | None = None
    rubric_item_id: str | None = None

    def as_jsonl(self) -> str:
        return self.model_dump_json()
