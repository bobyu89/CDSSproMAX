# Sub-Agent: knowledge-base — 知識庫建立與維護

> **權重:基礎設施層(rag-note 的內容來源)。**
> 主來源 StatPearls 結構化文獻 + 自建教材。按疾病分類。可溯源。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | knowledge-base |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | ChromaDB |
| 被依賴模組 | rag-note(檢索)、case-generator(可選參照) |
| 主來源 | StatPearls 結構化文獻(已有)+ 自建教材 |

> GitHub 路徑:`ticdss/kb/`。Notion:「TICDSS / knowledge-base / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 文獻來源 | StatPearls 結構化資料(已有,不另找新來源)+ 定期官網更新 |
| 分類方式 | 按疾病分類(對應 StatPearls 結構,也對應案例主題) |
| 來源把關 | StatPearls 本身已同儕審查=把關;檢索結果標明來源即可,不過度設限 |

---

## 為什麼用 StatPearls 當主來源

StatPearls 是同儕審查的臨床參考,本身按疾病組織、結構化、權威可信:
- 穩定權威,免去動態抓論文的品質參差與可信度判斷
- 按疾病完整組織 → 正好對應「按疾病分類」與案例主題
- 已同儕審查 → 把關內建,不需額外設「只收有 DOI」這類規則

> 明確不另找新來源(依使用者指示);僅定期同步 StatPearls 更新。

---

## 知識庫結構

```
ChromaDB 兩個 collection(rag-note 已約定):
├── open_literature   StatPearls 條目,metadata 標 disease + source=StatPearls
└── custom_materials  自建教材,metadata 標 disease + source=自建

兩者皆按疾病(disease)分類標籤,檢索時可依疾病過濾,提升精準度。
```

---

## 產出檔案

### 1. `kb/ingest_statpearls.py` — StatPearls 匯入

```python
"""
StatPearls 結構化文獻匯入
=========================
把已有的 StatPearls 結構化資料切塊、嵌入、存入 ChromaDB。
按疾病分類標籤。
"""

def ingest_statpearls(chroma, statpearls_data):
    """
    statpearls_data: 已有的結構化資料(條目列表)。
    每條目含:disease、section(如病因/症狀/診斷/治療)、text、ref。
    """
    coll = chroma.get_or_create_collection("open_literature")
    for entry in statpearls_data:
        # 依章節切塊,每塊一個可檢索單位
        chunks = _chunk_by_section(entry)
        for i, chunk in enumerate(chunks):
            coll.add(
                ids=[f"sp_{entry['disease']}_{entry['section']}_{i}"],
                documents=[chunk["text"]],
                metadatas=[{
                    "disease": entry["disease"],      # 疾病分類
                    "section": chunk["section"],      # 章節
                    "source": "StatPearls",           # 來源標記
                    "ref": entry.get("ref", ""),      # 可溯源
                }])


def _chunk_by_section(entry):
    """依 StatPearls 章節結構切塊(病因/流病/症狀/診斷/治療...)。"""
    # StatPearls 本身結構化,直接依 section 切
    return entry.get("sections", [])
```

### 2. `kb/ingest_custom.py` — 自建教材匯入

```python
"""
自建教材匯入
============
把個人講義、臨床筆記存入 custom_materials,標 disease 與 source=自建。
"""

def ingest_custom_material(chroma, material):
    """material: {disease, title, text, note_id}。"""
    coll = chroma.get_or_create_collection("custom_materials")
    chunks = _chunk_text(material["text"])
    for i, chunk in enumerate(chunks):
        coll.add(
            ids=[f"custom_{material['note_id']}_{i}"],
            documents=[chunk],
            metadatas=[{
                "disease": material["disease"],
                "source": "自建",
                "note_id": material["note_id"],
                "title": material["title"],
            }])


def _chunk_text(text, size=500):
    """自建教材無固定結構,依長度切塊。"""
    return [text[i:i+size] for i in range(0, len(text), size)]
```

### 3. `kb/updater.py` — 定期更新

```python
"""
定期更新 StatPearls
===================
定期上 StatPearls 官網檢查更新,同步變動條目。不抓新來源。
"""

async def sync_statpearls(chroma, last_sync_date):
    """
    定期排程(如每月)呼叫。檢查 StatPearls 更新,重新匯入變動條目。
    只更新既有來源,不引入新來源(依設計決策)。
    """
    updated = _fetch_statpearls_updates(last_sync_date)  # 官網更新
    if updated:
        ingest_statpearls(chroma, updated)               # 重新匯入
    return {"synced": len(updated), "date": last_sync_date}


def _fetch_statpearls_updates(since):
    """上 StatPearls 官網取得 since 之後更新的條目。"""
    raise NotImplementedError("串接 StatPearls 更新來源時實作")
```

### 4. `kb/retrieval.py` — 檢索(供 rag-note)

```python
"""
知識庫檢索
==========
rag-note 用。可依疾病過濾,提升精準度。檢索結果標明來源。
"""

def retrieve(chroma, query, disease=None, k=4):
    """
    依弱點查詢檢索。disease 提供時過濾該疾病,提升精準。
    回傳含來源標記的結果(可溯源)。
    """
    hits = []
    for coll_name in ["open_literature", "custom_materials"]:
        coll = chroma.get_collection(coll_name)
        where = {"disease": disease} if disease else None
        res = coll.query(query_texts=[query], n_results=k, where=where)
        for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
            hits.append({
                "text": doc,
                "disease": meta.get("disease"),
                "source": meta.get("source"),     # StatPearls / 自建
                "ref": meta.get("ref") or meta.get("note_id"),
            })
    return hits
```

---

## 設計重點

- **StatPearls 為主、權威穩定**:用已有的結構化資料,不動態抓新論文,
  品質穩定。把關由 StatPearls 同儕審查內建,不另設來源限制。
- **按疾病分類提升精準**:每塊標 disease,rag-note 檢索時可依疾病過濾,
  避免跨疾病的雜訊。對應案例主題(胸痛、腹痛...)。
- **依結構切塊**:StatPearls 本身有章節結構(病因/症狀/診斷/治療),
  依此切塊,每塊語義完整;自建教材無結構則依長度切。
- **定期更新不擴源**:updater 只同步 StatPearls 更新,不引新來源,
  符合「不找新的」指示。
- **可溯源**:每塊標 source(StatPearls/自建)與 ref,rag-note 卡片
  附出處時直接取用,學員知道是權威文獻還是個人教材。
- **冷啟動友善**:StatPearls 已有資料,匯入即可用,知識庫不從零空白開始。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:StatPearls 主來源 + 按疾病分類 + 定期更新 + 檢索 | 善用既有結構化資料,穩定權威,對應案例主題 |

---

## 驗證方式

1. 匯入 StatPearls 資料,確認 open_literature 每塊標 disease + source=StatPearls。
2. 匯入自建教材,確認 custom_materials 標 source=自建。
3. retrieve 指定 disease="胸痛",確認只回該疾病相關塊。
4. 檢索結果確認含來源標記與 ref,可供 rag-note 溯源。
5. sync_statpearls 確認只更新既有條目,不新增其他來源。
```
