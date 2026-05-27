"""Pure-Python aggregation helpers (DB rows → Pydantic shapes).

No LLM calls — those live in ``generators.py``. No DB I/O either; callers
load ORM rows and pass them in. This keeps the unit tests offline-friendly
and lets the router call the helpers in parallel via ``asyncio.gather``.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from src.handout.schema import (
    FlowPoint,
    FlowZone,
    HrvTimePoint,
    RadarPoint,
    SpacedRepetitionItem,
)
from src.physio.hrv import rmssd as _rmssd_fn

# ─── Radar ────────────────────────────────────────────────────────────────


def _resolved_score(row: Any) -> int | None:
    """Prefer the grader's ``final_score``; fall back to ``s_score``."""
    score = getattr(row, "final_score", None)
    if score is not None:
        return int(score)
    s = getattr(row, "s_score", None)
    return int(s) if s is not None else None


def compute_radar(scores: Iterable[Any], rubric: Any) -> list[RadarPoint]:
    """Bucket DuatScore rows by rubric item → dimension, take the mean.

    Multiple rubric items can share a dimension (e.g. several PE manoeuvres
    in '心血管系統'); the radar shows the mean of those items.
    """
    items_by_id: dict[str, Any] = {it.id: it for it in rubric.items}

    bucket: dict[str, list[int]] = defaultdict(list)
    max_by_dim: dict[str, int] = {}

    for row in scores:
        item = items_by_id.get(row.rubric_item_id)
        if item is None:
            continue
        s = _resolved_score(row)
        if s is None:
            continue
        bucket[item.dimension].append(s)
        # Track the max possible for the dimension (use the largest max_score
        # among contributing items — they're usually all 5).
        max_by_dim[item.dimension] = max(
            max_by_dim.get(item.dimension, 0), int(item.max_score)
        )

    # Ensure every rubric dimension appears in the radar even if unscored —
    # the frontend draws a full polygon, missing axes look broken.
    out: list[RadarPoint] = []
    seen: set[str] = set()
    for it in rubric.items:
        if it.dimension in seen:
            continue
        seen.add(it.dimension)
        vals = bucket.get(it.dimension, [])
        mean = round(sum(vals) / len(vals)) if vals else 0
        out.append(
            RadarPoint(
                dimension=it.dimension,
                score=mean,
                max_score=max_by_dim.get(it.dimension, int(it.max_score)),
            )
        )
    return out


# ─── HRV timeseries ──────────────────────────────────────────────────────


def compute_hrv_timeseries(
    samples: list[Any], *, window_s: int = 30, step_s: int = 10
) -> list[HrvTimePoint]:
    """Sliding-window RMSSD over physio_samples, one point every ``step_s``.

    Each emitted point's ``rmssd_window`` is RMSSD over the preceding
    ``window_s`` seconds. ``heart_rate`` is the heart-rate of the sample
    sitting at the window's right edge.
    """
    if not samples:
        return []

    rows = sorted(samples, key=lambda r: r.timestamp_ms)
    start_ms = rows[0].timestamp_ms
    end_ms = rows[-1].timestamp_ms

    window_ms = window_s * 1000
    step_ms = step_s * 1000

    out: list[HrvTimePoint] = []
    cursor = start_ms + window_ms  # earliest point with a full window behind it
    if cursor > end_ms:
        # Not enough span for one full window — emit a single point at the end.
        cursor = end_ms

    while cursor <= end_ms:
        lo = cursor - window_ms
        rr = [
            r.r_to_r_ms
            for r in rows
            if lo <= r.timestamp_ms <= cursor
            and getattr(r, "quality_flag", "good") != "gap"
            and r.r_to_r_ms > 0
        ]
        # The sample at the right edge — for heart rate
        edge = max(
            (r for r in rows if r.timestamp_ms <= cursor),
            key=lambda r: r.timestamp_ms,
            default=None,
        )
        rmssd_v: float | None
        if len(rr) >= 2:
            rmssd_v = round(_rmssd_fn(rr), 2)
        else:
            rmssd_v = None
        out.append(
            HrvTimePoint(
                timestamp_ms=cursor,
                heart_rate=getattr(edge, "heart_rate", None) if edge else None,
                rmssd_window=rmssd_v,
            )
        )
        cursor += step_ms

    return out


# ─── Flow curve (Csikszentmihalyi 2×2) ────────────────────────────────────
#
# Classic Flow theory: psychological state is a function of perceived
# *challenge* against perceived *skill*, both normalised to [0, 1].
#
#   skill ≥ challenge + 0.2  → BOREDOM   (skills outstrip the task)
#   challenge ≥ skill + 0.2  → ANXIETY   (task outstrips skills)
#   both < 0.3               → APATHY    (low engagement, low demand)
#   otherwise                → FLOW      (balanced challenge vs skill)
#
# Csikszentmihalyi's eight-channel model splits the diagonal further, but for
# a teaching dashboard the 2×2 macro view is more legible. We treat the
# 0.2 gap as the "balance band" — wider than the original (which used the
# subject's mean as origin) because we have only a single OSCE session.

_BALANCE_BAND = 0.2
_LOW_THRESHOLD = 0.3


