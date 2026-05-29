# Sub-Agent: signal-pause — 語音停頓訊號採集器

> **權重:標準(訊號採集器,被 fusion-classifier 取用)。**
> 把語音停頓轉成標準訊號標籤(fluent/long)。把問診已有的停頓邏輯正式化。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | signal-pause |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session) |
| 被依賴模組 | fusion-classifier |
| 資料來源 | Deepgram STT 的靜音偵測 |

> GitHub 路徑:`ticdss/signals/pause.py`。Notion:「TICDSS / signal-pause / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 判斷方式 | 混合:固定閾值為安全網,累積足夠資料後改用相對個人基準 |
| 訊號細度 | 停頓長度 + 頻率(多久停一次) |
| 與問診整合 | 把 inquiry 已有的停頓偵測邏輯抽出,正式化為獨立採集器 |

---

## 為什麼用混合判斷

- 純固定閾值:講話慢的人被誤判卡住,講話快的人卡了卻沒被抓到。
- 純相對個人:第一版沒累積資料時無基準可比。
- **混合(本版)**:預設用固定閾值(安全網),學員本次累積足夠停頓樣本後,
  改用相對個人基準。與 signal-hrv 的相對基準邏輯一致,系統行為統一。

---

## 訊號標籤定義

| 標籤 | 意義 | 判斷 |
|------|------|------|
| `fluent` | 流暢、思路順 | 停頓短、頻率低 |
| `long` | 卡住、猶豫 | 停頓長 或 頻繁停頓 |

---

## 產出檔案

### `signals/pause.py`

```python
"""
語音停頓訊號採集器
==================
把 Deepgram 的靜音偵測轉成 fluent/long 標籤。
混合判斷:固定閾值為安全網,累積足夠資料後用相對個人基準。
只採集標籤,不判斷學習狀態(交給 fusion-classifier)。
"""

import statistics

# 固定閾值(安全網,無個人基準時用)
DEFAULT_LONG_THRESHOLD = 5.0      # 秒,超過視為長停頓
MIN_SAMPLES_FOR_RELATIVE = 5      # 累積幾筆後改用相對基準
FREQUENT_PAUSE_WINDOW = 60        # 秒,計算停頓頻率的視窗
FREQUENT_PAUSE_COUNT = 3          # 視窗內停頓幾次算頻繁


def _long_threshold(session) -> float:
    """
    取得當前的長停頓閾值。
    累積足夠停頓樣本 → 用個人平均 + 1.5 倍標準差;否則用固定值。
    """
    pauses = [s["duration"] for s in session.signals
              if s["type"] == "pause"]
    if len(pauses) >= MIN_SAMPLES_FOR_RELATIVE:
        mean = statistics.mean(pauses)
        sd = statistics.pstdev(pauses) or 1.0
        return mean + 1.5 * sd          # 相對個人:明顯高於自己平常
    return DEFAULT_LONG_THRESHOLD        # 安全網


def _is_frequent(session, now: float) -> bool:
    """近 FREQUENT_PAUSE_WINDOW 秒內停頓次數是否達頻繁標準。"""
    recent = [s for s in session.signals
              if s["type"] == "pause"
              and now - s["timestamp"] <= FREQUENT_PAUSE_WINDOW]
    return len(recent) >= FREQUENT_PAUSE_COUNT


def collect_and_classify(session, duration: float, timestamp: float) -> str:
    """
    主入口:採集一次停頓,分類,寫入 session.signals。
    duration: 這次停頓秒數;timestamp: 發生時間(相對訓練開始)。
    回傳 'fluent' | 'long'。
    """
    threshold = _long_threshold(session)

    # 長度判斷
    is_long_by_duration = duration > threshold
    # 頻率判斷(先記錄再算,把這次也算進去)
    is_frequent = _is_frequent(session, timestamp)

    label = "long" if (is_long_by_duration or is_frequent) else "fluent"

    session.signals.append({
        "type": "pause",
        "phase": session.phase.value,
        "timestamp": timestamp,
        "duration": duration,
        "label": label,
        "threshold_used": round(threshold, 1),
        "frequent": is_frequent,
    })
    return label
```

---

## 與問診的整合(正式化)

inquiry 模組原本在 `handle_input` 裡直接寫 `session.signals.append({...pause...})`。
正式化後,inquiry 改為呼叫本模組:

```python
# inquiry_agent.py 內,把原本的停頓邏輯換成:
from signals.pause import collect_and_classify

if silence > 0:
    collect_and_classify(session, duration=silence,
                         timestamp=time.time() - session.scratch["...t0"])
```

這樣停頓偵測邏輯集中在一處,問診、診斷或任何階段都共用同一套標準。

---

## 設計重點

- **混合判斷,行為與 HRV 一致**:固定閾值當安全網,有個人資料後轉相對基準,
  跟 signal-hrv 的相對基準思路統一,整個系統的訊號判斷邏輯一致。
- **長度 + 頻率雙條件**:單次長停頓、或短時間內頻繁停頓,都算 long。
  捕捉「一次卡很久」與「一直猶豫」兩種不同的卡住型態。
- **正式化、去重複**:把散在問診的停頓邏輯收攏成單一模組,所有階段共用,
  未來要改判斷標準只改一處。
- **只採集不判斷**:輸出 fluent/long,不解讀「這代表焦慮還是思考」,
  交給 fusion-classifier 配合 HRV、表情交叉驗證。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:混合判斷 + 長度/頻率雙條件,正式化問診停頓邏輯 | 三大決策定稿,與 HRV 基準邏輯統一 |

---

## 驗證方式

1. 無個人資料時,餵入 6 秒停頓,確認用固定閾值判 'long'。
2. 累積 5 筆以上停頓後,確認改用相對個人基準計算閾值。
3. 60 秒內餵入 3 次短停頓,確認因頻率判 'long'(即使每次都不長)。
4. 確認每次都寫入 session.signals,含 label、threshold_used、frequent。
5. 確認 inquiry 改呼叫本模組後,停頓仍正確記錄。
```
