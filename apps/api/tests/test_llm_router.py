"""llm-adapter 驗證 — 對應 builder-spec/sub-agents/llm-adapter.md「驗證方式」。

1. dialog 與 vision 使用不同主力模型。
2. 模擬主力拋例外 → 自動切備援且 used_fallback=True。
3. 連續呼叫 → session.scratch["llm_cost"] 正確累加。
4. 改 LLM_CONFIG 主力 → 呼叫端程式碼不需改動即生效。
"""

from __future__ import annotations

import pytest

from src.core import TrainingSession, Phase
from src.llm import interface, router
from src.llm.interface import LLMResponse, LLMUsage


class FakeProvider(interface.LLMProvider):
    """可程式化的假 provider:可指定要不要拋例外、回傳成本多少。"""

    def __init__(self, model: str, *, fail: bool = False, cost: float = 0.01):
        self.model = model
        self._fail = fail
        self._cost = cost

    async def generate(self, prompt, system="", temperature=0.7, json_mode=False):
        if self._fail:
            raise RuntimeError(f"{self.model} simulated failure")
        return LLMResponse(
            text=f"ok:{self.model}",
            usage=LLMUsage(self.name, self.model, 100, 50, self._cost),
        )

    async def generate_with_image(self, prompt, image_b64, system="", json_mode=False):
        return await self.generate(prompt, system)


@pytest.fixture(autouse=True)
def _restore_config():
    saved = {k: list(v) for k, v in router.LLM_CONFIG.items()}
    saved_providers = dict(router._PROVIDERS)
    yield
    router.LLM_CONFIG.clear()
    router.LLM_CONFIG.update(saved)
    router._PROVIDERS.clear()
    router._PROVIDERS.update(saved_providers)


def _session():
    return TrainingSession(mode="practice", scenario_id="c", phase=Phase.INQUIRY)


@pytest.mark.asyncio
async def test_tasks_use_different_primary_models():
    assert router.LLM_CONFIG["vision"][0] != router.LLM_CONFIG["diagnosis"][0]
    # vision 主力是 gemini,diagnosis 主力是 claude
    assert router.LLM_CONFIG["vision"][0][0] == "gemini"
    assert router.LLM_CONFIG["diagnosis"][0][0] == "claude"


@pytest.mark.asyncio
async def test_fallback_on_primary_failure():
    # 主力 fail、備援 ok
    router._PROVIDERS["gemini"] = lambda model: FakeProvider(model, fail=True)
    router._PROVIDERS["claude"] = lambda model: FakeProvider(model, fail=False, cost=0.05)
    router.LLM_CONFIG["dialog"] = [("gemini", "g"), ("claude", "c")]

    sess = _session()
    resp = await router.call_llm("dialog", "hi", session=sess)
    assert resp.usage.used_fallback is True
    assert resp.text == "ok:c"


@pytest.mark.asyncio
async def test_cost_accumulates_on_session():
    router._PROVIDERS["gemini"] = lambda model: FakeProvider(model, cost=0.02)
    router.LLM_CONFIG["inquiry"] = [("gemini", "g")]
    sess = _session()
    await router.call_llm("inquiry", "a", session=sess)
    await router.call_llm("inquiry", "b", session=sess)
    assert sess.scratch["llm_cost"] == pytest.approx(0.04)
    assert len(sess.scratch["llm_calls"]) == 2


@pytest.mark.asyncio
async def test_all_models_fail_raises():
    router._PROVIDERS["gemini"] = lambda model: FakeProvider(model, fail=True)
    router._PROVIDERS["claude"] = lambda model: FakeProvider(model, fail=True)
    router.LLM_CONFIG["duat"] = [("gemini", "g"), ("claude", "c")]
    with pytest.raises(RuntimeError, match="所有模型皆失敗"):
        await router.call_llm("duat", "x", session=_session())


@pytest.mark.asyncio
async def test_swap_primary_without_touching_caller():
    """改 LLM_CONFIG 主力,呼叫端 call_llm('dialog', ...) 不變即生效。"""
    calls = {}

    def make(model):
        def factory(model=model):
            calls["model"] = model
            return FakeProvider(model)
        return factory

    router._PROVIDERS["gemini"] = make("gemini")
    router._PROVIDERS["claude"] = make("claude")

    router.LLM_CONFIG["dialog"] = [("gemini", "model-A")]
    await router.call_llm("dialog", "x", session=_session())
    assert calls["model"] == "model-A"

    # 換主力為 claude/model-B,呼叫端完全沒改
    router.LLM_CONFIG["dialog"] = [("claude", "model-B")]
    await router.call_llm("dialog", "x", session=_session())
    assert calls["model"] == "model-B"
