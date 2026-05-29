# Sub-Agent: signal-expression — 臉部表情訊號採集器

> **權重:標準(訊號採集器,被 fusion-classifier 取用)。**
> 把臉部表情轉成標準訊號標籤。本地 FER 連續追蹤 + 需要時 Gemini 補強。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | signal-expression |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session)、llm-adapter(Gemini 補強) |
| 被依賴模組 | fusion-classifier |
| 資料來源 | 攝影機畫面 |

> GitHub 路徑:`ticdss/signals/expression.py`。Notion:「TICDSS / signal-expression / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 辨識方式 | 分層:本地 FER 模型即時連續追蹤;低信心時抽幀送 Gemini 補強 |
| 表情類別 | 四類:frown / focused / relaxed / neutral |
| 追蹤方式 | 連續追蹤(與身評一致,即時) |

---

## 表情類別設計

對應 fusion 的三種學習狀態,加一個中性避免污染:

| 標籤 | 意義 | 對應 fusion 訊號 |
|------|------|------------------|
| `frown` | 皺眉、緊繃 | 焦慮 |
| `focused` | 專注 | 心流 |
| `relaxed` | 放鬆、鬆懈 | 低投入 |
| `neutral` | 中性、無明顯表情 | 不干擾(大多數時間) |

> neutral 很關鍵:多數時間人臉平靜,有中性類別才不會硬把平靜臉判成情緒,
> 避免污染 fusion-classifier 的判斷。

---

## 分層辨識策略

```
本地 FER 模型(即時、免費、連續)
   │  輸出表情 + 信心分數
   ├── 信心高 → 直接採用
   └── 信心低 → 抽該幀送 Gemini 判讀(情境理解,少量)
```

與 vision 的分層邏輯一致:本地優先,不確定才動用雲端,控制成本。

---

## 產出檔案

### `signals/expression.py`

```python
"""
臉部表情訊號採集器
==================
本地 FER 連續追蹤,低信心時抽幀送 Gemini 補強。
四類表情:frown / focused / relaxed / neutral。
只採集標籤,不判斷學習狀態(交給 fusion-classifier)。
"""

import time
from llm.router import call_llm

EXPRESSIONS = ["frown", "focused", "relaxed", "neutral"]
CONFIDENCE_THRESHOLD = 0.6        # 低於此信心才求助 Gemini

# 本地 FER 原始輸出 → 我們的四類標籤
# (FER 模型常輸出 angry/happy/neutral/sad/surprise 等,做映射)
FER_TO_LABEL = {
    "angry":    "frown",
    "disgust":  "frown",
    "fear":     "frown",
    "sad":      "frown",
    "happy":    "relaxed",
    "surprise": "focused",
    "neutral":  "neutral",
}


def _local_fer(frame):
    """
    本地 FER 模型推論。回傳 (原始表情, 信心)。
    實際用 fer / deepface 等開源套件;此處為介面。
    """
    # result = fer_model.predict(frame)
    # return result.label, result.confidence
    raise NotImplementedError("串接本地 FER 模型時實作")


def _map_label(raw: str) -> str:
    """把 FER 原始輸出映射到四類。"""
    return FER_TO_LABEL.get(raw, "neutral")


async def collect_and_classify(session, frame, timestamp: float = None) -> str:
    """
    主入口:採集一幀表情,分類,寫入 session.signals。
    連續呼叫(每幾幀一次),回傳四類標籤之一。
    """
    if timestamp is None:
        timestamp = time.time()

    # 第一層:本地 FER
    raw, confidence = _local_fer(frame)
    label = _map_label(raw)
    source = "local_fer"

    # 第二層:信心低 → 送 Gemini 補強
    if confidence < CONFIDENCE_THRESHOLD:
        resp = await call_llm(
            "vision",
            prompt="判斷畫面中學員的表情屬於哪一類,只回一個英文字:"
                   "frown / focused / relaxed / neutral",
            image_b64=frame, session=session)
        g = resp.text.strip().lower()
        if g in EXPRESSIONS:
            label = g
            source = "gemini"

    session.signals.append({
        "type": "expression",
        "phase": session.phase.value,
        "timestamp": timestamp,
        "label": label,
        "confidence": round(confidence, 2),
        "source": source,
    })
    return label


def dominant_expression(session, window: float = 10.0,
                        now: float = None) -> str:
    """
    取近 window 秒內的主要表情(供 fusion 取用)。
    連續追蹤會產生很多幀,fusion 需要的是「最近這段時間的主導表情」,
    而非單一幀,以降低雜訊。
    """
    if now is None:
        now = time.time()
    recent = [s["label"] for s in session.signals
              if s["type"] == "expression"
              and now - s["timestamp"] <= window]
    if not recent:
        return "neutral"
    # 排除 neutral 後取最多者;全是 neutral 才回 neutral
    non_neutral = [r for r in recent if r != "neutral"]
    pool = non_neutral or recent
    return max(set(pool), key=pool.count)
```

---

## 設計重點

- **分層控成本**:本地 FER 連續即時跑(免費),只有信心低於 0.6 才抽幀送
  Gemini。與 vision 邏輯一致。
- **四類含 neutral**:多數時間人臉平靜,neutral 避免硬判情緒污染 fusion。
- **dominant_expression 降雜訊**:連續追蹤產生大量幀,fusion 不看單幀,
  而是取近 10 秒的主導表情,單幀誤判不影響整體。
- **只採集不判斷**:輸出表情標籤,「皺眉代表焦慮還是專心想」交給
  fusion-classifier 配合 HRV、停頓交叉驗證。表情本來就最易誤判,
  正好靠三訊號互相佐證。
- **FER 映射可調**:FER_TO_LABEL 把開源模型的原始輸出映射到四類,
  未來換更好的模型只改映射表。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:本地 FER 連續追蹤 + Gemini 補強 + 四類表情 | 三大決策定稿,分層控成本,neutral 防污染 |

---

## 驗證方式

1. 本地 FER 高信心輸出 angry,確認映射為 frown 且不呼叫 Gemini。
2. 本地 FER 信心低於 0.6,確認觸發 Gemini 補強。
3. 連續餵入多幀,確認 dominant_expression 回傳近 10 秒主導表情。
4. 餵入大量 neutral 夾雜少數 frown,確認 dominant 排除 neutral 取 frown。
5. 確認每幀都寫入 session.signals,含 label、confidence、source。
```
