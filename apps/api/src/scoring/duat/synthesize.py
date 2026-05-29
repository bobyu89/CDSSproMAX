"""
S-Agent 綜整 (Builder duat-agents.md)
======================================
把問診/身評/診斷三軌整合成一個整體評價(與 E 並行,都只依賴 O)。
"""

from __future__ import annotations

from src.core.contract import EvalResult
from src.llm.router import call_llm


async def run_synthesize(session, observation: EvalResult) -> EvalResult:
    resp = await call_llm(
        "duat",
        prompt=f"根據觀察摘要:\n{observation.payload['observation']}\n"
        f"請將三軌表現整合成一段整體評價,說明學員的臨床推理是否連貫"
        f"(問診→身評→診斷是否一氣呵成)。回傳JSON。",
        session=session,
        json_mode=True,
    )
    return EvalResult(source="duat-synthesize", payload={"synthesis": resp.text})
