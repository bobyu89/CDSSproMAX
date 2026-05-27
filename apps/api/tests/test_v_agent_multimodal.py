"""V-Agent real-call path — monkeypatch the multimodal helper."""

import base64

import pytest

from src.agents.v_agent import VAgent, VAgentInput

pytestmark = pytest.mark.asyncio


def _fake_jpeg_b64() -> str:
    # 1×1 JPEG so the agent has *something* to send.
    return base64.b64encode(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00").decode()


async def test_v_agent_real_path_monkeypatched(monkeypatch):
    from src.agents import v_agent as v_module
    from src.config import get_settings

    # Pretend we have an API key for this test.
    get_settings.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    captured = {}

    async def fake_multimodal(*, model, prompt, images_b64, system_instruction):
        captured["model"] = model
        captured["n_images"] = len(images_b64)
        captured["has_intent"] = "右下肺葉" in prompt
        return {
            "action_correct": True,
            "technique_score": 0.82,
            "duration_adequate": True,
            "evidence_frames": [0, 2],
            "notes": "聽診器膜面平貼，停留約 4 秒。",
        }

    monkeypatch.setattr(v_module, "gemini_generate_json_multimodal", fake_multimodal)

    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id="pe.lung.auscultation.right_lower",
            target_action="auscultation",
            target_region="right_lower_lung",
            student_intent="我要聽右下肺葉",
            detected_regions=["right_lower_lung"],
            keyframes_b64=[_fake_jpeg_b64(), _fake_jpeg_b64(), _fake_jpeg_b64()],
            duration_seconds=4.2,
        )
    )

    assert out.action_correct is True
    assert out.technique_score == pytest.approx(0.82)
    assert out.duration_adequate is True
    assert out.evidence_frames == [0, 2]
    assert "stub" not in out.model_version.lower()
    assert captured["n_images"] == 3
    assert captured["has_intent"] is True
    assert out.prompt_hash and out.prompt_hash.startswith("sha256:")


async def test_v_agent_falls_back_on_api_error(monkeypatch):
    from src.agents import v_agent as v_module
    from src.config import get_settings

    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    async def boom(**_kwargs):
        raise RuntimeError("simulated API outage")

    monkeypatch.setattr(v_module, "gemini_generate_json_multimodal", boom)

    v = VAgent()
    out = await v.run(
        VAgentInput(
            rubric_item_id="pe.cardio.auscultation",
            target_action="auscultation",
            target_region="pmi",
            detected_regions=["pmi"],
            keyframes_b64=[_fake_jpeg_b64()],
            duration_seconds=4.0,
        )
    )
    assert "stub" in out.model_version.lower()
    assert "api-error" in out.model_version
