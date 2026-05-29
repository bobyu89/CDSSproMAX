# Sub-Agent: transition — 過渡期模組

> **權重:標準(訓練流程的過渡階段)。**
> 問診與身評之間的 30 秒過渡期。彙整問診摘要 + 預載身評標準。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | transition |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session)、llm-adapter、scenario-schema |
| 被依賴模組 | 訓練迴圈 |
| 階段 | Phase.TRANSITION(問診後、身評前) |

> GitHub 路徑:`ticdss/flow/transition.py`。Notion:「TICDSS / transition / v1.0」。

---

## 設計決策

| 決策 | 採用方案 |
|------|---------|
| 是否獨立模組 | 是,獨立小模組(非單純倒數) |
| 過渡期工作 | 彙整問診摘要(供學員整理思緒)+ 預載身評標準(供 vision 用) |

---

## 過渡期做什麼

時間軸:問診 → **過渡期(30 秒)** → 身評。這 30 秒不是空等:

```
學員端:看問診摘要,整理思緒,準備器材
系統端:彙整問診結果、預載身評標準(standard_sequence 等)給 vision
```

考試模式 30 秒固定;練習模式不限時,學員按鈕進入身評。

---

## 產出檔案:`flow/transition.py`

```python
"""
過渡期模組
==========
問診與身評之間的過渡。彙整問診摘要供學員整理,
預載身評標準供 vision 使用。考試模式 30 秒,練習模式不限時。
"""

from llm.router import call_llm


async def run_transition(session):
    """
    過渡期主流程。回傳給前端顯示的摘要,並完成身評預載。
    """
    # 1. 彙整問診摘要(供學員整理思緒)
    inquiry_score = session.phase_scores.get("inquiry")
    summary = await _summarize_inquiry(session, inquiry_score)

    # 2. 預載身評標準到 session.scratch(供 vision 取用)
    _preload_exam_standard(session)

    return {
        "summary": summary,                         # 問診摘要
        "time_limit": session.time_limit(),         # 考試模式 30 秒;練習 None
        "next": "examination",
    }


async def _summarize_inquiry(session, inquiry_score):
    """把問診結果彙整成一段摘要,幫學員整理已知資訊。"""
    if inquiry_score is None:
        return "（無問診紀錄）"
    covered = inquiry_score.sub_items.get("dimensions", {})
    resp = await call_llm(
        "dialog",
        prompt=(f"學員問診涵蓋情況:{covered}\n"
                f"請用 3-4 句話彙整目前已知的病人資訊,"
                f"幫學員在進入身體評估前整理思緒。"),
        session=session)
    return resp.text


def _preload_exam_standard(session):
    """
    從情境預載身評標準到 scratch,供 vision 即用。
    scenario-schema 載入時已放 standard_sequence,此處確認就緒。
    """
    scenario = session.scratch.get("scenario")
    if scenario and scenario.examination:
        session.scratch["standard_sequence"] = \
            scenario.examination.standard_sequence
        session.scratch["required_regions"] = \
            scenario.examination.required_regions
```

---

## 在流程引擎的位置

```
問診階段結束(score 寫入 session)
   ↓
Phase.TRANSITION → run_transition(session)
   ├── 彙整問診摘要 → 前端顯示
   └── 預載身評標準 → session.scratch
   ↓ (考試 30 秒到 / 練習按鈕)
身評階段(vision 直接取用預載的 standard_sequence)
```

---

## 設計重點

- **不是空等,是準備**:過渡期同時服務學員(整理思緒)與系統(預載身評標準),
  讓身評一開始就有標準可比,不需臨時載入。
- **摘要幫學員減壓**:進入身評前看一段「目前已知什麼」,符合真實臨床
  「邊問邊整理」的節奏,也降低認知負荷。
- **預載解耦**:vision 需要的 standard_sequence 在過渡期就備好放 scratch,
  vision 不需自己去情境取,模組間靠 session 解耦。
- **雙模式時限**:考試 30 秒固定(time_limit 回 30),練習不限時(回 None),
  與 core 的 EXAM_TIME_LIMIT 一致。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:問診摘要彙整 + 身評標準預載 | 過渡期非空等,服務學員整理與系統預載 |

---

## 驗證方式

1. 問診結束後呼叫 run_transition,確認回傳問診摘要。
2. 確認 session.scratch["standard_sequence"] 已預載,vision 可直接用。
3. 考試模式確認 time_limit 回 30;練習模式回 None。
4. 無問診紀錄時,確認摘要優雅處理(不報錯)。
```
