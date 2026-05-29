"""
M-Agent 記憶 (Builder duat-agents.md)
======================================
比對學員過去歷程,產出個人化敘事。
設計成「沒歷程也能跑」:首次訓練只描述本次,有歷程才比對。
"""

from __future__ import annotations

from src.core.contract import EvalResult
from src.llm.router import call_llm


def _load_history(student_id, history_loader=None):
    """讀取學員過去的 A-Agent 分析紀錄。無則回空。

    history_loader: 可注入的載入器(persistence 串接後傳入 Repository.get_student_history)。
    """
    if student_id is None or history_loader is None:
        return []
    try:
        return history_loader(student_id, limit=3)
    except Exception:  # noqa: BLE001
        return []


async def run_memory(session, analysis: EvalResult, student_id=None, history_loader=None) -> EvalResult:
    history = _load_history(student_id, history_loader)

    if not history:
        prompt = (
            f"本次分析:\n{analysis.payload['analysis']}\n"
            f"這是學員第一次訓練。請用鼓勵語氣描述本次表現重點,"
            f"並標示未來可追蹤的指標。回傳JSON。"
        )
    else:
        prompt = (
            f"本次分析:\n{analysis.payload['analysis']}\n"
            f"過去紀錄:\n{history}\n"
            f"請比對:1)有無進步 2)是否重犯老問題 3)個人化建議。回傳JSON。"
        )

    resp = await call_llm("duat", prompt=prompt, session=session, json_mode=True)
    return EvalResult(
        source="duat-memory",
        payload={"memory": resp.text, "has_history": bool(history)},
    )
