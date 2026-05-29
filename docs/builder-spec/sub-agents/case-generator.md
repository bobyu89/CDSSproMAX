# Sub-Agent: case-generator — 模擬案例生成器

> **權重:標準偏高(案例供給來源,依賴 scenario-schema)。**
> AI 生成案例草稿 → 自我品質檢查 → 專家後台審核 → 常駐案例庫。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | case-generator |
| 模組版本 | v1.1 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、scenario-schema、llm-adapter、SQL 資料庫 |
| 被依賴模組 | 訓練迴圈(抽案例)、難度調整 |

> GitHub 路徑:`ticdss/scenario/generator.py`。Notion:「TICDSS / case-generator / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 自動化程度 | AI 生成草稿 → 專家後台審核 → 通過後成常駐案例 |
| 即時/建庫 | 預先建庫:可批次生成存入待審,審核通過的進常駐庫 |
| 品質把關 | 兩道關:AI 自我品質檢查(減輕專家負擔)+ 專家人工審核 |

## 案例池與模式規則

| 模式 | 可用案例池 | 沒案例時 |
|------|-----------|---------|
| 練習模式 | approved 優先 → 補 draft(標實驗性)→ 即時生成保底 | 不開天窗,一定有案例 |
| OSCE 模式 | 只用 approved | 誠實告知無正式案例,不硬給 |

> 解決冷啟動:系統初期 approved 少時,練習模式仍可用 draft 或即時生成的
> 實驗性案例(明確標示),OSCE 則堅守只用審核過的,確保考核可信。

---

## 為什麼是「建庫 + 兩道把關」

你的工作流決定了架構:
```
AI 生成草稿 → 專家審核 → 通過 → 常駐案例庫
```
- 要經專家審核才能用 → 必然預先建庫,不能即時生成沒審過的案例給學員。
- AI 先自檢 → 專家只看「AI 認為合理的」,不用看爛草稿,省專家時間。

---

## 完整流程

```
輸入:主題(胸痛)+ 混淆級別(1/2/3)
   ↓
① AI 生成案例草稿(符合 scenario-schema 結構)
   ↓
② AI 自我品質檢查(臨床合理?難度符合?診斷排序對?)
   ↓ 通過
③ 寫入 SQL,狀態 = draft(待審佇列)
   ↓ 專家後台審核
④ 專家通過 → 狀態 = approved → 進常駐案例庫
   ↓
⑤ 訓練時從 approved 案例抽(依主題、難度)
```

案例狀態:`draft`(待審)/ `approved`(常駐)/ `rejected`(退回)。
只有 approved 會被學員用到。

---

## 產出檔案

### `scenario/generator.py`

