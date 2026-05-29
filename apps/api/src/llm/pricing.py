"""
成本估算 — 個人戶開發必備 (Builder llm-adapter.md)
==================================================
每百萬 token 的美元價格。實際數字依各服務公告調整。
使用我們 canonical 的真實模型 ID(非規格範例的占位名)。
"""

from __future__ import annotations

# (input 價格, output 價格) per 1M tokens, USD
PRICING: dict[str, tuple[float, float]] = {
    "gemini-3.5-flash": (0.30, 2.50),
    "claude-opus-4-7": (5.00, 25.00),
}

# 未知模型的保守預設(避免成本顯示為 0 而誤判)
_DEFAULT = (1.00, 5.00)


def estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    p_in, p_out = PRICING.get(model, _DEFAULT)
    return (in_tok / 1e6) * p_in + (out_tok / 1e6) * p_out
