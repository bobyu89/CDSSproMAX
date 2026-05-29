# Sub-Agent: core — 系統核心(契約 + 資料中樞 + 流程引擎)

> **權重:最高。** 任何其他模組開發前,必須先讀本檔,確認契約。
> core 的契約一旦變動,所有模組都要對齊,因此修改最謹慎。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | core |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | 無(最底層) |
| 被依賴模組 | 全部 |

> 同步至 GitHub 時,此模組置於 `ticdss/core/`;Notion 設計紀錄頁標題建議:
> 「TICDSS / core / contract-v1.0」。每次契約變動,版本號 +0.1 並記錄於下方設計紀錄。

---

## 職責

core 統合三件事,作為全系統地基:

1. **契約(contract)** — 定義 `StageAgent` 介面與 `StageScore`、`EvalResult` 格式。
2. **資料中樞(session-state)** — 定義 `TrainingSession`,全系統共用的狀態物件。
3. **流程引擎(flow-engine)** — 狀態機、註冊表、階段調度。

> 三者目前統合於 core(兩層架構)。已預留協調者接口(見文末),
> 未來任一部分長大時,可升級拆出獨立協調者,不影響其他模組。

---

## 產出檔案

### 1. `core/contract.py` — 契約定義

```python
"""
契約定義 — 系統最底層約定
==========================
不含執行邏輯,只定義「資料長什麼樣」「介面要實作什麼」。
所有模組依賴此契約,故必須最穩定。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict, Literal

CONTRACT_VERSION = "1.0"


# ── Payload 格式(明確定義各階段輸入) ──

class InquiryPayload(TypedDict):
    """問診階段輸入。"""
    text: str                  # STT 轉好的學員語句
    silence: float             # 語音停頓秒數
    prosody: dict | None       # 語速/音量分析

class VisionPayload(TypedDict):
    """身評階段輸入。"""
    intent: str                # 意圖宣告,如「評估左下肺葉」
    frame: str                 # base64 影格
    check_technique: bool      # 是否需判斷手法

class DiagnosisPayload(TypedDict):
    """診斷階段輸入。"""
    text: str                  # 學員診斷與處置陳述


# ── 評分輸出格式 ──

@dataclass
class StageScore:
    """
    階段 Agent 的評分輸出(inquiry/vision/diagnosis 用)。
    代表「一個訓練階段」的表現。
    """
    stage: str
    raw_score: float                                 # 0–100
    sub_items: dict = field(default_factory=dict)
    weak_points: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    contract_version: str = CONTRACT_VERSION         # 相容性檢查用


@dataclass
class EvalResult:
    """
    評分代理的輸出(realtime/DUAT/output 用)。
    與 StageScore 區隔:StageScore 是「階段表現」,
    EvalResult 是「對表現的評估與加工」。
    """
    source: str                                      # 哪個評分代理產出
    payload: dict = field(default_factory=dict)      # 評估內容(格式依代理而定)
    contract_version: str = CONTRACT_VERSION


# ── 階段 Agent 介面 ──

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
```

### 2. `core/session.py` — 資料中樞

```python
"""
資料中樞 — 全系統共用的訓練狀態
================================
所有模組讀寫同一個 TrainingSession:
問診寫 anxiety、fusion 寫 signals、評分讀 phase_scores。
"""

from enum import Enum
from dataclasses import dataclass, field


class Phase(str, Enum):
    SCENARIO   = "scenario"
    INQUIRY    = "inquiry"
    TRANSITION = "transition"
    EXAM       = "examination"
    DIAGNOSIS  = "diagnosis"
    REVIEW     = "review"


EXAM_TIME_LIMIT = {           # 考試模式各階段時限(秒)
    Phase.INQUIRY:    360,
    Phase.TRANSITION:  30,
    Phase.EXAM:       360,
    Phase.DIAGNOSIS:  120,
}

PHASE_ORDER = [Phase.SCENARIO, Phase.INQUIRY, Phase.TRANSITION,
               Phase.EXAM, Phase.DIAGNOSIS, Phase.REVIEW]


@dataclass
class TrainingSession:
    mode: str                                       # 'practice' | 'exam'
    scenario_id: str
    phase: Phase = Phase.SCENARIO
    difficulty: int = 1
    anxiety: float = 0.3
    hrv_baseline: float = None
    signals: list = field(default_factory=list)
    phase_scores: dict = field(default_factory=dict)
    scratch: dict = field(default_factory=dict)     # 各 Agent 暫存區

    def time_limit(self):
        return EXAM_TIME_LIMIT.get(self.phase) if self.mode == "exam" else None

    def advance(self):
        idx = PHASE_ORDER.index(self.phase)
        if idx < len(PHASE_ORDER) - 1:
            self.phase = PHASE_ORDER[idx + 1]
        return self.phase
```

