# Sub-Agent: fusion-classifier — 三訊號融合分類器

> **權重:標準偏高(整合三個訊號採集器,系統的學習狀態判斷核心)。**
> 多模態情感運算(Multimodal Affective Computing)的實作核心。
> HRV × 停頓 × 表情 → 學習狀態 → 即時難度調整。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | fusion-classifier |
| 模組版本 | v1.1 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session)、signal-hrv、signal-pause、signal-expression |
| 被依賴模組 | 訓練迴圈(即時調難度)、output-stress(壓力曲線) |

> GitHub 路徑:`ticdss/fusion/classifier.py`。Notion:「TICDSS / fusion-classifier / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 介入門檻 | 加權投票:兩個以上訊號一致即介入(靈敏) |
| 訊號加權 | HRV 權重最高(生理訊號最難偽裝);停頓、表情次之 |
| 介入時機 | 狀態須持續一段時間(防抖)才調難度,避免頻繁變動 |

## 壓力監測開關與缺訊號處理

> 壓力監測是**可選功能**,使用者可開關。HRV 不可替代——
> 沒有 HRV 就不做壓力判斷,而非用停頓+表情頂替(會降低可信度)。

```
壓力監測模式(使用者可開關):
├── 開 + 有 HRV → fusion 正常,即時調難度 + 壓力曲線
├── 開 + 沒 HRV → 回報「無法生成壓力監測」,不頂替
└── 沒開        → 不做壓力監測,訓練照常
```

> 理由:HRV 是壓力判斷核心(最難偽裝)。沒可靠訊號就不 output 不可靠結論,
> 與系統「HRV 為代理指標、用語嚴謹」的精神一致。停頓/表情仍會採集記錄,
> 但不單獨用於壓力判斷。

---

## 三決策如何互相搭配

- **兩個以上一致就介入** → 靈敏,不漏狀態
- **HRV 權重最高** → 靈敏的同時,讓最可信的生理訊號說話最大聲
- **持續才調** → 防抖,避免靈敏過頭變頻繁亂調

合起來 = 靈敏但不毛躁:容易偵測狀態,但要持續且 HRV 同意才真的調難度。

---

## 訊號 → 狀態的對應

| 學習狀態 | HRV | 停頓 | 表情 |
|---------|-----|------|------|
| anxious(焦慮) | drop | long | frown |
| flow(心流) | stable | fluent | focused |
| low_engagement(低投入) | flat | fluent | relaxed |

---

## 加權投票機制

每個狀態收集三訊號的「票」,訊號加權後得分最高者勝;
但需達門檻(兩票以上等效)才算有效狀態,否則為 ambiguous(不介入)。

```
權重:HRV 0.5、停頓 0.25、表情 0.25
```

HRV 0.5 代表:HRV 一個訊號就抵停頓+表情兩個。生理訊號最難偽裝,最可信。

---

## 產出檔案

### `fusion/classifier.py`

