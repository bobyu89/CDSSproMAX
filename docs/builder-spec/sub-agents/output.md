# Sub-Agent: output — 五種輸出 + 協調者

> **權重:output-orchestrator 標準偏高(統籌五輸出一致性);五種輸出各為標準。**
> 把評分資料轉成六種呈現(五種輸出,RAG 講義獨立)。共用一份 DUAT 結果,杜絕數字矛盾。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組群 | output-orchestrator / narrative / radar / weakness / keyfocus / stress |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、duat-flow、llm-adapter、fusion-classifier、vision |
| 被依賴模組 | 前端結果頁、rag-note(取用弱點) |

> GitHub 路徑:`ticdss/output/`。Notion:各輸出一頁。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 分數來源 | 五種輸出共用同一份 DUAT 結果,不各自重算,杜絕數字矛盾 |
| 協調方式 | 設 output-orchestrator 統籌,管理依賴順序與一致性 |
| 反事實回饋 | 放 output-narrative(評語裡順帶「如果當時…」) |

---

## 為什麼這裡需要協調者

output-orchestrator 讓系統多一個能力:**確保五種輸出彼此不矛盾**。
- 共用一份真相來源(DUAT 結果 + StageScore)
- 管理依賴:弱點分析 → 重點提示(重點從弱點挑,不各算各的)
- 確保評語呼應雷達圖、壓力曲線的數字

這是「為能力而加」,非「為組織而加」,故合理。

---

## 依賴關係

```
output-orchestrator
   │ 取得共用資料(DUAT 結果 + StageScore + fusion_state + 軌跡)
   ├── output-radar       獨立(吃 StageScore 分數)
   ├── output-stress      獨立(吃 fusion_state + HRV)
   ├── output-weakness    獨立(吃 weak_points + DUAT analysis)
   │      ↓
   ├── output-keyfocus    依賴 weakness(從弱點挑最重要)
   └── output-narrative   最後(呼應上述所有 + 反事實回饋)
```

---

## 產出檔案

### 0. `output/orchestrator.py` — 協調者

```python
"""
輸出協調者
==========
統籌五種輸出,共用一份 DUAT 結果,確保彼此不矛盾。
管理依賴:weakness → keyfocus;narrative 最後呼應全部。
"""

from output.radar import build_radar
from output.stress import build_stress
from output.weakness import build_weakness
from output.keyfocus import build_keyfocus
from output.narrative import build_narrative


async def build_all_outputs(session, duat_result):
    """產出五種輸出。duat_result 為共用真相來源。"""
    # 獨立的先算(可並行)
    radar = build_radar(session)
    stress = build_stress(session)
    weakness = build_weakness(session, duat_result)

    # keyfocus 依賴 weakness
    keyfocus = build_keyfocus(weakness)

    # narrative 最後,呼應全部 + 反事實回饋
    narrative = await build_narrative(
        session, duat_result, radar, weakness, keyfocus, stress)

    return {
        "narrative": narrative,    # ① 自然語言評語(含反事實)
        "radar": radar,            # ② 雷達圖
        "weakness": weakness,      # ③ 弱點分析
        "keyfocus": keyfocus,      # ④ 重點提示
        "stress": stress,          # ⑤ 壓力曲線
        # ⑥ RAG 講義由 rag-note 模組另外產生
    }
```

### 1. `output/radar.py` — ② 雷達圖

```python
"""雷達圖:問診/身評/診斷/溝通四維度。吃 StageScore 分數。"""

def build_radar(session):
    ps = session.phase_scores
    return {
        "type": "radar",
        "dimensions": {
            "問診": ps.get("inquiry").raw_score if ps.get("inquiry") else 0,
            "身評": ps.get("examination").raw_score if ps.get("examination") else 0,
            "診斷": ps.get("diagnosis").raw_score if ps.get("diagnosis") else 0,
            "溝通": _communication(session),
        },
    }

def _communication(session):
    # 溝通分數:綜合問診品質與停頓流暢度
    inq = session.phase_scores.get("inquiry")
    if not inq:
        return 0
    return inq.sub_items.get("quality", 0)
```

### 2. `output/stress.py` — ⑤ HRV 壓力曲線

