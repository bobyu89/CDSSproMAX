"""Consensus Arbiter — exhaustive rule coverage."""

import pytest

from src.agents.arbiter import (
    A_ADVOCATE_LOW,
    A_ADVOCATE_MEDIUM,
    E_CONF_HIGH,
    E_CONF_MEDIUM,
    THRESHOLDS_VERSION,
    arbitrate,
)


# === Layer 1: accept (high confidence, no dissent) =========================

def test_layer1_high_confidence_no_dissent():
    d = arbitrate(e_confidence=0.95, s_score=4, a_advocate_score=0.05)
    assert d.action == "accept"
    assert d.confidence == "high"
    assert d.flag_reason is None


def test_layer1_exact_threshold_boundary():
    # e=0.80 (≥ HIGH), a=0.29 (< LOW) → accept
    d = arbitrate(e_confidence=E_CONF_HIGH, s_score=3, a_advocate_score=A_ADVOCATE_LOW - 0.01)
    assert d.action == "accept"


def test_layer1_a_advocate_exactly_at_threshold_falls_to_layer2():
    # a_advocate_score = 0.30 is NOT < 0.30, so Layer 1 fails;
    # but e=0.85 ≥ 0.5 and a=0.30 < 0.5 so Layer 2 applies.
    d = arbitrate(e_confidence=0.85, s_score=4, a_advocate_score=A_ADVOCATE_LOW)
    assert d.action == "flag"
    assert d.confidence == "medium"


# === Layer 2: flag (moderate) ==============================================

def test_layer2_moderate_confidence_moderate_dissent():
    d = arbitrate(e_confidence=0.65, s_score=3, a_advocate_score=0.40)
    assert d.action == "flag"
    assert d.confidence == "medium"
    assert d.flag_reason == "moderate_uncertainty"


def test_layer2_e_threshold_boundary():
    # e=0.50 (≥ MEDIUM), a=0.49 (< MEDIUM) → flag
    d = arbitrate(
        e_confidence=E_CONF_MEDIUM,
        s_score=2,
        a_advocate_score=A_ADVOCATE_MEDIUM - 0.01,
    )
    assert d.action == "flag"


def test_layer2_high_e_but_high_dissent_still_flag():
    # e=0.90 (high) but a=0.45 (moderate, not low) → drops out of Layer 1,
    # qualifies for Layer 2.
    d = arbitrate(e_confidence=0.90, s_score=5, a_advocate_score=0.45)
    assert d.action == "flag"
    assert d.confidence == "medium"


# === Layer 3: force_human (low confidence or strong dissent) ===============

def test_layer3_low_confidence():
    d = arbitrate(e_confidence=0.20, s_score=3, a_advocate_score=0.10)
    assert d.action == "force_human"
    assert d.confidence == "low"
    assert d.flag_reason == "low_confidence_or_strong_advocate"


def test_layer3_strong_dissent_overrides_high_e():
    # Even with very high E confidence, a strong A dissent forces human review.
    d = arbitrate(e_confidence=0.95, s_score=4, a_advocate_score=0.70)
    assert d.action == "force_human"


def test_layer3_exact_medium_boundary():
    # a_advocate_score = 0.50 is NOT < 0.50, fails Layer 2 → Layer 3.
    d = arbitrate(e_confidence=0.80, s_score=3, a_advocate_score=A_ADVOCATE_MEDIUM)
    assert d.action == "force_human"


def test_layer3_e_just_below_medium():
    d = arbitrate(
        e_confidence=E_CONF_MEDIUM - 0.01,
        s_score=2,
        a_advocate_score=0.10,
    )
    assert d.action == "force_human"


# === Input validation ======================================================

@pytest.mark.parametrize("bad", [-0.01, 1.01, -1.0, 1.5])
def test_invalid_e_confidence_raises(bad):
    with pytest.raises(ValueError, match="e_confidence"):
        arbitrate(e_confidence=bad, s_score=3, a_advocate_score=0.1)


@pytest.mark.parametrize("bad", [-0.01, 1.01, -1.0, 1.5])
def test_invalid_a_advocate_raises(bad):
    with pytest.raises(ValueError, match="a_advocate_score"):
        arbitrate(e_confidence=0.5, s_score=3, a_advocate_score=bad)


# === Metadata ==============================================================

def test_thresholds_version_recorded():
    d = arbitrate(e_confidence=0.9, s_score=4, a_advocate_score=0.1)
    assert d.thresholds_version == THRESHOLDS_VERSION


def test_decision_is_pydantic_serializable():
    d = arbitrate(e_confidence=0.9, s_score=4, a_advocate_score=0.1)
    payload = d.model_dump()
    assert payload["action"] == "accept"
    assert payload["confidence"] == "high"
    assert "thresholds_version" in payload
