"""Smoke tests for the five Agent shells — verify each can be called."""

import pytest

from src.agents import AAgent, EAgent, MAgent, OAgent, SAgent
from src.agents.a_agent import AAgentInput
from src.agents.e_agent import EAgentInput
from src.agents.m_agent import MAgentInput
from src.agents.o_agent import OAgentInput, Phase
from src.agents.s_agent import SAgentInput


pytestmark = pytest.mark.asyncio


async def test_o_agent_advances_phase():
    o = OAgent()
    out = await o.run(OAgentInput(session_id="s1", current_phase=Phase.SCENARIO, mode="exam"))
    assert out.next_phase == Phase.INQUIRY
    assert out.time_limit_s == 360


async def test_o_agent_practice_no_time_limit():
    o = OAgent()
    out = await o.run(OAgentInput(session_id="s1", current_phase=Phase.INQUIRY, mode="practice"))
    assert out.next_phase == Phase.TRANSITION
    assert out.time_limit_s is None


async def test_o_agent_review_stays_at_review():
    o = OAgent()
    out = await o.run(OAgentInput(session_id="s1", current_phase=Phase.REVIEW, mode="exam"))
    assert out.next_phase == Phase.REVIEW


async def test_e_agent_stub_returns_bundle():
    e = EAgent()
    out = await e.run(EAgentInput(rubric_item_id="lqqopera.location", transcript_text="..."))
    assert out.rubric_item_id == "lqqopera.location"
    assert "stub" in out.extraction_notes.lower()
    bundle = out.as_bundle()
    assert bundle["rubric_item_id"] == "lqqopera.location"


async def test_s_agent_stub():
    s = SAgent()
    out = await s.run(
        SAgentInput(
            rubric_item_id="lqqopera.location",
            rubric_item_spec={"max_score": 5},
            evidence_bundle={"rubric_item_id": "lqqopera.location"},
        )
    )
    assert out.score == 0
    assert "stub" in out.cot_reasoning.lower()


async def test_a_agent_stub():
    a = AAgent()
    out = await a.run(
        AAgentInput(
            rubric_item_id="lqqopera.location",
            rubric_item_spec={"max_score": 5},
            evidence_bundle={"rubric_item_id": "lqqopera.location"},
            s_score=4,
            s_cot="[stub]",
        )
    )
    assert out.advocate_score == 0.0


async def test_m_agent_no_alert_below_threshold():
    m = MAgent()
    out = await m.run(
        MAgentInput(rubric_item_id="lqqopera.location", total_scored=20, total_overridden=4)
    )
    assert out.override_rate == 0.20
    assert out.alert is False


async def test_m_agent_alerts_above_threshold():
    m = MAgent()
    out = await m.run(
        MAgentInput(rubric_item_id="lqqopera.quality", total_scored=20, total_overridden=8)
    )
    assert out.override_rate == 0.40
    assert out.alert is True
    assert "exceeds" in (out.alert_reason or "")


async def test_m_agent_ignores_alert_with_small_sample():
    """Below sample-size floor (10) — alert suppressed even if rate is high."""
    m = MAgent()
    out = await m.run(
        MAgentInput(rubric_item_id="lqqopera.onset", total_scored=5, total_overridden=4)
    )
    assert out.override_rate == 0.80
    assert out.alert is False