```python
"""壓力曲線:讀 fusion_state 時序 + HRV,產出壓力隨時間變化。"""

def build_stress(session):
    # fusion 狀態時序 → 壓力等級
    stress_map = {"anxious": 3, "ambiguous": 2,
                  "low_engagement": 1, "flow": 0}
    curve = [
        {"t": s["timestamp"], "level": stress_map.get(s["state"], 2),
         "state": s["state"]}
        for s in session.signals if s["type"] == "fusion_state"
    ]
    # HRV 原始值疊加(供細看)
    hrv = [{"t": s["timestamp"], "rmssd": s["rmssd"]}
           for s in session.signals if s["type"] == "hrv"]
    # 標示壓力峰值對應的階段(考試模式的壓力軌跡報告)
    peak = max(curve, key=lambda c: c["level"]) if curve else None
    return {"type": "stress_curve", "curve": curve,
            "hrv": hrv, "peak": peak}
```

### 3. `output/weakness.py` — ③ 弱點分析

```python
"""弱點分析:彙整三軌 weak_points + DUAT analysis,排序。"""

def build_weakness(session, duat_result):
    # 共用真相來源:三軌弱點 + DUAT 分析
    weak = []
    for ss in session.phase_scores.values():
        weak.extend(ss.weak_points)
    # DUAT analysis 已排序的關鍵弱點優先
    analysis = duat_result["analysis"].payload.get("analysis", "")
    return {"type": "weakness",
            "items": weak,                 # 各軌原始弱點
            "duat_analysis": analysis}     # DUAT 排序後的深度分析
```

### 4. `output/keyfocus.py` — ④ 重點提示

```python
"""重點提示:從弱點分析挑最該注意的一個(依賴 weakness)。"""

def build_keyfocus(weakness):
    items = weakness["items"]
    # 重點 = 弱點清單第一項(DUAT 已排序);無弱點則給正向
    top = items[0] if items else "整體表現良好,維持目前水準"
    return {"type": "keyfocus", "focus": top,
            "rationale": weakness["duat_analysis"]}
```

### 5. `output/narrative.py` — ① 自然語言評語(含反事實)

```python
"""
自然語言評語
============
最後產出,呼應雷達圖/弱點/重點/壓力曲線,語氣一致不矛盾。
含反事實回饋(「如果當時…」),取用 DUAT analysis 的細節。
"""

from llm.router import call_llm


async def build_narrative(session, duat_result, radar, weakness,
                          keyfocus, stress):
    # 共用所有輸出,確保評語與數字一致
    resp = await call_llm(
        "duat",
        prompt=(
            f"請寫一段給學員的整體評語(像臨床老師的口吻):\n"
            f"四維度分數:{radar['dimensions']}\n"
            f"最該注意:{keyfocus['focus']}\n"
            f"弱點:{weakness['items']}\n"
            f"壓力峰值:{stress.get('peak')}\n"
            f"DUAT 綜整:{duat_result['synthesis'].payload.get('synthesis')}\n"
            f"DUAT 記憶:{duat_result['memory'].payload.get('memory')}\n\n"
            f"要求:1)語氣鼓勵但誠實 2)務必呼應上述數字,不可矛盾 "
            f"3)結尾加一段反事實回饋,具體說明『如果當時做了什麼,"
            f"結果會如何不同』(取材自弱點與診斷推理)。回傳純文字。"),
        session=session)
    return {"type": "narrative", "text": resp.text}
```

---

## 設計重點

- **共用真相來源**:五輸出都從同一份 DUAT 結果 + StageScore 讀,
  雷達圖、弱點、評語的數字必然一致,不會各說各話。
- **協調者管依賴**:keyfocus 從 weakness 挑、narrative 呼應全部,
  由 orchestrator 控制產出順序,杜絕矛盾。
- **反事實回饋在 narrative**:用 DUAT analysis 的弱點與原因,
  在評語結尾自然帶出「如果當時問了過敏史…」,不另立模組。
- **壓力曲線標峰值**:stress 標示壓力峰值對應時刻,
  即考試模式「壓力軌跡報告」的核心。
- **radar/stress/weakness 可並行**:三者互相獨立,orchestrator 可同時算。

---

## 個人化報告:Cornell 康乃爾筆記格式