```python
"""
模擬案例生成器
==============
AI 生成符合 scenario-schema 的案例草稿 → 自我品質檢查 →
寫入 SQL 待審 → 專家審核通過後成常駐案例。
"""

from scenario.schema import (Scenario, StandardPatient, InquiryStandard,
                             ExamStandard, DiagnosisStandard,
                             confusion_descriptor)
from llm.router import call_llm
import uuid


async def generate_case_draft(topic: str, level: int, session=None):
    """
    依主題與混淆級別生成案例草稿。
    用 confusion_descriptor 決定該級別的混淆手段強度。
    """
    desc = confusion_descriptor(level)      # 該級別的混淆參數

    resp = await call_llm(
        "diagnosis",
        prompt=(
            f"請生成一個臨床訓練案例,主題:{topic},"
            f"混淆程度:{desc['desc']}。\n"
            f"混淆手段:干擾線索 {desc['distractors']} 個、"
            f"{'非典型表現' if desc['atypical'] else '典型表現'}、"
            f"病人配合度 {desc['cooperativeness']}。\n"
            f"請依以下結構回傳完整 JSON:\n"
            f"- patient: 年齡/性別/主訴/性格/初始anxiety/配合度\n"
            f"- inquiry: LQQOPERA 八維度標準應答、關鍵必問項、干擾線索\n"
            f"- examination: 標準手法順序、必做部位、關鍵發現\n"
            f"- diagnosis: 三個診斷(按危急度排序,各含原因/結果/危急度)、"
            f"必須排除的致命診斷\n"
            f"- confusion_techniques: 本案例用了哪些混淆手段"),
        session=session)

    data = _parse(resp.text)
    scenario = _build_scenario(topic, level, data)
    return scenario


async def quality_check(scenario: Scenario, session=None) -> dict:
    """
    AI 自我品質檢查(第一道關)。
    檢查臨床合理性、難度是否符合、診斷排序是否正確。
    """
    resp = await call_llm(
        "diagnosis",
        prompt=(
            f"請審查以下訓練案例的品質,回傳JSON:\n{_serialize(scenario)}\n"
            f"檢查:1)臨床是否合理(症狀/診斷/檢查相符)"
            f"2)混淆程度是否符合宣稱級別 {scenario.confusion_level}"
            f"3)三診斷危急度排序是否正確"
            f"4)是否有矛盾或不合理處\n"
            f'回傳:{{"pass":true/false,"issues":[...],"suggestions":[...]}}'),
        system="你是資深臨床教師,嚴格把關案例品質。",
        session=session)
    return _parse(resp.text)


async def create_case(topic, level, db, session=None):
    """
    完整流程:生成 → 自檢 → 寫入待審佇列。
    """
    scenario = await generate_case_draft(topic, level, session)
    qc = await quality_check(scenario, session)

    if not qc.get("pass"):
        # 自檢未過,可重生成或附問題供人工參考
        return {"status": "qc_failed", "issues": qc.get("issues"),
                "scenario": scenario}

    # 自檢通過 → 寫入 SQL,狀態 draft,等專家審核
    case_id = _save_draft(db, scenario, qc)
    return {"status": "draft", "case_id": case_id, "scenario": scenario}


# ── 專家審核(後台呼叫) ──
def approve_case(db, case_id):
    """專家審核通過 → 狀態改 approved,成常駐案例。"""
    db.execute("UPDATE scenarios SET status='approved' WHERE id=?", (case_id,))


def reject_case(db, case_id, reason):
    """專家退回 → 狀態改 rejected。"""
    db.execute("UPDATE scenarios SET status='rejected', "
               "reject_reason=? WHERE id=?", (reason, case_id))


# ── 訓練時抽案例(依模式區分案例池) ──
async def pick_case(db, mode: str, topic=None, level=None, session=None):
    """
    依模式抽案例,解決冷啟動,避免開天窗。

    練習模式:優先 approved → 不夠補 draft(實驗性)→ 都沒有則即時生成保底
    OSCE 模式:只用 approved → 沒有則誠實告知,不硬給
    """
    if mode == "exam":
        # OSCE 只用審核過的,確保考核公平可信
        case = _query_one(db, ["approved"], topic, level)
        if case is None:
            return {"status": "no_case",
                    "message": "此主題/難度尚無正式案例,無法進行 OSCE"}
        return {"status": "ok", "experimental": False, "case": case}

    # 練習模式:approved 優先
    case = _query_one(db, ["approved"], topic, level)
    if case:
        return {"status": "ok", "experimental": False, "case": case}

    # approved 不夠 → 補 draft(標示實驗性)
    case = _query_one(db, ["draft"], topic, level)
    if case:
        return {"status": "ok", "experimental": True, "case": case,
                "notice": "這是實驗性案例,可能有不完美之處,"
                          "若發現問題歡迎回報"}

    # 都沒有 → 即時生成一個 draft 保底,不開天窗
    result = await create_case(topic or "綜合", level or 1, db, session)
    return {"status": "ok", "experimental": True,
            "case": result.get("scenario"),
            "notice": "這是即時生成的實驗性案例"}


def _query_one(db, statuses, topic, level):
    """從指定狀態池抽一個。"""
    placeholders = ",".join("?" * len(statuses))
    q = f"SELECT * FROM scenarios WHERE status IN ({placeholders})"
    params = list(statuses)
    if topic:
        q += " AND topic=?"; params.append(topic)
    if level:
        q += " AND confusion_level=?"; params.append(level)
    q += " ORDER BY RANDOM() LIMIT 1"
    return db.query_one(q, params)


# ── 案例庫批次管理 ──
async def batch_generate(db, plan: list, session=None):
    """
    預先批次生成多個案例存入待審佇列。
    plan: [{"topic": "胸痛", "level": 2, "count": 3}, ...]
    生成後皆為 draft 狀態,等專家審核。
    """
    created = []
    for item in plan:
        for _ in range(item.get("count", 1)):
            result = await create_case(
                item["topic"], item["level"], db, session)
            created.append(result)
    return {"generated": len(created), "items": created}


def library_stats(db):
    """案例庫總覽:各狀態、各主題、各難度的數量(供後台儀表板)。"""
    return {
        "by_status": db.query(
            "SELECT status, COUNT(*) FROM scenarios GROUP BY status"),
        "by_topic": db.query(
            "SELECT topic, status, COUNT(*) FROM scenarios "
            "GROUP BY topic, status"),
        "by_level": db.query(
            "SELECT confusion_level, status, COUNT(*) FROM scenarios "
            "GROUP BY confusion_level, status"),
    }


def pending_review(db, limit=20):
    """待審佇列:列出 draft 狀態案例供專家後台審核。"""
    return db.query(
        "SELECT id, topic, confusion_level, qc_result, created_at "
        "FROM scenarios WHERE status='draft' ORDER BY created_at LIMIT ?",
        [limit])



# ── 內部 ──
def _build_scenario(topic, level, data):
    p = data.get("patient", {})
    return Scenario(
        scenario_id=str(uuid.uuid4()),
        title=f"{topic}案例",
        confusion_level=level,
        patient=StandardPatient(
            age=p.get("age", 50), gender=p.get("gender", ""),
            chief_complaint=p.get("chief_complaint", ""),
            persona=p.get("persona", ""),
            initial_anxiety=p.get("initial_anxiety", 0.3),
            cooperativeness=p.get("cooperativeness", 1.0)),
        inquiry=InquiryStandard(**data.get("inquiry", {})),
        examination=ExamStandard(**data.get("examination", {})),
        diagnosis=DiagnosisStandard(**data.get("diagnosis", {})),
        confusion_techniques=data.get("confusion_techniques", []))


def _save_draft(db, scenario, qc):
    cid = scenario.scenario_id
    db.execute(
        "INSERT INTO scenarios (id, topic, confusion_level, status, "
        "content, qc_result) VALUES (?,?,?,?,?,?)",
        (cid, scenario.title, scenario.confusion_level, "draft",
         _serialize(scenario), str(qc)))
    return cid


def _parse(txt):
    import json
    try: return json.loads(txt)
    except Exception: return {}

def _serialize(scenario):
    import json
    from dataclasses import asdict
    return json.dumps(asdict(scenario), ensure_ascii=False)
```

