# Sub-Agent: scenario-schema — 情境案例結構(情境契約)

> **權重:高(情境契約,三軌 Agent 的共同依賴,地位接近 core)。**
> 定義「一個訓練案例長什麼樣」。難度 = 混淆程度,三級,保留升級空間。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | scenario-schema |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract) |
| 被依賴模組 | inquiry / vision / diagnosis / case-generator / 難度調整 |

> GitHub 路徑:`ticdss/scenario/schema.py`。Notion:「TICDSS / scenario-schema / v1.0」。

---

## 為什麼需要這個模組

整個系統繞著「情境」轉:問診要比對標準答案、身評要比對標準順序、
診斷要比對正確排序。但這些標準存在哪、長什麼樣,先前未定義。
本模組是「情境契約」——如同 core 定義 Agent 契約,本模組定義案例契約。
三軌 Agent 都依賴它才知道要比對什麼;case-generator 依賴它才知道要產出什麼。

---

## 核心設計決策

| 決策 | 採用方案 |
|------|---------|
| 難度定義 | 難度 = 混淆程度(多容易誤判),非病情嚴重度 |
| 難度分級 | 三級(低/中/高混淆),數字編號保留升級空間 |
| 難度歸屬 | 案例的屬性,生成時決定;練習模式「升級」= 換更高混淆度案例 |

---

## 難度 = 混淆程度

難度衡量「這個案例多容易被誤判」,訓練的是抗誤導的臨床推理,
呼應診斷模組「rule out worst first」。

| 級別 | 混淆程度 | 特徵 | 範例 |
|------|---------|------|------|
| 1 | 低 | 典型表現、線索清楚、方向明確 | 胸痛+冒冷汗+左臂放射 → 教科書式 MI |
| 2 | 中 | 有干擾線索、需鑑別、仔細問可釐清 | 胸痛合併 GERD 病史,靠問診區分 |
| 3 | 高 | 非典型、多個合理診斷、易被誤導 | 年輕女性非典型胸痛,實為 PE 卻像焦慮 |

> 數字編號(1/2/3)保留升級空間:未來加第 4、5 級只需定義內容,不改架構。

### 製造混淆的四個手段

混淆程度透過以下手段實現(級別越高用得越多越強):

1. **干擾線索**:加入誘導往錯誤診斷的似是而非資訊
2. **非典型表現**:典型症狀不出現,真正診斷藏在不顯眼處
3. **鑑別接近**:多個診斷都說得通,需細究才能區分
4. **病人配合度**:高難度時病人不主動講關鍵資訊,需追問才得

---

## 產出檔案

### `scenario/schema.py`

```python
"""
情境案例結構(情境契約)
========================
定義一個訓練案例的完整結構。三軌 Agent 依此比對,
case-generator 依此產出。難度 = 混淆程度,三級保留升級。
"""

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
    chief_complaint: str                # 主訴
    persona: str                        # 性格/語氣描述
    initial_anxiety: float = 0.3        # 初始 anxiety(考試模式固定)
    cooperativeness: float = 1.0        # 配合度,1.0=主動講;低=要追問


@dataclass
class InquiryStandard:
    """問診標準答案(供 inquiry 比對)。"""
    # LQQOPERA 八維度,各維度的標準應答內容
    answers: dict = field(default_factory=dict)
    # 關鍵必問項(漏掉重扣)
    critical_questions: list = field(default_factory=list)
    # 干擾線索:會誘導往錯誤方向的資訊(製造混淆)
    distractors: list = field(default_factory=list)


@dataclass
class ExamStandard:
    """身體評估標準(供 vision 比對)。"""
    # 標準手法順序,如 ["視診","聽診","叩診","觸診"]
    standard_sequence: list = field(default_factory=list)
    # 必做的評估部位(解剖區域)
    required_regions: list = field(default_factory=list)
    # 該情境的關鍵發現(學員該找到的)
    key_findings: list = field(default_factory=list)


@dataclass
class DiagnosisStandard:
    """診斷標準(供 diagnosis 比對)。"""
    # 三個正確診斷,按危急度高→低排序
    # 每個含 name / reason / outcome / urgency(危急度 1-5)
    ranked_diagnoses: list = field(default_factory=list)
    # 必須排除的致命診斷(rule out worst)
    must_rule_out: list = field(default_factory=list)


@dataclass
class Scenario:
    """
    一個完整訓練案例。系統一切評核的「標準答案」來源。
    """
    scenario_id: str
    title: str                          # 如「胸痛案例」
    confusion_level: ConfusionLevel     # 難度 = 混淆程度(1/2/3)
    schema_version: str = SCHEMA_VERSION

    patient: StandardPatient = None
    inquiry: InquiryStandard = None
    examination: ExamStandard = None
    diagnosis: DiagnosisStandard = None

    # 混淆手段標記(說明本案例用了哪些製造混淆,供生成與審核)
    confusion_techniques: list = field(default_factory=list)
    # 標準病人標準順序,載入時寫入 session.scratch 供 vision 用
    metadata: dict = field(default_factory=dict)


def load_into_session(session, scenario: Scenario):
    """
    載入案例到 session。把各 Agent 需要的標準答案放到對應位置。
    """
    session.scenario_id = scenario.scenario_id
    session.difficulty = scenario.confusion_level
    session.anxiety = scenario.patient.initial_anxiety
    # vision 順序評分需要的標準順序
    session.scratch["standard_sequence"] = scenario.examination.standard_sequence
    # 各 Agent 從 session.scratch 取標準
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
```

---

## 設計重點

- **情境契約,接近 core 地位**:三軌 Agent 都依賴此結構才知道比對什麼。
  如同 StageAgent 是 Agent 契約,Scenario 是案例契約。
- **難度即混淆,參數化**:`confusion_level` 是案例屬性,`confusion_descriptor`
  把級別轉成具體手段強度(干擾數、是否非典型、配合度),
  case-generator 照此生成。第一級②(難度實現)由此解決。
- **保留升級**:ConfusionLevel 用數字,加 4、5 級只增 descriptor 內容,不改架構。
- **載入即就位**:`load_into_session` 把標準順序等寫入 session.scratch,
  vision 的 standard_sequence、診斷的 ranked_diagnoses 都從這裡來。
- **練習模式升級的真相**:迴圈後「升一級」= 載入一個更高 confusion_level
  的案例,而非即時改當前案例。

---

## 與其他模組的關係

```
scenario-schema(定義結構)
   ├── case-generator    依此結構生成案例
   ├── inquiry           讀 inquiry.answers / distractors 比對
   ├── vision            讀 examination.standard_sequence 評順序
   ├── diagnosis         讀 diagnosis.ranked_diagnoses 評排序
   └── 難度調整           迴圈後依表現載入不同 confusion_level 案例
```

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:情境契約 + 混淆三級難度 + 載入機制 | 補系統最大隱形缺口;難度=混淆程度定稿 |

---

## 驗證方式

1. 建立一個 level 1 案例,確認 confusion_descriptor 回傳低混淆參數。
2. load_into_session 後,確認 session.scratch["standard_sequence"] 正確寫入。
3. 確認 diagnosis 能從 session 取得 ranked_diagnoses 比對。
4. 建 level 3 案例,確認 distractors、非典型、低配合度都標記。
5. 確認加一個假想的 level 4 只需擴充 descriptor,不改 Scenario 結構。
```