> 五種輸出是「素材」,個人化報告把它們組裝成一份**單次結構化複盤**,
> 採康乃爾筆記三欄結構,引導學員主動回想與反思,而非被動看分數。

### 三欄對應

```
┌──────────┬─────────────────────────────┐
│ 線索欄    │ 筆記欄                       │
│ (Cue)    │ (Notes)                      │
│ 問診      │ 雷達分數 + DUAT 評估細節      │
│ 身評      │ 操作軌跡 + 位置/手法/順序      │
│ 診斷      │ 三診斷排序 + 推理分析          │
│ 壓力      │ HRV 壓力曲線 + 峰值對應步驟    │
├──────────┴─────────────────────────────┤
│ 總結欄 (Summary)                         │
│ narrative 評語 + 反事實 + 連結到 Zettel 卡片 │
└─────────────────────────────────────────┘
```

### `output/report.py` — Cornell 報告組裝

```python
"""
個人化報告(康乃爾筆記格式)
============================
把五種輸出組裝成 Cornell 三欄:線索欄 / 筆記欄 / 總結欄。
總結欄連結到 rag-note 的 Zettelkasten 卡片,單次複盤導向長期累積。
"""

def build_cornell_report(outputs, zettel_cards):
    """
    outputs: build_all_outputs 的五種輸出。
    zettel_cards: rag-note 產出的卡片(供總結欄連結)。
    """
    radar = outputs["radar"]["dimensions"]
    stress = outputs["stress"]

    # 線索欄 + 筆記欄(逐維度)
    rows = [
        {"cue": "問診", "notes": f"分數 {radar['問診']};"
         f"{outputs['weakness']['duat_analysis'][:80]}"},
        {"cue": "身評", "notes": f"分數 {radar['身評']};操作軌跡見附錄"},
        {"cue": "診斷", "notes": f"分數 {radar['診斷']};三診斷排序與推理"},
        {"cue": "壓力", "notes": f"壓力峰值 {stress.get('peak')}"},
    ]

    # 總結欄:評語 + 連結卡片
    card_links = [f"[[{c['topic']}]]" for c in zettel_cards.get("cards", [])]
    summary = {
        "narrative": outputs["narrative"]["text"],
        "key_focus": outputs["keyfocus"]["focus"],
        "linked_cards": card_links,        # 連到 Zettelkasten 永久卡
    }

    return {"type": "cornell_report", "rows": rows, "summary": summary}
```

### Cornell 報告的 Obsidian 呈現(可選)

純文字環境用表格模擬三欄;Obsidian 可用 callout + 表格:

```markdown
> [!abstract] 個人化複盤報告 — 2026-05-29 胸痛案例

| 線索 | 筆記 |
|------|------|
| 問診 | 75 分;遺漏誘發因子追問 |
| 身評 | 70 分;左下肺位置偏移 |
| 診斷 | 85 分;第一診斷正確抓最危急 |
| 壓力 | 峰值於第 4 分鐘問診階段 |

> [!summary] 總結
> （narrative 評語 + 反事實回饋）
> 延伸學習:[[誘發因子問診]] [[動態評估思維]]
```

### 設計重點(Cornell 報告)

- **Cornell 管單次、Zettel 管長期**:報告是這一次的結構化複盤,
  總結欄連到永久卡,把單次回顧導向長期知識累積。兩種筆記法各司其職。
- **促進主動回想**:線索欄(問診/身評/診斷/壓力)可遮住筆記欄,
  讓學員看線索先自己回想表現,呼應系統「引導複盤而非被動看分」的精神。
- **總結欄是樞紐**:narrative 評語 + keyfocus 重點 + 連結卡片,
  三者匯於一處,串起 output 與 rag-note 兩個模組。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:五輸出 + orchestrator,共用真相來源,反事實入 narrative | 三大決策定稿 |

---

## 驗證方式

1. 五輸出的分數皆源自同一 DUAT 結果,確認雷達圖與評語數字一致。
2. keyfocus 的 focus 等於 weakness 第一項。
3. narrative 評語呼應雷達分數,且結尾含反事實回饋。
4. stress 曲線正確標示壓力峰值。
5. 無弱點時,keyfocus 給正向訊息,narrative 不杜撰問題。
```