---

## SQL 資料表(scenarios)

```sql
CREATE TABLE scenarios (
    id              TEXT PRIMARY KEY,
    topic           TEXT,
    confusion_level INTEGER,         -- 1/2/3
    status          TEXT,            -- draft / approved / rejected
    content         TEXT,            -- 序列化的 Scenario JSON
    qc_result       TEXT,            -- AI 自檢結果
    reject_reason   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 設計重點

- **混淆級別驅動生成**:`confusion_descriptor(level)` 把難度級別轉成具體
  混淆參數(干擾數、是否非典型、配合度),餵給 LLM 生成對應難度的案例。
  難度與生成直接掛鉤。
- **兩道品質把關**:AI 自檢擋掉明顯不合理(省專家時間),專家審核做最終確認。
  只有 approved 會被學員抽到,確保臨床品質。
- **建庫而非即時**:審核流程決定必須預先建庫。訓練時 `pick_case` 從 approved
  抽,依主題與難度,支援練習模式「升級 = 抽更高 confusion_level 案例」。
- **狀態機清晰**:draft → approved/rejected,專家後台只需 approve/reject。
- **依賴 scenario-schema**:生成的案例必為合法 Scenario 結構,三軌 Agent
  可直接使用,case-generator 與 schema 的關係如同實作與契約。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:生成→自檢→待審→專家核可→常駐;混淆級別驅動 | 解決「情境從哪來」;對接專家審核工作流 |
| 2026-05-29 | v1.1 | 加案例庫批次管理 + 模式案例池規則(練習可用draft、OSCE只用approved)+ 即時生成保底 | 解決冷啟動,避免無案例可用 |

---

## 驗證方式

1. 給「胸痛 + level 3」,確認生成案例的 distractors、非典型、低配合度符合。
2. 確認生成案例為合法 Scenario,三軌 Agent 可載入。
3. quality_check 對一個故意矛盾的案例,確認回 pass=false 並列問題。
4. create_case 自檢通過後,確認寫入 SQL 狀態為 draft。
5. approve_case 後,確認 pick_case 能抽到該案例;draft 狀態抽不到。
6. pick_case 指定 level=2,確認只抽到 level 2 的 approved 案例。
7. 練習模式無 approved 時,確認抽到 draft 並回傳 experimental=True 與提示。
8. 練習模式完全無案例時,確認即時生成保底,不開天窗。
9. OSCE 模式無 approved 時,確認回 no_case,不給 draft。
10. batch_generate 餵入計畫,確認批次生成對應數量的 draft 案例。
11. library_stats 確認回傳各狀態/主題/難度的統計。
```
