"""
臉部表情訊號採集器 (Builder signal-expression.md)
==================================================
本地 FER 為主,信心低時送 Gemini 補強。映射到四類:
frown(焦慮)/ focused(心流)/ relaxed(低投入)/ neutral(中性)。
只採集標籤,不判斷學習狀態(交給 fusion-classifier)。

注意:本地 FER 模型(_local_fer)為 Wave 2 才接的外部依賴;在 FER 未接前,
collect_and_classify 會直接走 Gemini 視覺判斷或回傳 neutral,不會 crash。
"""

from __future__ import annotations

import time

from src.llm.router import call_llm

EXPRESSIONS = {"frown", "focused", "relaxed", "neutral"}
CONFIDENCE_THRESHOLD = 0.6

FER_TO_LABEL = {
    "angry": "frown",
    "disgust": "frown",
    "fear": "frown",
    "sad": "frown",
    "happy": "relaxed",
    "surprise": "focused",
    "neutral": "neutral",
}


def _local_fer(frame):
    """本地 FER 推論。回傳 (原始表情, 信心)。Wave 2 接 fer/deepface 時實作。

    未接模型前回傳低信心 neutral,讓 collect_and_classify 走 Gemini 補強。
    """
    return "neutral", 0.0


def _map_label(raw: str) -> str:
    return FER_TO_LABEL.get(raw, "neutral")


async def collect_and_classify(session, frame, timestamp: float | None = None) -> str:
    """主入口:採集一幀表情,分類,寫入 session.signals。"""
    if timestamp is None:
        timestamp = time.time()

    raw, confidence = _local_fer(frame)
    label = _map_label(raw)
    source = "local_fer"

    if confidence < CONFIDENCE_THRESHOLD:
        try:
            resp = await call_llm(
                "vision",
                prompt="判斷畫面中學員的表情屬於哪一類,只回一個英文字:"
                "frown / focused / relaxed / neutral",
                image_b64=frame,
                session=session,
            )
            g = resp.text.strip().lower()
            if g in EXPRESSIONS:
                label = g
                source = "gemini"
        except Exception:  # noqa: BLE001 — 表情是輔助訊號,失敗不可中斷訓練
            label = "neutral"
            source = "fallback"

    session.signals.append({
        "type": "expression",
        "phase": session.phase.value,
        "timestamp": timestamp,
        "label": label,
        "confidence": round(confidence, 2),
        "source": source,
    })
    return label


def dominant_expression(session, window: float = 10.0, now: float | None = None) -> str:
    """取近 window 秒內的主要表情(供 fusion 取用),降低單幀雜訊。"""
    if now is None:
        now = time.time()
    recent = [
        s["label"]
        for s in session.signals
        if s["type"] == "expression" and now - s["timestamp"] <= window
    ]
    if not recent:
        return "neutral"
    non_neutral = [r for r in recent if r != "neutral"]
    pool = non_neutral or recent
    return max(set(pool), key=pool.count)
