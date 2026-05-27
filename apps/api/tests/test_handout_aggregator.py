"""Aggregator unit tests — pure-Python, no DB / no LLM."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.handout.aggregator import (
    classify_flow_zone,
    compute_flow_curve,
    compute_hrv_timeseries,
    compute_radar,
    compute_spaced_repetition,
    weak_dimensions_from_radar,
)
from src.handout.schema import RadarPoint
from src.rubric.schema import Rubric, RubricCriterion, RubricItem


# ─── Fixtures ────────────────────────────────────────────────────────────


def _rubric(items: list[tuple[str, str, float]]) -> Rubric:
    """items = [(id, dimension, weight), ...]"""
    return Rubric(
        rubric_id="test.rubric",
        type="lqqopera",
        version="1.0",
        items=[
            RubricItem(
                id=i,
                dimension=d,
                weight=w,
                max_score=5,
                criteria=[
                    RubricCriterion(level=5, descriptor="x"),
                    RubricCriterion(level=0, descriptor="x"),
                ],
            )
            for i, d, w in items
        ],
    )


def _score_row(rid: str, *, s_score: int | None = None, final_score: int | None = None,
               created_at: datetime | None = None):
    return SimpleNamespace(
        rubric_item_id=rid,
        s_score=s_score,
        final_score=final_score,
        created_at=created_at or datetime(2026, 5, 28, 10, 0, 0, tzinfo=timezone.utc),
    )


def _physio_row(ts_ms: int, rr: int, hr: int | None = 75, q: str = "good"):
    return SimpleNamespace(
        timestamp_ms=ts_ms, r_to_r_ms=rr, heart_rate=hr, quality_flag=q
    )


# ─── Radar ────────────────────────────────────────────────────────────────


def test_radar_buckets_multiple_items_into_one_dimension():
    rubric = _rubric([
        ("pe.cardio.ausc", "心血管系統", 1.0),
        ("pe.cardio.palp", "心血管系統", 0.8),
        ("pe.lung.ausc", "呼吸系統", 1.0),
    ])
    rows = [
        _score_row("pe.cardio.ausc", s_score=4),
        _score_row("pe.cardio.palp", s_score=2),
        _score_row("pe.lung.ausc", s_score=5),
    ]
    radar = compute_radar(rows, rubric)
    by_dim = {p.dimension: p.score for p in radar}
    assert by_dim["心血管系統"] == 3  # mean(4,2) = 3
    assert by_dim["呼吸系統"] == 5


def test_radar_prefers_final_score_over_s_score():
    rubric = _rubric([("lqq.l", "Location", 1.0)])
    rows = [_score_row("lqq.l", s_score=2, final_score=4)]
    radar = compute_radar(rows, rubric)
    assert radar[0].score == 4


def test_radar_emits_zero_for_unscored_dimension():
    rubric = _rubric([("lqq.l", "Location", 1.0), ("lqq.q", "Quality", 1.0)])
    radar = compute_radar([_score_row("lqq.l", s_score=3)], rubric)
    by_dim = {p.dimension: p.score for p in radar}
    assert by_dim["Quality"] == 0


def test_weak_dimensions_threshold():
    radar = [
        RadarPoint(dimension="A", score=2, max_score=5),  # 0.4 → weak
        RadarPoint(dimension="B", score=4, max_score=5),  # 0.8 → strong
        RadarPoint(dimension="C", score=3, max_score=5),  # 0.6 → not weak
    ]
    assert weak_dimensions_from_radar(radar, threshold_ratio=0.6) == ["A"]


# ─── HRV timeseries ──────────────────────────────────────────────────────


def test_hrv_timeseries_empty_input():
    assert compute_hrv_timeseries([]) == []


def test_hrv_timeseries_sliding_window():
    # 60 seconds of samples at 1 Hz, RR=800ms
    base = 1_700_000_000_000
    samples = [_physio_row(base + i * 1000, 800) for i in range(60)]
    pts = compute_hrv_timeseries(samples, window_s=30, step_s=10)
    assert len(pts) >= 3
    # First point should sit at base + 30s (window_ms)
    assert pts[0].timestamp_ms == base + 30_000
    # RMSSD over constant RR is 0
    assert pts[0].rmssd_window == 0.0


def test_hrv_timeseries_skips_gap_samples():
    base = 1_700_000_000_000
    samples = [
        _physio_row(base, 800),
        _physio_row(base + 1000, 800, q="gap"),
        _physio_row(base + 2000, 810),
    ]
    pts = compute_hrv_timeseries(samples, window_s=30, step_s=10)
    # With only 2 valid samples spanning 2s the window is partial but RMSSD computable
    assert pts  # at least one point


# ─── Flow zone ────────────────────────────────────────────────────────────


def test_flow_zone_classification_csikszentmihalyi_2x2():
    # Balanced mid → flow
    assert classify_flow_zone(0.6, 0.6) == "flow"
    # High challenge, low skill → anxiety
    assert classify_flow_zone(0.9, 0.2) == "anxiety"
    # Low challenge, high skill → boredom
    assert classify_flow_zone(0.2, 0.9) == "boredom"
    # Both low → apathy
    assert classify_flow_zone(0.1, 0.1) == "apathy"
    # Within balance band but both above low threshold → flow
    assert classify_flow_zone(0.5, 0.55) == "flow"


def test_flow_curve_emits_points():
    rubric = _rubric([("lqq.l", "Location", 0.6)])
    base = datetime(2026, 5, 28, 10, 0, 0, tzinfo=timezone.utc)
    base_ms = int(base.timestamp() * 1000)
    samples = [_physio_row(base_ms + i * 1000, 800) for i in range(120)]
    scores = [
        _score_row("lqq.l", s_score=3, created_at=base + timedelta(seconds=10)),
        _score_row("lqq.l", s_score=4, created_at=base + timedelta(seconds=60)),
    ]
    curve = compute_flow_curve(samples, scores, rubric, step_s=30)
    assert len(curve) >= 3
    for p in curve:
        assert 0.0 <= p.challenge <= 1.0
        assert 0.0 <= p.skill <= 1.0
        assert p.zone in {"flow", "anxiety", "boredom", "apathy"}


# ─── Spaced repetition ───────────────────────────────────────────────────


def test_spaced_repetition_cadence_per_dim():
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    items = compute_spaced_repetition(["Quality", "Onset"], now=now)
    # 4 reviews × 2 dimensions
    assert len(items) == 8
    quality_items = [i for i in items if i.dimension == "Quality"]
    assert [i.iteration for i in quality_items] == [1, 2, 3, 4]
    # First review is 1 day out
    assert quality_items[0].next_review_date == "2026-05-29"
    # Final review at 21 days
    assert quality_items[-1].next_review_date == "2026-06-18"


def test_spaced_repetition_empty():
    assert compute_spaced_repetition([]) == []