```python
"""
三訊號融合分類器
================
HRV × 停頓 × 表情 → 學習狀態 → 即時難度調整。
加權投票(HRV 最重)+ 持續性防抖。
"""

import time
from signals.expression import dominant_expression

# 訊號權重:HRV 最難偽裝,權重最高
WEIGHTS = {"hrv": 0.5, "pause": 0.25, "expression": 0.25}

# 各狀態對應的訊號標籤
STATE_SIGNATURE = {
    "anxious":        {"hrv": "drop",   "pause": "long",   "expression": "frown"},
    "flow":           {"hrv": "stable", "pause": "fluent", "expression": "focused"},
    "low_engagement": {"hrv": "flat",   "pause": "fluent", "expression": "relaxed"},
}

VOTE_THRESHOLD = 0.5        # 加權得分需達此值才算有效狀態
STABLE_DURATION = 20.0      # 狀態須持續幾秒才調難度(防抖)


def _latest(session, sig_type, window=10.0, now=None):
    """取近 window 秒內某訊號的最新標籤。"""
    if now is None:
        now = time.time()
    items = [s for s in session.signals
             if s["type"] == sig_type and now - s["timestamp"] <= window]
    return items[-1]["label"] if items else None


def classify_state(session, now=None) -> str:
    """
    加權投票得出當前學習狀態。
    回傳 anxious / flow / low_engagement / ambiguous。
    """
    hrv = _latest(session, "hrv", now=now)
    pause = _latest(session, "pause", now=now)
    expr = dominant_expression(session, now=now)

    observed = {"hrv": hrv, "pause": pause, "expression": expr}

    # 對每個候選狀態算加權得分
    scores = {}
    for state, sig in STATE_SIGNATURE.items():
        score = sum(WEIGHTS[k] for k in sig
                    if observed.get(k) == sig[k])
        scores[state] = score

    best = max(scores, key=scores.get)
    # 達門檻才算有效;否則訊號太分散 → ambiguous
    return best if scores[best] >= VOTE_THRESHOLD else "ambiguous"


def update_and_decide(session, mode: str, now=None) -> dict:
    """
    主入口:分類狀態 + 持續性防抖 + 介入決策。
    每隔一小段時間由訓練迴圈呼叫一次。
    """
    if now is None:
        now = time.time()

    # ── 壓力監測開關與 HRV 必要檢查 ──
    if not session.scratch.get("stress_monitoring_enabled", False):
        return {"state": "disabled",
                "message": "壓力監測未開啟"}      # 使用者沒開,不做

    if _latest(session, "hrv", now=now) is None:
        return {"state": "unavailable",
                "message": "無 HRV 訊號,無法生成壓力監測"}  # 沒 HRV,不頂替

    state = classify_state(session, now=now)

    # ── 持續性追蹤(防抖) ──
    fs = session.scratch.setdefault("fusion", {
        "candidate": None, "since": now, "active": None})

    if state != fs["candidate"]:
        # 狀態變了,重新計時
        fs["candidate"] = state
        fs["since"] = now
        held = 0.0
    else:
        held = now - fs["since"]

    # 記錄狀態時序(供 output-stress 壓力曲線)
    session.signals.append({
        "type": "fusion_state", "timestamp": now,
        "state": state, "held": round(held, 1)})

    # ── 介入決策 ──
    # 須持續 STABLE_DURATION 秒,且非 ambiguous,才調難度
    intervention = "none"
    if state != "ambiguous" and held >= STABLE_DURATION \
       and fs["active"] != state:
        intervention = _intervention(state, mode)
        fs["active"] = state        # 標記已對此狀態介入,避免重複

    return {"state": state, "held": round(held, 1),
            "intervention": intervention}


def _intervention(state: str, mode: str) -> str:
    """狀態 → 介入動作。考試模式僅記錄不介入。"""
    if mode == "exam":
        return "record_only"
    return {
        "anxious":        "lower_difficulty",   # 焦慮 → 降難度/給提示
        "flow":           "maintain",           # 心流 → 維持
        "low_engagement": "raise_difficulty",   # 低投入 → 升難度/加情境
    }.get(state, "none")
```

---

## 設計重點

- **加權投票實現「兩個一致 + HRV 最重」**:HRV 權重 0.5,單獨命中即達門檻;
  停頓+表情兩個一致(0.25+0.25=0.5)也達門檻。所以「HRV 命中」或
  「另兩個一致」都會觸發,符合你要的靈敏度,同時 HRV 說話最大聲。
- **持續性防抖**:狀態須穩定 STABLE_DURATION 秒才調難度,避免訊號瞬間
  波動造成頻繁亂調。`fs["active"]` 避免同一狀態重複介入。
- **ambiguous 不介入**:訊號分散、得分未達門檻時不動作,避免誤判
  (延續單一訊號易誤判的防範)。
- **考試模式只記錄**:exam 模式 record_only,狀態時序仍記錄,供事後
  壓力曲線,但不介入流程,確保考試公平。
- **狀態時序餵給 output-stress**:每次分類寫入 fusion_state,
  成為 HRV 壓力曲線/壓力軌跡報告的資料來源。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:加權投票(HRV 0.5)+ 持續性防抖 + 即時介入 | 三大決策定稿,靈敏但不毛躁 |
| 2026-05-29 | v1.1 | 加壓力監測開關 + HRV 必要檢查(沒 HRV 不頂替) | 壓力監測為可選功能;HRV 不可替代,缺則誠實回報 |

---

## 驗證方式

1. 只有 HRV=drop(停頓/表情不符),確認得分 0.5 達門檻 → anxious。
2. HRV 不符但 pause=long+expression=frown,確認 0.5 達門檻 → anxious。
3. 三訊號全分散,確認 ambiguous、不介入。
4. anxious 持續 10 秒(未達 20 秒),確認尚不介入;持續 20 秒後才 lower_difficulty。
5. 考試模式下任何狀態,確認 intervention 為 record_only。
6. 確認每次分類寫入 fusion_state,供壓力曲線取用。
```
