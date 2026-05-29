"""
即時評分器 (Builder realtime-scorer.md / contract-v1.0)
=======================================================
練習模式中,節點結束後立即給分 + 一句回饋。
60% 確定性(用既有 StageScore)+ 40% LLM 語義。輸出 EvalResult。
考試模式不即時給分(回 None),全程結束才由 DUAT 評。
"""

from __future__ import annotations

import json

from src.core.contract import EvalResult
from src.llm.router import call_llm


async def realtime_score(session, stage_score, context: str = ""):
    """對剛結束的節點即時評分。考試模式回 None。"""
    if session.mode == "exam":
        return None

    deterministic = stage_score.raw_score  # 0–100,已算好(60%)

    # 40% LLM 語義(只評規則抓不到的品質)
    semantic = deterministic
    feedback = "繼續保持"
    try:
        resp = await call_llm(
            "dialog",
            prompt=(
                f"以下是學員在『{stage_score.stage}』階段的表現:\n{context}\n"
                f"請就『表達清晰度與臨床合理性』給 0–100 分,並用一句話(20字內)回饋。"
                f'回傳JSON:{{"semantic":分數,"feedback":"一句話"}}'
            ),
            session=session,
            json_mode=True,
        )
        parsed = _parse(resp.text)
        semantic = parsed.get("semantic", deterministic)
        feedback = parsed.get("feedback", "繼續保持")
    except Exception:  # noqa: BLE001 — 語義評分失敗退回確定性,不中斷
        pass

    final = round(deterministic * 0.6 + float(semantic) * 0.4, 1)
    return EvalResult(
        source="realtime-scorer",
        payload={
            "stage": stage_score.stage,
            "score": final,
            "deterministic": deterministic,
            "semantic": semantic,
            "feedback": feedback,
        },
    )


def _parse(txt):
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return {}
