"""
A-Agent 分析 (Builder duat-agents.md)
======================================
依 E + S 找出弱點、錯誤模式與原因(依賴評估與綜整)。
"""

from __future__ import annotations

from src.core.contract import EvalResult
from src.llm.router import call_llm


async def run_analyze(session, evaluation: EvalResult, synthesis: EvalResult) -> EvalResult:
    resp = await call_llm(
        "duat",
        prompt=f"評估結果:\n{evaluation.payload['evaluation']}\n"
        f"整體綜整:\n{synthesis.payload['synthesis']}\n"
        f"請找出:1)最關鍵的弱點(排序)2)錯誤模式 3)可能原因。"
        f"回傳JSON,含 weak_points 陣列。",
        session=session,
        json_mode=True,
    )
    return EvalResult(source="duat-analyze", payload={"analysis": resp.text})
