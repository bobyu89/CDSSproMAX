"""
語音停頓訊號採集器 (Builder signal-pause.md)
=============================================
把靜音偵測轉成 fluent/long 標籤。混合判斷:固定閾值為安全網,
累積足夠資料後用相對個人基準。只採集標籤,不判斷學習狀態。
"""

from __future__ import annotations

import statistics

DEFAULT_LONG_THRESHOLD = 5.0  # 秒,超過視為長停頓
MIN_SAMPLES_FOR_RELATIVE = 5  # 累積幾筆後改用相對基準
FREQUENT_PAUSE_WINDOW = 60  # 秒,計算停頓頻率的視窗
FREQUENT_PAUSE_COUNT = 3  # 視窗內停頓幾次算頻繁


def _long_threshold(session) -> float:
    pauses = [s["duration"] for s in session.signals if s["type"] == "pause"]
    if len(pauses) >= MIN_SAMPLES_FOR_RELATIVE:
        mean = statistics.mean(pauses)
        sd = statistics.pstdev(pauses) or 1.0
        return mean + 1.5 * sd  # 相對個人:明顯高於自己平常
    return DEFAULT_LONG_THRESHOLD


def _is_frequent(session, now: float) -> bool:
    recent = [
        s for s in session.signals
        if s["type"] == "pause" and now - s["timestamp"] <= FREQUENT_PAUSE_WINDOW
    ]
    return len(recent) >= FREQUENT_PAUSE_COUNT


def collect_and_classify(session, duration: float, timestamp: float) -> str:
    """主入口:採集一次停頓,分類,寫入 session.signals。回傳 'fluent' | 'long'。"""
    threshold = _long_threshold(session)
    is_long_by_duration = duration > threshold
    is_frequent = _is_frequent(session, timestamp)
    label = "long" if (is_long_by_duration or is_frequent) else "fluent"

    session.signals.append({
        "type": "pause",
        "phase": session.phase.value,
        "timestamp": timestamp,
        "duration": duration,
        "label": label,
        "threshold_used": round(threshold, 1),
        "frequent": is_frequent,
    })
    return label
