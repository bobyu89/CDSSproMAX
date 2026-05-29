"""
LLM 統一介面 (Builder llm-adapter.md / contract-v1.0)
=====================================================
所有 Agent 透過此介面呼叫 LLM,不直接依賴任何 SDK。
換模型只改 config,Agent 程式碼完全不動。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMUsage:
    """單次呼叫的用量與成本。"""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    used_fallback: bool = False  # 是否觸發了備援


@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        """純文字生成。json_mode=True 時要求模型只回 JSON。"""
        ...

    @abstractmethod
    async def generate_with_image(
        self,
        prompt: str,
        image_b64: str | list[str],
        system: str = "",
        json_mode: bool = False,
    ) -> LLMResponse:
        """帶影像生成(身評視覺評核用)。"""
        ...
