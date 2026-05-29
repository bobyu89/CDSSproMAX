"""壓力曲線:讀 fusion_state 時序 + HRV,產出壓力隨時間變化。(Builder output.md)"""

from __future__ import annotations


def build_stress(session) -> dict:
    stress_map = {"anxious": 3, "ambiguous": 2, "low_engagement": 1, "flow": 0}
    curve = [
        {"t": s["timestamp"], "level": stress_map.get(s["state"], 2), "state": s["state"]}
        for s in session.signals
        if s.get("type") == "fusion_state"
    ]
    hrv = [
        {"t": s["timestamp"], "rmssd": s.get("rmssd")}
        for s in session.signals
        if s.get("type") == "hrv"
    ]
    peak = max(curve, key=lambda c: c["level"]) if curve else None
    return {"type": "stress_curve", "curve": curve, "hrv": hrv, "peak": peak}
