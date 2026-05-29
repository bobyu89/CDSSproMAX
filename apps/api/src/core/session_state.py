"""
資料中樞 — 全系統共用的訓練狀態 (Builder core.md / contract-v1.0)
=================================================================
所有模組讀寫同一個 TrainingSession:
問診寫 anxiety、fusion 寫 signals、評分讀 phase_scores。

注意:這是「執行期 in-memory 狀態」,與 db/models.py 的持久化 Session 不同層。
持久化由 persistence 模組負責(訓練結束寫摘要)。
檔名用 session_state.py 而非 session.py,避免與 db/session.py 混淆。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Phase(str, Enum):
    SCENARIO = "scenario"
    INQUIRY = "inquiry"
    TRANSITION = "transition"
    EXAM = "examination"
    DIAGNOSIS = "diagnosis"
    REVIEW = "review"


EXAM_TIME_LIMIT = {  # 考試模式各階段時限(秒)
    Phase.INQUIRY: 360,
    Phase.TRANSITION: 30,
    Phase.EXAM: 360,
    Phase.DIAGNOSIS: 120,
}

PHASE_ORDER = [
    Phase.SCENARIO,
    Phase.INQUIRY,
    Phase.TRANSITION,
    Phase.EXAM,
    Phase.DIAGNOSIS,
    Phase.REVIEW,
]


@dataclass
class TrainingSession:
    mode: str  # 'practice' | 'exam'
    scenario_id: str
    phase: Phase = Phase.SCENARIO
    difficulty: int = 1
    anxiety: float = 0.3
    hrv_baseline: float | None = None
    signals: list = field(default_factory=list)
    phase_scores: dict = field(default_factory=dict)
    scratch: dict = field(default_factory=dict)  # 各 Agent 暫存區

    def time_limit(self) -> int | None:
        return EXAM_TIME_LIMIT.get(self.phase) if self.mode == "exam" else None

    def advance(self) -> Phase:
        idx = PHASE_ORDER.index(self.phase)
        if idx < len(PHASE_ORDER) - 1:
            self.phase = PHASE_ORDER[idx + 1]
        return self.phase
