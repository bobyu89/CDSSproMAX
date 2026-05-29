"""
E-Agent 評估 (Builder duat-agents.md)
======================================
依 Rubric 對每一項逐條打分,給出分數與依據。
"""

from __future__ import annotations

from src.core.contract import EvalResult
from src.llm.router import call_llm


async def run_evaluate(session, observation: EvalResult) -> EvalResult:
    resp = await call_llm(
        "duat",
        prompt=f"根據觀察摘要:\n{observation.payload['observation']}\n"
        f"請依臨床技能 Rubric 對問診、身評、診斷逐項評分(0–100)並附依據。"
        f"另外回傳一個 0–1 的 confidence 表示本評估的把握程度。回傳JSON。",
        session=session,
        json_mode=True,
    )
    return EvalResult(source="duat-evaluate", payload={"evaluation": resp.text})
