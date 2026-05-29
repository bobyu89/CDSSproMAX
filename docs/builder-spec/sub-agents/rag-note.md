# Sub-Agent: rag-note — 個人化學習講義(Zettelkasten 雙卡)

> **權重:標準(個人化閉環收尾)。**
> 依弱點生成卡片盒筆記:永久卡(知識網絡)+ 訓練卡(失誤日誌)。Obsidian 格式。
> 系統「評分→弱點→檢索→卡片」閉環終點。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | rag-note |
| 模組版本 | v2.0(Zettelkasten 雙卡版,取代 v1 文章版) |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、llm-adapter、output-weakness、duat-memory、ChromaDB |
| 被依賴模組 | Obsidian vault、個人學習歷程 |

> GitHub 路徑:`ticdss/rag/note.py`。Notion:「TICDSS / rag-note / v2.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 知識庫 | 混合:開放醫學文獻 + 自建教材 |
| 卡片顆粒度 | 雙卡:永久卡(知識點,累積)+ 訓練卡(單次失誤,新增) |
| 輸出格式 | Obsidian(雙向連結 `[[...]]` + callout) |

---

## 為什麼用 Zettelkasten 雙卡

學員的弱點會重複出現、會累積。文章式講義每次都生新文章,知識散又重複。
卡片盒讓知識長成網絡:

```
永久卡(知識點,會累積、會被重複連結)
└── 「誘發因子問診 LQQOPERA-P」這個知識本身
    一張,永久存在,每次相關弱點都連回它

訓練卡(這次的失誤紀錄,每次訓練新增)
└── 「2026-05-29 胸痛案例 - 漏問誘發因子」
    記錄這次發生什麼,連結 → 永久卡
```

重複弱點 → 訓練卡是新的,但都連回同一張永久卡 → 累積自然發生。
這與 M-Agent 歷程整合:M 知道「第幾次」,訓練卡記錄每一次。

---

## 卡片格式

### 永久卡(Obsidian)

```markdown
---
type: permanent
topic: 誘發因子問診
tags: [LQQOPERA, 問診, clinical-reasoning]
created: 2026-05-29
hit_count: 3
---

> [!note] 核心概念
> 誘發因子(Precipitating)是 LQQOPERA 的 P 維度,
> 用於釐清症狀在什麼情況下加重或誘發。

## 為什麼重要
（知識點本身的說明,不綁定特定一次訓練）

## 延伸
- [[動態評估思維]]
- [[LQQOPERA 完整框架]]

## 文獻出處
- Smith et al. (2023). *PMID: 12345678*
- 自建教材:問診技巧講義 §3.2

## 訓練紀錄(自動累積)
- [[2026-05-29 胸痛案例 - 漏問誘發因子]]
- [[2026-05-15 腹痛案例 - 漏問誘發因子]]
```

### 訓練卡(Obsidian)

```markdown
---
type: training
date: 2026-05-29
scenario: 胸痛案例
weak_point: 漏問誘發因子
---

> [!warning] 這次的失誤
> 問診時未追問「什麼情況會讓胸痛加重」,
> 導致無法區分心因性與肌肉骨骼性胸痛。

## 當時情境
（DUAT analysis 提供的具體失誤描述）

## 連結知識
- [[誘發因子問診]]   ← 連回永久卡

## M-Agent 歷程提示
> 這是你第 3 次在「誘發因子」失誤,建議專門練習。
```

---

## 產出檔案

### `rag/note.py`

