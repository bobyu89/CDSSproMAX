"""
LLM 路由器 — 熱插拔的切換中樞 (Builder llm-adapter.md)
======================================================
1. 任務導向:依任務取得主力模型
2. 備援機制:主力失敗自動切備援,並記錄 fallback
3. 成本追蹤:每次呼叫累加成本至 session.scratch["llm_cost"]

換模型只改 LLM_CONFIG 一張表,所有 Agent 程式碼不動。
模型 ID 預設取自 settings(單一真相),可被 LLM_CONFIG override。
"""

from __future__ import annotations

import logging

from src.config import get_settings
from src.llm.adapters import ClaudeAdapter, GeminiAdapter
from src.llm.interface import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

_settings = get_settings()
_GEMINI = _settings.e_agent_model  # gemini-3.5-flash
_CLAUDE = _settings.s_agent_model  # claude-opus-4-7

# 任務 → [(主力 provider, model), (備援 provider, model), ...]
# 換模型只改這張表,所有 Agent 不動。
LLM_CONFIG: dict[str, list[tuple[str, str]]] = {
    "vision": [("gemini", _GEMINI), ("gemini", _GEMINI)],
    "dialog": [("gemini", _GEMINI), ("claude", _CLAUDE)],
    "diagnosis": [("claude", _CLAUDE), ("gemini", _GEMINI)],
    "duat": [("claude", _CLAUDE), ("gemini", _GEMINI)],
    # inquiry 的語義模糊判斷:便宜優先(Gemini),備援 Claude
    "inquiry": [("gemini", _GEMINI), ("claude", _CLAUDE)],
}

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "gemini": GeminiAdapter,
    "claude": ClaudeAdapter,
}


def _build(provider_name: str, model: str) -> LLMProvider:
    return _PROVIDERS[provider_name](model=model)


def _accumulate_cost(session, response: LLMResponse) -> None:
    if session is None:
        return
    scratch = getattr(session, "scratch", None)
    if scratch is None:
        return
    scratch.setdefault("llm_cost", 0.0)
    scratch["llm_cost"] += response.usage.cost_usd
    scratch.setdefault("llm_calls", [])
    scratch["llm_calls"].append(response.usage)


async def call_llm(
    task: str,
    prompt: str,
    session=None,
    image_b64=None,
    system: str = "",
    temperature: float = 0.7,
    json_mode: bool = False,
) -> LLMResponse:
    """
    依任務呼叫 LLM。主力失敗自動切備援。成本累加至 session。

    task        — LLM_CONFIG 的鍵(vision/dialog/diagnosis/duat/inquiry)
    image_b64   — 提供時走 generate_with_image(僅 vision 任務)
    json_mode   — True 時要求模型只回 JSON
    """
    if task not in LLM_CONFIG:
        raise KeyError(f"unknown LLM task '{task}'; known: {list(LLM_CONFIG)}")

    chain = LLM_CONFIG[task]
    last_error: Exception | None = None

    for i, (pname, model) in enumerate(chain):
        provider = _build(pname, model)
        try:
            if image_b64 is not None:
                resp = await provider.generate_with_image(
                    prompt, image_b64, system=system, json_mode=json_mode
                )
            else:
                resp = await provider.generate(
                    prompt, system=system, temperature=temperature, json_mode=json_mode
                )
            resp.usage.used_fallback = i > 0
            if i > 0:
                logger.warning(
                    "task '%s' fell back to %s/%s (primary failed)", task, pname, model
                )
            _accumulate_cost(session, resp)
            return resp
        except Exception as e:  # noqa: BLE001 — try next in fallback chain
            last_error = e
            logger.warning("task '%s' attempt %d (%s/%s) failed: %s", task, i, pname, model, e)
            continue

    raise RuntimeError(f"任務 {task} 所有模型皆失敗:{last_error}")
