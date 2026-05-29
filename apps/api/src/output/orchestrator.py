"""
輸出協調者 (Builder output.md)
===============================
統籌五種輸出,共用一份 DUAT 結果,確保彼此不矛盾。
管理依賴:weakness → keyfocus;narrative 最後呼應全部。
"""

from __future__ import annotations

from src.output.keyfocus import build_keyfocus
from src.output.narrative import build_narrative
from src.output.radar import build_radar
from src.output.stress import build_stress
from src.output.weakness import build_weakness


async def build_all_outputs(session, duat_result: dict) -> dict:
    """產出五種輸出。duat_result 為共用真相來源。"""
    radar = build_radar(session)
    stress = build_stress(session)
    weakness = build_weakness(session, duat_result)
    keyfocus = build_keyfocus(weakness)  # 依賴 weakness
    narrative = await build_narrative(  # 最後,呼應全部 + 反事實
        session, duat_result, radar, weakness, keyfocus, stress
    )
    return {
        "narrative": narrative,  # ① 自然語言評語(含反事實)
        "radar": radar,  # ② 雷達圖
        "weakness": weakness,  # ③ 弱點分析
        "keyfocus": keyfocus,  # ④ 重點提示
        "stress": stress,  # ⑤ 壓力曲線
        # ⑥ RAG 講義由 rag.note 模組另外產生
    }