```python
"""
個人化學習講義(Zettelkasten 雙卡)
==================================
弱點 → 檢索 → 永久卡(知識,累積)+ 訓練卡(失誤,新增)。
Obsidian 格式,與 M-Agent 歷程整合實現累積。
"""

from llm.router import call_llm
import datetime


def _retrieve(chroma, query, k=4):
    """從開放文獻 + 自建教材檢索,保留出處。"""
    hits = []
    for coll in ["open_literature", "custom_materials"]:
        res = chroma.get_collection(coll).query(
            query_texts=[query], n_results=k)
        for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
            hits.append({
                "text": doc,
                "source": meta.get("source", "未標示"),
                "ref": meta.get("doi") or meta.get("pmid") or meta.get("note_id"),
                "type": "文獻" if coll == "open_literature" else "教材"})
    return hits


def _topic_of(weak_point, chroma):
    """把弱點對應到永久卡主題(查是否已有同主題卡)。"""
    # 實際以向量相似度比對既有永久卡;此處示意
    # existing = chroma.get_collection("permanent_cards").query(...)
    return weak_point.split(":")[-1].strip()


async def generate_cards(session, weakness, duat_result, chroma,
                         student_id=None):
    """
    主入口:依弱點生成/更新雙卡。
    weakness: output-weakness 輸出;duat_result: 取 analysis 與 memory。
    回傳要寫入 Obsidian 的卡片清單。
    """
    weak_items = weakness["items"]
    if not weak_items:
        return {"type": "zettel_cards", "cards": [],
                "message": "本次無明顯弱點。"}

    today = datetime.date.today().isoformat()
    scenario = session.scenario_id
    analysis = duat_result["analysis"].payload.get("analysis", "")
    memory = duat_result["memory"].payload.get("memory", "")

    cards = []
    for wp in weak_items:
        topic = _topic_of(wp, chroma)
        contexts = _retrieve(chroma, wp)

        # 1. 永久卡:LLM 生成/更新知識點內容
        perm = await call_llm(
            "diagnosis",
            prompt=(f"知識主題:{topic}\n參考資料:{[c['text'] for c in contexts]}\n"
                    f"請寫一張 Zettelkasten 永久卡的核心概念與重要性"
                    f"(知識本身,不綁定特定訓練)。回傳JSON:"
                    f'{{"core":"...","why":"...","links":["相關主題"]}}'),
            session=session)
        perm_data = _parse(perm.text)

        sources = [{"source": c["source"], "ref": c["ref"], "type": c["type"]}
                   for c in contexts]

        # 2. 訓練卡:記錄這次失誤(取 DUAT analysis 的具體描述)
        train = await call_llm(
            "diagnosis",
            prompt=(f"弱點:{wp}\n本次分析:{analysis}\nM-Agent歷程:{memory}\n"
                    f"請寫一張訓練卡:這次失誤的具體描述 + 當時情境。"
                    f"回傳JSON:{{\"failure\":\"...\",\"context\":\"...\"}}"),
            session=session)
        train_data = _parse(train.text)

        cards.append({
            "permanent": _render_permanent(topic, perm_data, sources, today),
            "training": _render_training(topic, wp, scenario, train_data,
                                         memory, today),
            "topic": topic,
        })

    return {"type": "zettel_cards", "cards": cards}


def _render_permanent(topic, data, sources, today):
    """產出永久卡 Obsidian markdown。"""
    links = "\n".join(f"- [[{l}]]" for l in data.get("links", []))
    refs = "\n".join(f"- {s['source']} *{s['ref'] or ''}* ({s['type']})"
                     for s in sources)
    return f"""---
type: permanent
topic: {topic}
created: {today}
---

> [!note] 核心概念
> {data.get('core', '')}

## 為什麼重要
{data.get('why', '')}

## 延伸
{links}

## 文獻出處
{refs}

## 訓練紀錄(自動累積)
- [[{today} {topic} 失誤紀錄]]
"""


def _render_training(topic, wp, scenario, data, memory, today):
    """產出訓練卡 Obsidian markdown。"""
    return f"""---
type: training
date: {today}
scenario: {scenario}
weak_point: {wp}
---

> [!warning] 這次的失誤
> {data.get('failure', '')}

## 當時情境
{data.get('context', '')}

## 連結知識
- [[{topic}]]

## M-Agent 歷程提示
> {memory}
"""


def _parse(txt):
    import json
    try:
        return json.loads(txt)
    except Exception:
        return {}
```

---

## 設計重點

- **雙卡分離知識與經驗**:永久卡是知識點(累積、被連結),訓練卡是單次失誤
  (新增、連回永久卡)。符合 Zettelkasten「一卡一事」原子原則。
- **累積靠連結**:重複弱點 → 新訓練卡都連回同一張永久卡,永久卡的「訓練紀錄」
  區自動長出多筆連結 → 學員看到自己在某知識點犯錯幾次。
- **與 M-Agent 整合**:M-Agent 提供「第幾次、進步否」的歷程敘事,
  寫入訓練卡;永久卡的 hit_count 對應犯錯次數。
- **Obsidian 原生**:雙向連結 `[[...]]` + callout(`[!note]`/`[!warning]`),
  丟進 vault 直接看知識圖譜。配合既有 obsidian-markdown skill。
- **可溯源**:永久卡文獻出處區附 DOI/PMID 或教材來源。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:混合知識庫 + 分層文章講義 | 閉環收尾 |
| 2026-05-29 | v2.0 | 改 Zettelkasten 雙卡(永久卡+訓練卡),Obsidian 格式 | 知識累積成網絡,與 M-Agent 歷程整合 |

---

## 驗證方式

1. 餵入含 2 弱點的 weakness,確認產出 2 組雙卡。
2. 確認永久卡含核心概念、延伸連結、文獻出處、訓練紀錄區。
3. 確認訓練卡 callout 標失誤,並 `[[連回]]` 永久卡。
4. 模擬同弱點第二次,確認訓練卡連回同一永久卡(主題相同)。
5. 確認 M-Agent 歷程敘事寫入訓練卡。
6. 確認輸出為合法 Obsidian markdown(callout + 雙向連結)。
```
