# Sub-Agent: duat-flow — DUAT 協調流程

> **權重:標準偏高(協調 DUAT 五代理的串接與並行)。**
> 迴圈結束後的深度驗證總流程。O → E‖S → A → M。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | duat-flow |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、duat-observe/evaluate/synthesize/analyze/memory |
| 被依賴模組 | 訓練迴圈(迴圈結束)、output 五種輸出 |

> GitHub 路徑:`ticdss/scoring/duat/flow.py`。Notion:「TICDSS / duat-flow / v1.0」。

---

## 設計決策(DUAT 整體)

| 決策 | 採用方案 |
|------|---------|
| LLM 使用 | 五代理皆用 LLM(最智能);對應 System 2 深度分析 |
| 執行方式 | 部分並行:O → (E‖S) → A → M |
| M-Agent 歷程 | 第一版即做;有歷程則比對,無歷程則只描述本次 |

---

## 並行依賴圖

```
O-Agent 觀察(先跑,彙整全程資料)
    ↓
┌─────────┴─────────┐
E-Agent 評估    S-Agent 綜整     ← 並行(都只依賴 O)
└─────────┬─────────┘
    ↓
A-Agent 分析(依賴 E + S)
    ↓
M-Agent 記憶(依賴 A,比對歷程)
    ↓
最終報告 → output 五種輸出
```

---

## 產出檔案:`scoring/duat/flow.py`

```python
"""
DUAT 協調流程
=============
迴圈結束後的深度驗證。O → (E‖S) → A → M。
五代理皆用 LLM,對應 Kahneman System 2 深度分析。
"""

import asyncio
from scoring.duat.observe import run_observe
from scoring.duat.evaluate import run_evaluate
from scoring.duat.synthesize import run_synthesize
from scoring.duat.analyze import run_analyze
from scoring.duat.memory import run_memory


async def deep_verify(session, student_id=None):
    """
    DUAT 主流程。回傳最終深度驗證結果(供 output 使用)。
    """
    # 1. O-Agent 先跑:彙整全程資料
    observation = await run_observe(session)

    # 2. E-Agent 與 S-Agent 並行(都只依賴 O)
    evaluation, synthesis = await asyncio.gather(
        run_evaluate(session, observation),
        run_synthesize(session, observation))

    # 3. A-Agent:依賴 E + S
    analysis = await run_analyze(session, evaluation, synthesis)

    # 4. M-Agent:依賴 A,比對歷程(無歷程則只描述本次)
    memory = await run_memory(session, analysis, student_id)

    return {
        "observation": observation,
        "evaluation": evaluation,
        "synthesis": synthesis,
        "analysis": analysis,
        "memory": memory,
    }
```

---

## 設計重點

- **部分並行省時間**:E 與 S 都只依賴 O,用 `asyncio.gather` 同時跑,
  比全串接快。A 等 E+S,M 收尾,依賴不搞錯。
- **五代理介面統一**:每個 `run_xxx` 都吃 session + 前序輸出,回 EvalResult,
  遵守 core 契約,可各自獨立替換。
- **對應 System 2**:五代理皆 LLM,代表「慢思考」的深度驗證,
  與 realtime-scorer(System 1 快思考)形成雙歷程。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:O→(E‖S)→A→M 並行協調 | DUAT 整體決策定稿 |

---

## 驗證方式

1. 確認 O 先完成才啟動 E、S。
2. 確認 E 與 S 並行(asyncio.gather)。
3. 確認 A 等 E+S 都好才跑,M 最後。
4. 確認回傳含五代理各自的 EvalResult。
```
