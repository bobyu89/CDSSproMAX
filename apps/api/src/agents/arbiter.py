"""Consensus Arbiter — Protocol §四.(三).

**Rule-based, NOT an LLM.** Pure function over three inputs:
  - E-Agent confidence (RAG cosine-weighted average, 0-1)
  - S-Agent score (0-5; informational, not used in routing decision)
  - A-Agent advocate score (0-1; how strongly A dissents)

Three-layer decision (per Protocol §四.(三) 表二):
  Layer 1: e_confidence ≥ 0.8 AND a_advocate_score < 0.3 → accept (high)
  Layer 2: e_confidence ≥ 0.5 AND a_advocate_score < 0.5 → flag (medium)
  Layer 3: otherwise                                      → force_human (low)

Thresholds (0.8 / 0.5 / 0.3 / 0.5) will be re-calibrated after Phase 1 Pilot
based on override-rate data. The `thresholds_version` field on the decision
makes that re-calibration auditable.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ArbiterAction = Literal["accept", "flag", "force_human"]
ArbiterConfidence = Literal["high", "medium", "low"]

# Threshold constants — version this string when calibration changes.
THRESHOLDS_VERSION = "v1.0"
E_CONF_HIGH = 0.80
E_CONF_MEDIUM = 0.50
A_ADVOCATE_LOW = 0.30
A_ADVOCATE_MEDIUM = 0.50


class ArbiterDecision(BaseModel):
    action: ArbiterAction
    confidence: ArbiterConfidence
    thresholds_version: str = Field(default=THRESHOLDS_VERSION)
    flag_reason: str | None = None


def arbitrate(
    e_confidence: float,
    s_score: int,  # noqa: ARG001 — kept for audit / future use
    a_advocate_score: float,
) -> ArbiterDecision:
    """Apply the three-layer consensus rule.

    Args:
        e_confidence: E-Agent RAG confidence in [0, 1].
        s_score: S-Agent's 0-5 score (recorded, not used for routing).
        a_advocate_score: A-Agent dissent strength in [0, 1].

    Returns:
        ArbiterDecision with action / confidence / optional flag_reason.

    Raises:
        ValueError: if either probability is outside [0, 1].
    """
    if not 0.0 <= e_confidence <= 1.0:
        raise ValueError(f"e_confidence must be in [0,1], got {e_confidence}")
    if not 0.0 <= a_advocate_score <= 1.0:
        raise ValueError(f"a_advocate_score must be in [0,1], got {a_advocate_score}")

    # Layer 1 — high E confidence AND low A dissent → accept.
    if e_confidence >= E_CONF_HIGH and a_advocate_score < A_ADVOCATE_LOW:
        return ArbiterDecision(action="accept", confidence="high")

    # Layer 2 — moderate E confidence AND moderate A dissent → flag.
    if e_confidence >= E_CONF_MEDIUM and a_advocate_score < A_ADVOCATE_MEDIUM:
        return ArbiterDecision(
            action="flag",
            confidence="medium",
            flag_reason="moderate_uncertainty",
        )

    # Layer 3 — low E confidence OR strong A dissent → human review required.
    return ArbiterDecision(
        action="force_human",
        confidence="low",
        flag_reason="low_confidence_or_strong_advocate",
    )
