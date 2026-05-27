"""Time-domain HRV metrics + state proxy."""

from __future__ import annotations

import math

import pytest

from src.physio.hrv import (
    TimeDomainSummary,
    mean_hr,
    pnn50,
    rmssd,
    sdnn,
    state_proxy_from_hrv,
    time_domain_summary,
)


# ─── Hand-computed reference ──────────────────────────────────────────────


# Five RR intervals chosen so SDNN/RMSSD/pNN50 all have clean expected values.
# RR:   [800, 810, 790, 805, 795]  (ms)
# mean = 800
# Successive diffs: [10, -20, 15, -10]; |diffs| → pNN50: 0 over-50 → 0%
# RMSSD = sqrt((100+400+225+100)/4) = sqrt(206.25) ≈ 14.361
# Sample-stddev (n-1 denom): variance = ((0+100+100+25+25)/4) = 62.5 → 7.906
REF_RR = [800, 810, 790, 805, 795]


def test_mean_hr_basic():
    # 800 ms → 75 bpm
    assert mean_hr(REF_RR) == pytest.approx(75.0, abs=0.05)


def test_sdnn_known_value():
    assert sdnn(REF_RR) == pytest.approx(math.sqrt(62.5), abs=1e-6)


def test_rmssd_known_value():
    assert rmssd(REF_RR) == pytest.approx(math.sqrt(206.25), abs=1e-6)


def test_pnn50_known_value():
    assert pnn50(REF_RR) == 0.0


def test_pnn50_counts_only_over_50ms():
    # Pairs: (800,860)=60, (860,800)=60, (800,900)=100  → all >50, 3/3 = 100%
    rr = [800, 860, 800, 900]
    assert pnn50(rr) == pytest.approx(100.0)


# ─── Sanity: variation vs steadiness ──────────────────────────────────────


def test_rmssd_higher_for_variable_input():
    steady = [800] * 20
    variable = [700, 900] * 10  # alternating ±100
    assert rmssd(variable) > rmssd(steady)
    assert sdnn(steady) == 0.0


# ─── Summary roundtrip ────────────────────────────────────────────────────


def test_time_domain_summary_shape():
    s = time_domain_summary(REF_RR)
    assert isinstance(s, TimeDomainSummary)
    assert s.n_samples == 5
    assert s.duration_s == pytest.approx(sum(REF_RR) / 1000.0)
    assert s.mean_hr == pytest.approx(75.0, abs=0.05)


# ─── Edge cases ───────────────────────────────────────────────────────────


def test_empty_raises():
    with pytest.raises(ValueError):
        sdnn([])
    with pytest.raises(ValueError):
        time_domain_summary([])


def test_gap_samples_filtered():
    # zeros and negatives are dropped
    s = time_domain_summary([800, 0, 810, -1, 790, 805, 795])
    assert s.n_samples == 5


# ─── State proxy ──────────────────────────────────────────────────────────


def _summary(*, mean_hr_v: float, sdnn_v: float, rmssd_v: float) -> TimeDomainSummary:
    return TimeDomainSummary(
        n_samples=60,
        duration_s=60.0,
        mean_hr=mean_hr_v,
        sdnn=sdnn_v,
        rmssd=rmssd_v,
        pnn50=0.0,
    )


def test_state_proxy_anxious_low_rmssd():
    assert state_proxy_from_hrv(_summary(mean_hr_v=85, sdnn_v=30, rmssd_v=12)) == "anxious"


def test_state_proxy_anxious_high_hr():
    assert state_proxy_from_hrv(_summary(mean_hr_v=110, sdnn_v=30, rmssd_v=30)) == "anxious"


def test_state_proxy_flow():
    assert state_proxy_from_hrv(_summary(mean_hr_v=70, sdnn_v=60, rmssd_v=50)) == "flow"


def test_state_proxy_low_engagement():
    assert state_proxy_from_hrv(_summary(mean_hr_v=60, sdnn_v=15, rmssd_v=25)) == "low_engagement"


def test_state_proxy_ambiguous():
    assert state_proxy_from_hrv(_summary(mean_hr_v=80, sdnn_v=30, rmssd_v=30)) == "ambiguous"