### 3. `core/flow.py` — 流程引擎 + 註冊表

```python
"""
流程引擎 + 註冊表
==================
流程引擎只認契約,不認任何階段的內部實作。
註冊表是熱插拔的開關:換版本 = 改一行註冊。
"""

from core.contract import StageAgent


class AgentRegistry:
    """熱插拔核心:管理階段名稱 → Agent 類別的對應。"""
    def __init__(self):
        self._reg: dict[str, type[StageAgent]] = {}

    def register(self, stage: str, agent_cls: type[StageAgent]):
        # 相容性檢查:確認 Agent 遵守的契約版本
        self._reg[stage] = agent_cls

    def get_agent(self, stage: str):
        cls = self._reg.get(stage)
        return cls() if cls else None


registry = AgentRegistry()


async def run_phase(session, receive_inputs):
    """
    流程引擎核心。任何 Agent 被替換都不需修改這段,
    因為它只呼叫契約定義的四個方法。
    """
    agent = registry.get_agent(session.phase.value)
    if agent is None:
        return                              # 無對應 Agent 的階段(如過渡期)
    yield {"type": "enter", "state": agent.on_enter(session)}
    async for payload in receive_inputs(session):
        resp = await agent.handle_input(session, payload)
        yield {"type": "response", "data": resp}
    score = agent.score(session)
    session.phase_scores[session.phase.value] = score
    agent.on_exit(session)
    yield {"type": "score", "score": score}
```

---

## 預留:協調者升級接口(未來用)

> 目前兩層架構,core 直接協調所有模組。當某功能群(如 scoring)
> 長大到需要自己的協調者時,依下列接口升級,不影響其他模組:

```python
# 未來新增 core/orchestrator_base.py
class GroupOrchestrator(ABC):
    """群組協調者基底。未來各功能群協調者繼承此類。"""
    group_name: str
    @abstractmethod
    async def coordinate(self, session, members: list) -> dict: ...
```

升級時:把該群組的成員註冊到對應協調者,core 改為呼叫協調者而非個別成員。
因為大家都遵守契約,此升級為局部變動。

---

## 設計重點

- **契約 / session / flow 三者統合於 core,但檔案分開**(contract.py / session.py / flow.py),
  邏輯上是一體(高權重地基),實體上仍可各自維護。
- `StageScore` 與 `EvalResult` 刻意分開:前者是「階段表現」,
  後者是「對表現的評估加工」,讓評分代理與階段代理職責清晰。
- `contract_version` 欄位讓未來熱插拔時可做相容性檢查。
- `scratch` 暫存區讓各 Agent 有地方放中間狀態,不污染 session 主結構。

---

## 設計紀錄(同步 Notion / GitHub 用)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | contract-v1.0 | 初版:契約 + session + flow 統合於 core | 兩層架構定稿,預留協調者升級接口 |

> **下次更新時,在此表新增一列。** GitHub commit message 建議格式:
> `core: contract-v1.1 — <變更摘要>`

---

## 驗證方式

1. 寫一個 `DummyAgent(StageAgent)`,實作四個方法。
2. `registry.register("inquiry", DummyAgent)`。
3. 跑 `run_phase`,確認流程引擎在不知道實作細節下完成一個階段。
4. 確認 `score()` 回傳的 `StageScore` 含正確 `contract_version`。
