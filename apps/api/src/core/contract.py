"""
契約定義 — 系統最底層約定 (Builder core.md / contract-v1.0)
============================================================
不含執行邏輯,只定義「資料長什麼樣」「介面要實作什麼」。
所有模組依賴此契約,故必須最穩定。

對應 docs/builder-spec/sub-agents/core.md。任何變動 → 版本 +0.1 並記錄。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict

CONTRACT_VERSION = "1.0"


# ── Payload 格式(明確定義各階段輸入) ──────────────────────────────────


class InquiryPayload(TypedDict):
    """問診階段輸入。"""

    text: str  # STT 轉好的學員語句
    silence: float  # 語音停頓秒數
    prosody: dict | None  # 語速/音量分析


class VisionPayload(TypedDict):
    """身評階段輸入。"""

    intent: str  # 意圖宣告,如「評估左下肺葉」
    frame: str  # base64 影格
    check_technique: bool  # 是否需判斷手法


class DiagnosisPayload(TypedDict):
    """診斷階段輸入。"""

    text: str  # 學員診斷與處置陳述


# ── 評分輸出格式 ───────────────────────────────────────────────────────


@dataclass
class StageScore:
    """
    階段 Agent 的評分輸出(inquiry/vision/diagnosis 用)。
    代表「一個訓練階段」的表現。
    """

    stage: str
    raw_score: float  # 0–100
    sub_items: dict = field(default_factory=dict)
    weak_points: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    contract_version: str = CONTRACT_VERSION  # 相容性檢查用


@dataclass
class EvalResult:
    """
    評分代理的輸出(realtime/DUAT/output 用)。
    與 StageScore 區隔:StageScore 是「階段表現」,
    EvalResult 是「對表現的評估與加工」。
    """

    source: str  # 哪個評分代理產出
    payload: dict = field(default_factory=dict)  # 評估內容(格式依代理而定)
    contract_version: str = CONTRACT_VERSION


# ── 階段 Agent 介面 ─────────────────────────────────────────────────────


class StageAgent(ABC):
    """
    問診/身評/診斷必須實作的介面。
    四個生命週期方法的輸入輸出格式於上方明確定義。
    """

    stage_name: str = "base"
    rubric_version: str = "v1.0"
    contract_version: str = CONTRACT_VERSION

    @abstractmethod
    def on_enter(self, session) -> dict:
        """進入階段。回傳給前端的初始狀態(如提示文字)。"""
        ...

    @abstractmethod
    async def handle_input(self, session, payload: dict) -> dict:
        """處理輸入(payload 格式見上方 TypedDict),回傳即時回應。"""
        ...

    @abstractmethod
    def score(self, session) -> StageScore:
        """階段結束評分,回傳 StageScore。"""
        ...

    @abstractmethod
    def on_exit(self, session) -> dict:
        """離開階段,回傳摘要(供過渡期顯示)。"""
        ...
