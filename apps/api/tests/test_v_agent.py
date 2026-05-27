"""V-Agent shell — Wave 1.5 stub behaviour."""

import pytest

from src.agents.v_agent import VAgent, VAgentInput


pytestmark = pytest.mark.asyncio


async def test_v_agent_stub_marks_action_correct_when_intent_matches():
    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id="pe.lung.auscultation.right_lower",
            target_action="auscultation",
            target_region="right_lower_lung",
            student_intent="我要聽右下肺葉",
            detected_regions=["right_lower_lung"],
            keyframes_b64=[],
            duration_seconds=4.0,
        )
    )
    assert out.action_correct is True
    assert 0.0 <= out.technique_score <= 1.0
    assert out.duration_adequate is True
    assert "stub" in out.model_version.lower()


async def test_v_agent_stub_rejects_when_region_not_detected():
    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id="pe.lung.auscultation.right_lower",
            target_action="auscultation",
            target_region="right_lower_lung",
            detected_regions=[],
            duration_seconds=4.0,
        )
    )
    assert out.action_correct is False
    assert out.technique_score == 0.0


async def test_v_agent_duration_below_threshold():
    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id="pe.cardio.auscultation",
            target_action="auscultation",
            target_region="pmi",
            detected_regions=["pmi"],
            duration_seconds=2.0,
        )
    )
    assert out.duration_adequate is False


async def test_v_agent_prompt_hash_present():
    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id="pe.cardio.auscultation",
            target_action="auscultation",
            target_region="pmi",
            detected_regions=["pmi"],
            duration_seconds=4.0,
        )
    )
    assert out.prompt_hash and out.prompt_hash.startswith("sha256:")
