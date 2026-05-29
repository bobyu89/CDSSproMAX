"""
情境案例結構(情境契約) (Builder scenario-schema.md / contract-v1.0)
====================================================================
定義一個訓練案例的完整結構。三軌 Agent 依此比對,case-generator 依此產出。
難度 = 混淆程度,三級保留升級。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SCHEMA_VERSION = "1.0"

# 混淆程度等級(保留升級空間:未來可加 4、5)
ConfusionLevel = Literal[1, 2, 3]


@dataclass
class StandardPatient:
    """標準病人設定。"""

    age: int
    gender: str
    chief_complaint: str  # 主訴
    persona: str  # 性格/語氣描述
    initial_anxiety: float = 0.3  # 初始 anxiety(考試模式固定)
    cooperativeness: float = 1.0  # 配合度,1.0=主動講;低=要追問


@dataclass
class InquiryStandard:
    """問診標準答案(供 inquiry 比對)。"""

    answers: dict = field(default_factory=dict)  # LQQOPERA 八維度標準應答
    critical_questions: list = field(default_factory=list)  # 關鍵必問項
    distractors: list = field(default_factory=list)  # 干擾線索(製造混淆)


@dataclass
class ExamStandard:
    """身體評估標準(供 vision 比對)。"""

    standard_sequence: list = field(default_factory=list)  # 如 ["視診","聽診","叩診","觸診"]
    required_regions: list = field(default_factory=list)  # 必做評估部位
    key_findings: list = field(default_factory=list)  # 關鍵發現


@dataclass
class DiagnosisStandard:
    """診斷標準(供 diagnosis 比對)。"""

    # 三個正確診斷,按危急度高→低排序;每個含 name/reason/outcome/urgency(1-5)
    ranked_diagnoses: list = field(default_factory=list)
    must_rule_out: list = field(default_factory=list)  # 必排除的致命診斷


@dataclass
class Scenario:
    """一個完整訓練案例。系統一切評核的「標準答案」來源。"""

    scenario_id: str
    title: str
    confusion_level: ConfusionLevel
    schema_version: str = SCHEMA_VERSION

    patient: StandardPatient | None = None
    inquiry: InquiryStandard | None = None
    examination: ExamStandard | None = None
    diagnosis: DiagnosisStandard | None = None

    confusion_techniques: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def load_into_session(session, scenario: Scenario):
    """載入案例到 session,把各 Agent 需要的標準答案放到對應位置。"""
    session.scenario_id = scenario.scenario_id
    session.difficulty = scenario.confusion_level
    if scenario.patient is not None:
        session.anxiety = scenario.patient.initial_anxiety
    if scenario.examination is not None:
        session.scratch["standard_sequence"] = scenario.examination.standard_sequence
    session.scratch["scenario"] = scenario
    return session


def confusion_descriptor(level: ConfusionLevel) -> dict:
    """回傳某混淆級別應使用的手段強度(供 case-generator 參照)。"""
    return {
        1: {"distractors": 0, "atypical": False, "close_ddx": False,
            "cooperativeness": 1.0, "desc": "低混淆:典型、線索清楚"},
        2: {"distractors": 2, "atypical": False, "close_ddx": True,
            "cooperativeness": 0.7, "desc": "中混淆:有干擾、需鑑別"},
        3: {"distractors": 3, "atypical": True, "close_ddx": True,
            "cooperativeness": 0.4, "desc": "高混淆:非典型、易誤導"},
    }[level]
