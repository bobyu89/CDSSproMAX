"""
自然語言評語(含反事實) (Builder output.md)
=============================================
最後產出,呼應雷達圖/弱點/重點/壓力曲線,語氣一致不矛盾。
含反事實回饋(「如果當時…」),取用 DUAT analysis 的細節。
"""

from __future__ import annotations

from src.llm.router import call_llm


async def build_narrative(session, duat_result, radar, weakness, keyfocus, stress) -> dict:
    resp = await call_llm(
        "duat",
        prompt=(
            f"請寫一段給學員的整體評語(像臨床老師的口吻):\n"
            f"四維度分數:{radar['dimensions']}\n"
            f"最該注意:{keyfocus['focus']}\n"
            f"弱點:{weakness['items']}\n"
            f"壓力峰值:{stress.get('peak')}\n"
            f"DUAT 綜整:{duat_result['synthesis'].payload.get('synthesis')}\n"
            f"DUAT 記憶:{duat_result['memory'].payload.get('memory')}\n\n"
            f"要求:1)語氣鼓勵但誠實 2)務必呼應上述數字,不可矛盾 "
            f"3)結尾加一段反事實回饋,具體說明『如果當時做了什麼,結果會如何不同』"
            f"(取材自弱點與診斷推理)。回傳純文字。"
        ),
        session=session,
    )
    return {"type": "narrative", "text": resp.text}
