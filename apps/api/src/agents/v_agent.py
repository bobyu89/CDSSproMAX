"""V-Agent — Vision Reviewer (Gemini 3.5 Flash Vision).

Wave 1.5 shell: input/output schemas + Gemini SDK wiring with stub mode.
Real keyframe upload (base64) happens here once the frontend is sending
camera bursts.

Position is already verified by Layer 1 (ArUco markers). V-Agent grades
ONLY the operation quality (correct action, technique, duration).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import Agent, AgentResult
from src.config import get_settings
from src.services.llm_clients import prompt_hash

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3].parent / "packages" / "shared-prompts"


def _load_system_prompt() -> str:
    path = _PROMPTS_DIR / "v_agent.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("v_agent.txt not found at %s — using minimal fallback", path)
        return (
            "You are the V-Agent. Judge PE operation quality from keyframes "
            'and reply with JSON {"action_correct": bool, '
            '"technique_score": float, "duration_adequate": bool, '
            '"evidence_frames": [int], "notes": str}.'
        )


class VAgentInput(BaseModel):
    """Inputs for one V-Agent call (single PE rubric item)."""

    rubric_item_id: str
    target_action: str  # e.g. "auscultation"
    target_region: str  # e.g. "right_lower_lung" (AnatomyRegion value)
    student_intent: str = ""  # what the student declared via ASR
    detected_regions: list[str] = Field(default_factory=list)  # from marker tracker
    keyframes_b64: list[str] = Field(default_factory=list)  # base64 JPEG/PNG
    duration_seconds: float = 0.0


class VAgentOutput(AgentResult):
    rubric_item_id: str
    action_correct: bool = False
    technique_score: float = 0.0  # 0-1
    duration_adequate: bool = False
    evidence_frames: list[int] = Field(default_factory=list)
    notes: str = ""


def _clamp_unit(value: Any) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


class VAgent(Agent[VAgentInput, VAgentOutput]):
    """Gemini 3.5 Flash multimodal vision reviewer.

    Wave 1.5 status: stub returns deterministic zero-confidence output.
    Real implementation lands when google-genai multimodal upload is
    wired in (next iteration).
    """

    name = "V-Agent"

    def __init__(self) -> None:
        settings = get_settings()
        self.model_id = settings.v_agent_model
        self._system_prompt = _load_system_prompt()
        # Flag to make stub vs real obvious in audit logs
        self._stub = True

    async def run(self, payload: VAgentInput) -> VAgentOutput:
        # ──────────────────────────────────────────────────────────────
        # Wave 1.5 STUB: returns deterministic output so the pipeline can
        # be exercised end-to-end (frontend sends keyframes → backend
        # writes audit + duat_scores → grading UI reads result).
        #
        # When ready to flip to real, replace the body below with:
        #   data = await gemini_generate_json(
        #       model=self.model_id,
        #       prompt=...,
        #       system_instruction=self._system_prompt,
        #       contents=[ ...frames as Part... ],
        #   )
        # google-genai multimodal API takes inline image bytes — see
        # https://ai.google.dev/gemini-api/docs/vision
        # ──────────────────────────────────────────────────────────────
        intent_match = (
            payload.target_region in payload.detected_regions
            and bool(payload.detected_regions)
        )
        user_payload = (
            f"rubric_item_id={payload.rubric_item_id} "
            f"target={payload.target_action}@{payload.target_region} "
            f"detected={payload.detected_regions} "
            f"intent={payload.student_intent!r} "
            f"frames={len(payload.keyframes_b64)} "
            f"duration={payload.duration_seconds:.1f}s"
        )

        return VAgentOutput(
            agent_name=self.name,
            model_version=f"{self.model_id} (stub)",
            prompt_hash=prompt_hash(self._system_prompt, user_payload),
            rubric_item_id=payload.rubric_item_id,
            action_correct=intent_match,
            technique_score=0.5 if intent_match else 0.0,
            duration_adequate=payload.duration_seconds >= 3.0,
            evidence_frames=[],
            notes="[stub] V-Agent not yet wired to Gemini Vision multimodal API",
        )
