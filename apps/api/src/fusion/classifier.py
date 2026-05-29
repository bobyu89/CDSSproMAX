"""
三訊號融合分類器 (Builder fusion-classifier.md / v1.1)
======================================================
HRV × 停頓 × 表情 → 學習狀態 → 即時難度調整。
加權投票(HRV 最重)+ 持續性防抖。
壓力監測為可選功能;沒有 HRV 不頂替(誠實回報)。
"""

from __future__ import annotations

import time

from src.signals.expression import dominant_expression

# 訊號權重:HRV 最難偽裝,權重最高
WEIGHTS = {"hrv": 0.5, "pause": 0.25, "expression": 0.25}

# 各狀態對應的訊號標籤
STATE_SIGNATURE = {
    "anxious": {"hrv": "drop", "pause": "long", "expression": "frown"},
    "flow": {"hrv": "stable", "pause": "fluent", "expression": "focused"},
    "low_engagement": {"hrv": "flat", "pause": "fluent", "expression": "relaxed"},
}

VOTE_THRESHOLD = 0.5  # 加權得分需達此值才算有效狀態
STABLE_DURATION = 20.0  # 狀態須持續幾秒才調難度(防抖)


def _latest(session, sig_type, window=10.0, now=None):
    """取近 window 秒內某訊號的最新標籤。"""
    if now is None:
        now = time.time()
    items = [
        s for s in session.signals
        if s["type"] == sig_type and now - s["timestamp"] <= window
    ]
    return items[-1]["label"] if items else None


def classify_state(session, now=None) -> str:
    """加權投票得出當前學習狀態。回傳 anxious/flow/low_engagement/ambiguous。"""
    observed = {
        "hrv": _latest(session, "hrv", now=now),
        "pause": _latest(session, "pause", now=now),
        "expression": dominant_expression(session, now=now),
    }
    scores = {
        state: sum(WEIGHTS[k] for k in sig if observed.get(k) == sig[k])
        for state, sig in STATE_SIGNATURE.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] >= VOTE_THRESHOLD else "ambiguous"


def update_and_decide(session, mode: str, now=None) -> dict:
    """主入口:分類狀態 + 持續性防抖 + 介入決策。"""
    if now is None:
        now = time.time()

    # 壓力監測開關與 HRV 必要檢查
    if not session.scratch.get("stress_monitoring_enabled", False):
        return {"state": "disabled", "message": "壓力監測未開啟"}
    if _latest(session, "hrv", now=now) is None:
        return {"state": "unavailable", "message": "無 HRV 訊號,無法生成壓力監測"}

    state = classify_state(session, now=now)

    # 持續性追蹤(防抖)
    fs = session.scratch.setdefault(
        "fusion", {"candidate": None, "since": now, "active": None}
    )
    if state != fs["candidate"]:
        fs["candidate"] = state
        fs["since"] = now
        held = 0.0
    else:
        held = now - fs["since"]

    session.signals.append({
        "type": "fusion_state",
        "timestamp": now,
        "state": state,
        "held": round(held, 1),
    })

    # 介入決策:須持續 STABLE_DURATION 秒,且非 ambiguous,才調難度
    intervention = "none"
    if state != "ambiguous" and held >= STABLE_DURATION and fs["active"] != state:
        intervention = _intervention(state, mode)
        fs["active"] = state

    return {"state": state, "held": round(held, 1), "intervention": intervention}


def _intervention(state: str, mode: str) -> str:
    """狀態 → 介入動作。考試模式僅記錄不介入。"""
    if mode == "exam":
        return "record_only"
    return {
        "anxious": "lower_difficulty",
        "flow": "maintain",
        "low_engagement": "raise_difficulty",
    }.get(state, "none")
