"""
HRV 訊號採集器 (Builder signal-hrv.md)
======================================
採集 RMSSD 與 LF/HF,相對「每迴圈前正念冥想建立的基準」分類。
只輸出訊號標籤,不判斷學習狀態(那是 fusion-classifier 的事)。

注意:這是「訊號標籤層」,與 physio/hrv.py(SDNN/RMSSD/pNN50 計算)互補。
physio/hrv.py 負責從 RR interval 算指標;本檔負責相對基準分類成 drop/stable/flat。
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class HRVBaseline:
    """每迴圈前正念冥想期間建立的個人基準。"""

    rmssd: float
    lf_hf: float


@dataclass
class HRVReading:
    """單次 HRV 量測。"""

    rmssd: float
    lf_hf: float
    timestamp: float


def build_baseline(readings: list[HRVReading]) -> HRVBaseline:
    """用 1 分鐘正念冥想期間的多次量測算基準(取中位數抗極端值)。"""
    return HRVBaseline(
        rmssd=statistics.median(r.rmssd for r in readings),
        lf_hf=statistics.median(r.lf_hf for r in readings),
    )


def classify_hrv(reading: HRVReading, baseline: HRVBaseline) -> str:
    """相對基準分類訊號。回傳 'drop' | 'stable' | 'flat'。"""
    rmssd_ratio = reading.rmssd / baseline.rmssd if baseline.rmssd else 1.0
    lf_hf_ratio = reading.lf_hf / baseline.lf_hf if baseline.lf_hf else 1.0

    if rmssd_ratio < 0.75 and lf_hf_ratio > 1.3:  # 焦慮:交感主導
        return "drop"
    if rmssd_ratio > 1.25:  # 低投入:過度放鬆、節律平坦
        return "flat"
    return "stable"  # 投入/心流帶


async def collect_and_classify(session, reading: HRVReading) -> str:
    """主入口:採集一筆 HRV,分類,寫入 session.signals。"""
    baseline = session.scratch.get("hrv_baseline")
    if baseline is None:
        return "stable"  # 尚未建立基準,暫視為穩定

    label = classify_hrv(reading, baseline)
    session.signals.append({
        "type": "hrv",
        "phase": session.phase.value,
        "timestamp": reading.timestamp,
        "label": label,
        "rmssd": reading.rmssd,
        "lf_hf": reading.lf_hf,
    })
    return label
