# Sub-Agent: signal-hrv — HRV 訊號採集器

> **權重:標準(訊號採集器,被 fusion-classifier 取用)。**
> 把 HRV 原始資料轉成標準訊號標籤(drop/stable/flat)。只採集、不判斷學習狀態。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | signal-hrv |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session) |
| 被依賴模組 | fusion-classifier |
| 資料來源 | Apple Watch / Garmin（HealthKit API） |

> GitHub 路徑:`ticdss/signals/hrv.py`。Notion:「TICDSS / signal-hrv / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 資料來源 | Apple Watch / Garmin,透過 HealthKit API |
| 基準建立 | 每迴圈前 1 分鐘正念冥想,同步採集 HRV 建立個人基準值 |
| 採用指標 | RMSSD（副交感活性）+ LF/HF ratio（自律神經平衡） |

---

## 核心設計:每迴圈前重建基準

> 這與 Pre-Training Protocol(引導呼吸/正念)整合:
> 每個訓練迴圈開始前,讓學員做 1 分鐘正念冥想,同時採集 HRV,
> 算出當下的個人基準(RMSSD 與 LF/HF 的基準帶)。
> 之後訓練中的 HRV,都跟「這次的基準」比,而非絕對數值,
> 避免個體差異與當日狀態造成的偏差,也避免基準漂移。

訊號標籤定義(相對基準):

| 標籤 | 意義 | 判斷(相對基準) |
|------|------|-----------------|
| `drop` | 焦慮/壓力 | RMSSD 明顯低於基準 且 LF/HF 升高 |
| `stable` | 投入/心流 | RMSSD 與 LF/HF 維持在基準帶內 |
| `flat` | 低投入 | RMSSD 偏高但變異節律平坦 |

> 嚴謹用語:HRV 為焦慮與投入程度的**生理代理指標**,非直接偵測心流。

---

## 產出檔案

### 1. `signals/hrv.py`

```python
"""
HRV 訊號採集器
==============
採集 RMSSD 與 LF/HF,相對「每迴圈前正念冥想建立的基準」分類。
只輸出訊號標籤,不判斷學習狀態(那是 fusion-classifier 的事)。
"""

from dataclasses import dataclass


@dataclass
class HRVBaseline:
    """每迴圈前正念冥想期間建立的個人基準。"""
    rmssd: float            # 基準 RMSSD
    lf_hf: float            # 基準 LF/HF ratio


@dataclass
class HRVReading:
    """單次 HRV 量測。"""
    rmssd: float
    lf_hf: float
    timestamp: float


def build_baseline(readings: list[HRVReading]) -> HRVBaseline:
    """
    用 1 分鐘正念冥想期間的多次量測,算出基準。
    取中位數較不受極端值影響。
    """
    import statistics
    return HRVBaseline(
        rmssd=statistics.median(r.rmssd for r in readings),
        lf_hf=statistics.median(r.lf_hf for r in readings))


def classify_hrv(reading: HRVReading, baseline: HRVBaseline) -> str:
    """
    相對基準分類訊號。回傳 'drop' | 'stable' | 'flat'。
    閾值為相對比例,可依實測校正。
    """
    rmssd_ratio = reading.rmssd / baseline.rmssd
    lf_hf_ratio = reading.lf_hf / baseline.lf_hf

    # 焦慮:RMSSD 明顯下降 + LF/HF 上升(交感主導)
    if rmssd_ratio < 0.75 and lf_hf_ratio > 1.3:
        return "drop"
    # 低投入:RMSSD 偏高但缺乏變化(過度放鬆、節律平坦)
    if rmssd_ratio > 1.25:
        return "flat"
    # 其餘視為穩定(投入/心流帶)
    return "stable"


async def collect_and_classify(session, reading: HRVReading) -> str:
    """
    主入口:採集一筆 HRV,分類,並寫入 session.signals。
    """
    baseline = session.scratch.get("hrv_baseline")
    if baseline is None:
        return "stable"     # 尚未建立基準,暫視為穩定

    label = classify_hrv(reading, baseline)

    # 寫入 signals 供 fusion-classifier 取用
    session.signals.append({
        "type": "hrv",
        "phase": session.phase.value,
        "timestamp": reading.timestamp,
        "label": label,
        "rmssd": reading.rmssd,
        "lf_hf": reading.lf_hf,
    })
    return label
```

### 2. `signals/hrv_baseline_flow.py` — 正念冥想基準建立

```python
"""
迴圈前基準建立流程
==================
與 Pre-Training Protocol 整合:1 分鐘正念冥想期間採集 HRV。
"""

from signals.hrv import build_baseline, HRVReading


async def run_baseline_calibration(session, reading_stream):
    """
    正念冥想 1 分鐘,持續採集 HRV,結束後建立基準存入 session。
    """
    readings = []
    async for raw in reading_stream:        # 來自 HealthKit 串流
        readings.append(HRVReading(
            rmssd=raw["rmssd"], lf_hf=raw["lf_hf"],
            timestamp=raw["timestamp"]))

    baseline = build_baseline(readings)
    session.scratch["hrv_baseline"] = baseline
    # 同時記錄到 session 主欄位,供報告使用
    session.hrv_baseline = baseline.rmssd
    return baseline
```

---

## 設計重點

- **每迴圈重建基準**:不是訓練前校準一次,而是每個迴圈前的正念冥想都重建。
  這讓 HRV 判讀始終相對「當下狀態」,避免個體差異、當日疲勞、基準漂移。
- **相對而非絕對**:所有分類用「相對基準的比例」,不用絕對 RMSSD 數值,
  因為個體 HRV 差異極大,絕對門檻不可靠。
- **只採集不判斷**:本模組只輸出 drop/stable/flat 標籤,「這代表焦慮還是
  心流」的判斷交給 fusion-classifier 三訊號交叉驗證,職責分清。
- **嚴謹用語**:程式碼註解與報告皆稱 HRV 為「代理指標」,不宣稱直接測心流,
  符合文獻現況。
- **與 Pre-Training 整合**:基準建立 = 正念冥想,一舉兩得:既校準 HRV,
  又讓學員進入狀態。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:每迴圈正念冥想建基準 + RMSSD/LF-HF 相對分類 | 三大決策定稿,基準與 Pre-Training 整合 |

---

## 驗證方式

1. 正念冥想期間餵入多筆 HRV,確認 build_baseline 取中位數建立基準。
2. 餵入 RMSSD 低於基準 75% 且 LF/HF 升高,確認分類 'drop'。
3. 餵入 RMSSD 高於基準 125%,確認分類 'flat'。
4. 餵入基準帶內數值,確認分類 'stable'。
5. 確認每次分類都寫入 session.signals,含 label 與原始值。
```
