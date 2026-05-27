"""V-Agent — Vision Reviewer (Gemini 3.5 Flash, multimodal).

Per Protocol design:
  Position is verified by Layer 1 (ArUco markers). V-Agent grades ONLY
  operation quality (correct action, technique, duration) from keyframes.

Stub vs real:
  - If ``keyframes_b64`` is empty OR Google API key is missing, the
    agent returns a deterministic stub (so the pipeline can be exercised
    without GPU / camera / API key).
  - Otherwise it calls Gemini 3.5 Flash via the multimodal helper
    ``gemini_generate_json_multimodal`` in services/llm_clients.py.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import Agent, AgentResult
from src.config import get_settings
from src.services.llm_clients import (
    gemini_generate_json_multimodal,
    prompt_hash,
)

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


def _stub_output(payload: VAgentInput, model_id: str, reason: str) -> VAgentOutput:
    """Deterministic fallback used when we can't reach Gemini Vision."""
    intent_match = (
        payload.target_region in payload.detected_regions
        and bool(payload.detected_regions)
    )
    user_payload = (
        f"rubric_item_id={payload.rubric_item_id} "
        f"target={payload.target_action}@{payload.target_region} "
        f"detected={payload.detected_regions} "
        f"frames={len(payload.keyframes_b64)} "
        f"duration={payload.duration_seconds:.1f}s"
    )
    return VAgentOutput(
        agent_name="V-Agent",
        model_version=f"{model_id} (stub: {reason})",
        prompt_hash=prompt_hash(reason, user_payload),
        rubric_item_id=payload.rubric_item_id,
        action_correct=intent_match,
        technique_score=0.5 if intent_match else 0.0,
        duration_adequate=payload.duration_seconds >= 3.0,
        evidence_frames=[],
        notes=f"[stub:{reason}] V-Agent fallback — pipeline exercised without real vision call.",
    )


class VAgent(Agent[VAgentInput, VAgentOutput]):
    """Gemini 3.5 Flash multimodal vision reviewer."""

    name = "V-Agent"

    def __init__(self) -> None:
        settings = get_settings()
        self.model_id = settings.v_agent_model
        self._system_prompt = _load_system_prompt()

    async def run(self, payload: VAgentInput) -> VAgentOutput:
        settings = get_settings()

        # ── Decide whether to hit the real API ──────────────────────────
        if not payload.keyframes_b64:
            return _stub_output(payload, self.model_id, "no-keyframes")
        if not settings.google_api_key:
            return _stub_output(payload, self.model_id, "no-api-key")

        # ── Build the user prompt body ──────────────────────────────────
        user_prompt = (
            f"Rubric item id: {payload.rubric_item_id}\n"
            f"Target action: {payload.target_action}\n"
            f"Target region: {payload.target_region}\n"
            f"Student declared intent: {payload.student_intent or '(none)'}\n"
            f"Marker-detected regions during action: {payload.detected_regions}\n"
            f"Total duration: {payload.duration_seconds:.1f} seconds\n"
            f"Number of keyframes attached: {len(payload.keyframes_b64)} "
            "(in chronological order, ~equal time spacing)\n\n"
            "Judge action correctness, technique quality, and duration adequacy. "
            "Position is already verified by markers — do not regrade it.\n"
            "Reply with the JSON schema described in the system prompt."
        )

        # ── Call Gemini multimodal ──────────────────────────────────────
        try:
            data = await gemini_generate_json_multimodal(
                model=self.model_id,
                prompt=user_prompt,
                images_b64=payload.keyframes_b64,
                system_instruction=self._system_prompt,
            )
        except Exception as exc:  # pragma: no cover - network / API errors
            logger.warning("V-Agent Gemini call failed: %s", exc)
            return _stub_output(payload, self.model_id, f"api-error:{type(exc).__name__}")

        # ── Parse + clamp ───────────────────────────────────────────────
        evidence_raw = data.get("evidence_frames", []) or []
        evidence: list[int] = []
        for v in evidence_raw:
            try:
                evidence.append(int(v))
            except (TypeError, ValueError):
                continue

        return VAgentOutput(
            agent_name=self.name,
            model_version=self.model_id,
            prompt_hash=prompt_hash(self._system_prompt, user_prompt),
            rubric_item_id=payload.rubric_item_id,
            action_correct=bool(data.get("action_correct", False)),
            technique_score=_clamp_unit(data.get("technique_score", 0.0)),
            duration_adequate=bool(data.get("duration_adequate", False)),
            evidence_frames=evidence,
            notes=str(data.get("notes", ""))[:300],
        )
