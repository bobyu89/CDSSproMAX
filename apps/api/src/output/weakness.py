"""弱點分析:彙整三軌 weak_points + DUAT analysis,排序。(Builder output.md)"""

from __future__ import annotations


def build_weakness(session, duat_result: dict) -> dict:
    weak = []
    for ss in session.phase_scores.values():
        weak.extend(getattr(ss, "weak_points", []))
    analysis = duat_result["analysis"].payload.get("analysis", "")
    return {"type": "weakness", "items": weak, "duat_analysis": analysis}
