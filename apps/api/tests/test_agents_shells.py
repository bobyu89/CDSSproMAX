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


async def test_e_agent_real_call_path(monkeypatch):
    """E-Agent is wired to Gemini now — verify the SDK call path without
    actually hitting the network."""
    from src.agents import e_agent as e_module

    async def fake_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "rubric_item_id": "lqqopera.location",
            "evidence_segments": [
                {"speaker": "student", "text": "請問哪裡痛？", "relevance_score": 0.9}
            ],
            "confidence": 0.85,
            "extraction_notes": "asked location explicitly",
        }

    monkeypatch.setattr(e_module, "gemini_generate_json", fake_gemini)

    class _NullBibliotheke:
        async def search(self, *args, **kwargs):  # noqa: ARG002
            return []

    e = EAgent(bibliotheke=_NullBibliotheke())
    out = await e.run(
        EAgentInput(
            rubric_item_id="lqqopera.location",
            transcript_text="(student): 請問哪裡痛？",
            case_context="chest pain case",
        )
    )
    assert out.rubric_item_id == "lqqopera.location"
    assert out.confidence == 0.85
    assert len(out.evidence_segments) == 1
    assert out.evidence_segments[0].text == "請問哪裡痛？"
    assert out.prompt_hash and out.prompt_hash.startswith("sha256:")
    bundle = out.as_bundle()
    assert bundle["rubric_item_id"] == "lqqopera.location"


async def test_s_agent_real_call_path(monkeypatch):
    """S-Agent is wired to Claude — fake the SDK call, verify parsing/audit."""
    from src.agents import s_agent as s_module

    async def fake_claude(*, model, system, user_message, max_tokens=2048):  # noqa: ARG001
        return {
            "score": 4,
            "cot_reasoning": "學員主動詢問位置並追問放射，符合 level 4 描述。",
            "cited_evidence_ids": [0],
        }

    monkeypatch.setattr(s_module, "claude_generate_json", fake_claude)

    s = SAgent()
    out = await s.run(
        SAgentInput(
            rubric_item_id="lqqopera.location",
            rubric_item_spec={"max_score": 5, "criteria": []},
            evidence_bundle={
                "rubric_item_id": "lqqopera.location",
                "evidence_segments": [{"speaker": "student", "text": "請問哪裡痛？"}],
            },
        )
    )
    assert out.score == 4
    assert out.cited_evidence_ids == [0]
    assert "放射" in out.cot_reasoning
    assert out.prompt_hash and out.prompt_hash.startswith("sha256:")


async def test_a_agent_real_call_path(monkeypatch):
    """A-Agent is wired to Gemini — fake the SDK call, verify parsing."""
    from src.agents import a_agent as a_module

    async def fake_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "advocate_report": "證據僅一句，未確認放射範圍。",
            "advocate_score": 0.4,
            "challenged_points": ["未追問放射", "未量化位置"],
        }

    monkeypatch.setattr(a_module, "gemini_generate_json", fake_gemini)

    a = AAgent()
    out = await a.run(
        AAgentInput(
            rubric_item_id="lqqopera.location",
            rubric_item_spec={"max_score": 5, "criteria": []},
            evidence_bundle={"rubric_item_id": "lqqopera.location"},
        )
    )
    assert out.advocate_score == 0.4
    assert len(out.challenged_points) == 2
    assert out.prompt_hash and out.prompt_hash.startswith("sha256:")


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
