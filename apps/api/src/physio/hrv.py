"""Time-domain HRV metrics + a coarse state proxy.

Pure stdlib — HRV windows are short (typically 60–300 s ≈ a few hundred RR
intervals) so numpy/scipy is overkill.

References
----------
- Shaffer F, Ginsberg JP. *An Overview of Heart Rate Variability Metrics and
  Norms*. Front Public Health. 2017;5:258. doi:10.3389/fpubh.2017.00258.
- Task Force of the European Society of Cardiology and the North American
  Society of Pacing and Electrophysiology. *Heart rate variability: standards
  of measurement, physiological interpretation, and clinical use*.
  Circulation. 1996;93(5):1043-1065.
"""

from __future__ import annotations

import math
from typing import Iterable

from pydantic import BaseModel, Field


# ─── Filtering ────────────────────────────────────────────────────────────


def _clean(rr_ms: Iterable[int]) -> list[int]:
    """Drop non-positive samples; they're encoded as gaps upstream."""
    return [int(x) for x in rr_ms if x is not None and x > 0]


def _require(rr_ms: list[int]) -> None:
    if not rr_ms:
        raise ValueError("rr_ms is empty — need at least one valid RR sample")


# ─── Metrics ──────────────────────────────────────────────────────────────


def sdnn(rr_ms: list[int]) -> float:
    """Standard deviation of NN intervals (ms).

    SDNN reflects total autonomic variability over the recording window.
    Healthy resting adults: ~50 ms (1 min) to ~140 ms (24 h) (Shaffer 2017).
    """
    cleaned = _clean(rr_ms)
    _require(cleaned)
    if len(cleaned) < 2:
        return 0.0
    mean = sum(cleaned) / len(cleaned)
    var = sum((x - mean) ** 2 for x in cleaned) / (len(cleaned) - 1)
    return math.sqrt(var)


def rmssd(rr_ms: list[int]) -> float:
    """Root mean square of successive RR-interval differences (ms).

    RMSSD is the time-domain marker most closely tracking vagal (parasympathetic)
    tone — drops in RMSSD predict acute stress and cognitive load.
    Healthy resting short-term: ~19–75 ms (Shaffer 2017).
    """
    cleaned = _clean(rr_ms)
    _require(cleaned)
    if len(cleaned) < 2:
        return 0.0
    diffs = [cleaned[i + 1] - cleaned[i] for i in range(len(cleaned) - 1)]
    return math.sqrt(sum(d * d for d in diffs) / len(diffs))


def pnn50(rr_ms: list[int]) -> float:
    """% of successive pairs differing by >50 ms.

    Highly correlated with RMSSD; included for completeness.
    """
    cleaned = _clean(rr_ms)
    _require(cleaned)
    if len(cleaned) < 2:
        return 0.0
    diffs = [abs(cleaned[i + 1] - cleaned[i]) for i in range(len(cleaned) - 1)]
    over = sum(1 for d in diffs if d > 50)
    return 100.0 * over / len(diffs)


def mean_hr(rr_ms: list[int]) -> float:
    """Mean heart rate in bpm, derived from RR intervals: 60000 / mean(RR)."""
    cleaned = _clean(rr_ms)
    _require(cleaned)
    mean_rr = sum(cleaned) / len(cleaned)
    if mean_rr <= 0:
        return 0.0
    return 60000.0 / mean_rr


# ─── Summary ──────────────────────────────────────────────────────────────


class TimeDomainSummary(BaseModel):
    """Bundle of time-domain HRV metrics for a single analysis window."""

    n_samples: int = Field(..., description="Valid (positive) RR samples used")
    duration_s: float = Field(..., description="Sum of RR intervals / 1000")
    mean_hr: float
    sdnn: float
    rmssd: float
    pnn50: float


def time_domain_summary(rr_ms: list[int]) -> TimeDomainSummary:
    """Compute SDNN / RMSSD / pNN50 / mean HR over a window of RR intervals."""
    cleaned = _clean(rr_ms)
    _require(cleaned)
    duration_s = sum(cleaned) / 1000.0
    return TimeDomainSummary(
        n_samples=len(cleaned),
        duration_s=duration_s,
        mean_hr=mean_hr(cleaned),
        sdnn=sdnn(cleaned),
        rmssd=rmssd(cleaned),
        pnn50=pnn50(cleaned),
    )


# ─── State proxy ──────────────────────────────────────────────────────────
#
# Thresholds — coarse, *proxy only*, not diagnostic.
#
#   flow          : moderate-to-high vagal tone, calm engagement
#                   (RMSSD ≥ 40 ms AND HR ≤ 90)
#   anxious       : sympathetic dominance / stress
#                   (RMSSD < 20 ms — Shaffer 2017 lower bound — OR HR > 100)
#   low_engagement: very low variability with low arousal — possibly
#                   disengaged or fatigued (SDNN < 20 ms AND HR < 65)
#   ambiguous     : anything else; caller should treat as "no signal"
#
# Numbers loosely follow Shaffer & Ginsberg (2017) short-term resting norms;
# the cutoffs are intentionally conservative so the proxy errs toward
# 'ambiguous' rather than over-interpreting noise.

_RMSSD_STRESS = 20.0      # ms — below this implies vagal withdrawal
_RMSSD_FLOW = 40.0        # ms — comfortably within healthy resting band
_SDNN_LOW = 20.0          # ms — total variability floor
_HR_HIGH = 100.0          # bpm — tachycardic territory
_HR_FLOW_CEIL = 90.0      # bpm — relaxed engagement upper bound
_HR_LOW = 65.0            # bpm — low arousal lower bound


def state_proxy_from_hrv(summary: TimeDomainSummary) -> str:
    """Map an HRV summary to a coarse learner-state hint.

    Returns one of: 'flow' | 'anxious' | 'low_engagement' | 'ambiguous'.

    Important: this is a *single-channel proxy*. The Fusion Engine (future Wave 3
    work) will combine this with prosody + facial expression before any decision
    surfaces to a learner or grader.
    """
    if summary.rmssd < _RMSSD_STRESS or summary.mean_hr > _HR_HIGH:
        return "anxious"
    if summary.rmssd >= _RMSSD_FLOW and summary.mean_hr <= _HR_FLOW_CEIL:
        return "flow"
    if summary.sdnn < _SDNN_LOW and summary.mean_hr < _HR_LOW:
        return "low_engagement"
    return "ambiguous"
