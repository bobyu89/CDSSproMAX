"""雷達圖:問診/身評/診斷/溝通四維度。吃 StageScore 分數。(Builder output.md)"""

from __future__ import annotations


def build_radar(session) -> dict:
    ps = session.phase_scores
    return {
        "type": "radar",
        "dimensions": {
            "問診": ps["inquiry"].raw_score if ps.get("inquiry") else 0,
            "身評": ps["examination"].raw_score if ps.get("examination") else 0,
            "診斷": ps["diagnosis"].raw_score if ps.get("diagnosis") else 0,
            "溝通": _communication(session),
        },
    }


def _communication(session) -> float:
    inq = session.phase_scores.get("inquiry")
    if not inq:
        return 0
    return inq.sub_items.get("quality", 0)
