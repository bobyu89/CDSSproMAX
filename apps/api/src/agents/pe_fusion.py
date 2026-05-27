"""PE score fusion — combines ArUco position evidence + V-Agent verdict.

For physical-examination rubric items we don't always have a transcript
(the student may have done the action silently). Instead we fuse:

  - Position correctness (markers)  → 80% weight (per Protocol design)
  - V-Agent technique score          → 20% weight (Gemini Vision)
  - V-Agent duration_adequate flag   → gating bonus / penalty

The result is a 0-5 score on the same scale as the LQQOPERA rubric
output, so it can flow into the same `duat_scores` table without
schema changes.

This module is invoked by the DUAT pipeline when the rubric item type
is "pe" and a PeObservation exists for the session.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.agents.v_agent import VAgentOutput

POSITION_WEIGHT = 0.8
TECHNIQUE_WEIGHT = 0.2
DURATION_BONUS = 0.5  # extra score (out of 5) when duration_adequate


@dataclass
class PeFusionResult:
    score_0_5: int
    raw_score: float
    position_correct: bool
    technique_score: float
    duration_adequate: bool
    rationale: str


def fuse(
    *,
    target_region: str,
    detected_regions: Iterable[str],
    v_agent: VAgentOutput | None,
) -> PeFusionResult:
    """Compute a 0-5 fused score for a single PE rubric item.

    Layer 1 contribution (position):
       correct → 1.0
       partial (region was in detected but not the primary one) → 0.5
       wrong → 0.0

    Layer 2 contribution (technique): direct V-Agent score in [0,1].
    """
    detected = set(detected_regions or [])
    if target_region in detected:
        position = 1.0
    elif detected:
        position = 0.5  # touched something, but not the right region
    else:
        position = 0.0

    technique = v_agent.technique_score if v_agent else 0.0
    duration_ok = v_agent.duration_adequate if v_agent else False

    weighted = POSITION_WEIGHT * position + TECHNIQUE_WEIGHT * technique
    # Bonus for adequate duration (clipped at 1.0 in the [0,1] domain)
    if duration_ok:
        weighted = min(1.0, weighted + 0.10)

    raw_score = weighted * 5  # [0, 5]
    final = round(raw_score)
    final = max(0, min(5, final))

    parts = [
        f"位置 {position:.0%}",
        f"技巧 {technique:.0%}",
        "持續時間達標" if duration_ok else "持續時間不足",
    ]
    rationale = " · ".join(parts)

    return PeFusionResult(
        score_0_5=final,
        raw_score=raw_score,
        position_correct=position >= 1.0,
        technique_score=technique,
        duration_adequate=duration_ok,
        rationale=rationale,
    )
