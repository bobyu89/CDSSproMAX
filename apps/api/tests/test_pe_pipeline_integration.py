"""Pipeline-level PE fusion routing — single source of truth tests."""

import pytest

from src.agents.pipeline import (
    apply_pe_fusion,
    derive_arbiter_for_pe,
    is_pe_rubric_item,
)
from src.agents.v_agent import VAgentOutput


def _v(action=True, technique=0.8, duration=True):
    return VAgentOutput(
        agent_name="V-Agent",
        model_version="gemini-3.5-flash",
        rubric_item_id="pe.x",
        action_correct=action,
        technique_score=technique,
        duration_adequate=duration,
        evidence_frames=[],
        notes="",
    )


def test_is_pe_rubric_item_detects_body_region():
    assert is_pe_rubric_item({"id": "pe.x", "body_region": "pmi"}) is True
    assert is_pe_rubric_item({"id": "pe.x", "expected_action": "auscultation"}) is True
    assert is_pe_rubric_item({"id": "lqqopera.location", "dimension": "Location"}) is False


def test_derive_arbiter_accept_when_both_correct():
    decision, conf = derive_arbiter_for_pe(
        position_correct=True, action_correct=True, has_any_detection=True
    )
    assert decision == "accept"
    assert conf == "high"


def test_derive_arbiter_flag_when_wrong_position_but_some_detection():
    decision, conf = derive_arbiter_for_pe(
        position_correct=False, action_correct=True, has_any_detection=True
    )
    assert decision == "flag"
    assert conf == "medium"


def test_derive_arbiter_force_human_when_no_detection():
    decision, conf = derive_arbiter_for_pe(
        position_correct=False, action_correct=False, has_any_detection=False
    )
    assert decision == "force_human"
    assert conf == "low"


def test_apply_pe_fusion_happy_path():
    fusion, arb_dec, arb_conf, cot = apply_pe_fusion(
        target_region="right_lower_lung",
        detected_regions=["right_lower_lung"],
        v_agent=_v(),
    )
    assert fusion.score_0_5 == 5
    assert arb_dec == "accept"
    assert arb_conf == "high"
    assert cot["source"] == "pe_fusion"
    assert cot["position_correct"] is True
    assert "rationale" in cot


def test_apply_pe_fusion_wrong_region_yields_flag():
    fusion, arb_dec, arb_conf, cot = apply_pe_fusion(
        target_region="right_lower_lung",
        detected_regions=["left_upper_lung"],
        v_agent=_v(),
    )
    assert arb_dec == "flag"
    assert arb_conf == "medium"
    assert fusion.position_correct is False


def test_apply_pe_fusion_no_detection_yields_force_human():
    fusion, arb_dec, _conf, _cot = apply_pe_fusion(
        target_region="pmi",
        detected_regions=[],
        v_agent=_v(action=False, technique=0.0, duration=False),
    )
    assert arb_dec == "force_human"
    assert fusion.score_0_5 == 0
