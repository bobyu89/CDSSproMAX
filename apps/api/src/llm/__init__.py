"""TICDSS LLM 熱插拔層 (Builder llm-adapter.md).

所有 Agent 透過 call_llm 呼叫 LLM,不直接綁定 SDK。
"""

from src.llm.interface import LLMProvider, LLMResponse, LLMUsage
from src.llm.pricing import PRICING, estimate_cost
from src.llm.router import LLM_CONFIG, call_llm

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMUsage",
    "PRICING",
    "estimate_cost",
    "LLM_CONFIG",
    "call_llm",
]
