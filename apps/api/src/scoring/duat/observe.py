"""
O-Agent 觀察 (Builder duat-agents.md)
======================================
彙整全程客觀資料(不評價,只整理),作為後續代理的共同輸入。
"""

from __future__ import annotations

from src.core.contract import EvalResult
from src.llm.router import call_llm


async def run_observe(session) -> EvalResult:
    raw = {
        "phase_scores": {
            k: vars(v) if hasattr(v, "__dict__") else v
            for k, v in session.phase_scores.items()
        },
        "signals": session.signals,
        "fusion_states": [s for s in session.signals if s.get("type") == "fusion_state"],
    }
    resp = await call_llm(
        "duat",
        prompt=f"以下是學員一次完整訓練的原始資料:\n{raw}\n"
        f"請客觀彙整為結構化觀察摘要(不評價),回傳JSON。",
        session=session,
        json_mode=True,
    )
    return EvalResult(
        source="duat-observe", payload={"observation": resp.text, "raw": raw}
    )