def classify_flow_zone(challenge: float, skill: float) -> FlowZone:
    if skill >= challenge + _BALANCE_BAND:
        return "boredom"
    if challenge >= skill + _BALANCE_BAND:
        return "anxiety"
    if challenge < _LOW_THRESHOLD and skill < _LOW_THRESHOLD:
        return "apathy"
    return "flow"


def _normalise_score(score: int | None, max_score: int) -> float:
    if score is None or max_score <= 0:
        return 0.0
    return max(0.0, min(1.0, score / max_score))


def compute_flow_curve(
    physio_samples: list[Any],
    scores: list[Any],
    rubric: Any,
    *,
    phase_changes: list[dict[str, Any]] | None = None,
    step_s: int = 30,
) -> list[FlowPoint]:
    """Build a flow-state timeline from rubric-item weights (challenge proxy)
    and rolling mean of recent scores (skill proxy).

    ``phase_changes`` is an optional list of ``{"timestamp_ms": int, ...}`` —
    if provided, we emit one additional FlowPoint at each phase boundary so
    the frontend can annotate transitions.
    """
    items_by_id: dict[str, Any] = {it.id: it for it in rubric.items}

    # Sort scores chronologically — the rolling mean walks forward in time.
    score_rows = sorted(
        (r for r in scores if _resolved_score(r) is not None),
        key=lambda r: getattr(r, "created_at", datetime.now(timezone.utc)),
    )

    if not score_rows and not physio_samples:
        return []

    # Time anchors
    if physio_samples:
        rows = sorted(physio_samples, key=lambda r: r.timestamp_ms)
        start_ms = rows[0].timestamp_ms
        end_ms = rows[-1].timestamp_ms
    else:
        # Fall back to score created_at timestamps converted to ms
        firsts = score_rows[0].created_at
        lasts = score_rows[-1].created_at
        start_ms = int(firsts.timestamp() * 1000)
        end_ms = max(int(lasts.timestamp() * 1000), start_ms + step_s * 1000)

    # Build emission timestamps: every ``step_s`` seconds + phase boundaries.
    step_ms = step_s * 1000
    times: list[int] = list(range(start_ms, end_ms + 1, step_ms))
    if phase_changes:
        for pc in phase_changes:
            ts = pc.get("timestamp_ms")
            if isinstance(ts, int) and start_ms <= ts <= end_ms and ts not in times:
                times.append(ts)
    times.sort()
    if not times:
        times = [start_ms]

    # Per emission, walk over score_rows up to and including that time.
    out: list[FlowPoint] = []
    for t in times:
        recent: list[tuple[float, float]] = []  # (skill_norm, weight)
        challenges: list[float] = []
        for r in score_rows:
            r_ts = int(getattr(r, "created_at", datetime.now(timezone.utc)).timestamp() * 1000)
            if r_ts > t:
                break
            item = items_by_id.get(r.rubric_item_id)
            max_score = int(item.max_score) if item else 5
            challenges.append(float(item.weight) if item else 0.6)
            recent.append((_normalise_score(_resolved_score(r), max_score), 1.0))

        # Skill proxy: rolling mean of normalised scores (last 5 items).
        if recent:
            tail = recent[-5:]
            skill = sum(s for s, _ in tail) / len(tail)
        else:
            skill = 0.0

        # Challenge proxy: mean weight of items attempted up to this point.
        if challenges:
            ch = sum(challenges[-5:]) / len(challenges[-5:])
        else:
            ch = 0.6  # neutral default
        ch = max(0.0, min(1.0, ch))

        out.append(
            FlowPoint(
                timestamp_ms=t,
                challenge=round(ch, 3),
                skill=round(skill, 3),
                zone=classify_flow_zone(ch, skill),
            )
        )
    return out


# ─── Spaced repetition (SM-2 lite) ───────────────────────────────────────


_SR_INTERVALS_DAYS = [1, 3, 7, 21]


def compute_spaced_repetition(
    weak_dimensions: list[str], *, now: datetime | None = None
) -> list[SpacedRepetitionItem]:
    """Schedule four review checkpoints per weak dimension at 1/3/7/21 days.

    We follow SM-2's exponential cadence but skip the easiness-factor since
    we only have one performance signal (the OSCE score).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    items: list[SpacedRepetitionItem] = []
    for dim in weak_dimensions:
        for i, days in enumerate(_SR_INTERVALS_DAYS, start=1):
            review = now + timedelta(days=days)
            items.append(
                SpacedRepetitionItem(
                    topic=f"複習：{dim}",
                    dimension=dim,
                    next_review_date=review.date().isoformat(),
                    iteration=i,
                )
            )
    return items


# ─── Helpers ──────────────────────────────────────────────────────────────


def weak_dimensions_from_radar(
    radar: list[RadarPoint], *, threshold_ratio: float = 0.6
) -> list[str]:
    """Return dimensions whose normalised score is below ``threshold_ratio``."""
    weak: list[str] = []
    for p in radar:
        if p.max_score <= 0:
            continue
        if p.score / p.max_score < threshold_ratio:
            weak.append(p.dimension)
    return weak
