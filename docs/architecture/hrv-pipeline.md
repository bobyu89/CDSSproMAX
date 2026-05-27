# HRV Pipeline (Wave 3 — Skeleton)

## 為什麼要 HRV

OSCE 訓練本身就是高壓情境：學生在限定時間內面對標準病人、被觀察、且結果計入學業。
HRV（心率變異）— 特別是 **RMSSD** 與 **SDNN** — 是文獻中最被廣泛驗證的「認知負荷 / 急性壓力」生理代理指標（Shaffer & Ginsberg, 2017；Task Force, 1996）。

在 TICDSS 中，HRV 是 Fusion Engine 三大訊號之一：

```
Prosody (語音韻律) ─┐
HRV (心率變異)      ├─→  Fusion Engine  ─→ 學習者狀態  ─→ S/A-Agent context
Vision (表情/動作) ─┘
```

> **Wave 3 範圍**：本文件 + 程式碼建立**骨架**（裝置接入、儲存、時間域指標、UI 監視器）。 Fusion Engine 真正整合到 DUAT 評分是後續工作。

## BLE 資料流

```
Polar H10 chest strap
    │  GATT advertising — Heart Rate Service 0x180D
    ▼
Browser (Chrome/Edge) — Web Bluetooth
    │  navigator.bluetooth.requestDevice
    ▼
HR Measurement characteristic 0x2A37  (notify)
    │  RR pairs in 1/1024 s units → 轉 ms
    ▼
HRVMonitor.tsx  ── 5 秒批次 ──→  POST /physio/sessions/{sid}/samples
                                        │
                                        ▼
                                  physio_samples (Postgres)
                                  index: (session_id, timestamp_ms)
```

每次 0x2A37 notification 通常攜帶 1–3 個 RR 區間（Polar H10 在 ~5 Hz 推送）。

### Web Bluetooth 限制

- 僅 Chromium 系（Chrome / Edge / Brave）支援；Safari / Firefox / iOS 一律走「示範模式」。
- 必須在 HTTPS 或 `localhost` 環境。
- `requestDevice` **必須**由使用者手勢觸發（按鈕點擊）；不可在 `useEffect` 自動執行。
- 斷線後 GATT server 失效，需要重新配對。

## 儲存格式

`physio_samples` 表（見 `apps/api/src/db/models.py`）：

| 欄位 | 型態 | 說明 |
|---|---|---|
| `id` | UUID | PK |
| `session_id` | UUID FK | 對應 `sessions.id` |
| `device_id` | str(120) | 例如 `Polar H10 ABCD1234` 或 `mock-device` |
| `timestamp_ms` | **BigInteger** | 用毫秒級 epoch（Integer 在 2038 年溢位） |
| `r_to_r_ms` | Integer | 單一 RR 區間（ms） |
| `heart_rate` | Integer? | 瞬時 BPM（裝置提供時填入） |
| `quality_flag` | enum | `good` / `noisy` / `gap` |
| `created_at` | timestamptz | 伺服器時間 |

複合索引 `(session_id, timestamp_ms)` 讓「指定時間窗計算 HRV」是 index scan。

## 時間域指標

實作在 `apps/api/src/physio/hrv.py`，純 stdlib（HRV 窗口短，不需 numpy/scipy）。

| 指標 | 公式 | 生理意義 |
|---|---|---|
| **mean_hr** | `60000 / mean(RR)` | 平均心率 |
| **SDNN** | `sqrt( Σ(RRᵢ − mean)² / (n−1) )` | 整體自律神經變異 |
| **RMSSD** | `sqrt( Σ(RRᵢ₊₁ − RRᵢ)² / (n−1) )` | 副交感（迷走）張力 — 認知負荷指標 |
| **pNN50** | `100 × #{|ΔRR| > 50 ms} / (n−1)` | 與 RMSSD 高度相關 |

> 健康成人短時段休息基準：RMSSD 約 19–75 ms、SDNN 約 30–100 ms（Shaffer 2017）。

## 狀態代理（state proxy）

`state_proxy_from_hrv(summary) → 'flow' | 'anxious' | 'low_engagement' | 'ambiguous'`

| 標籤 | 判定 | 邏輯 |
|---|---|---|
| **anxious** | RMSSD < 20 ms 或 HR > 100 | 迷走張力低落 / 心搏過速 → 交感主導 |
| **flow** | RMSSD ≥ 40 ms 且 HR ≤ 90 | 健康變異 + 放鬆心率 → 平靜投入 |
| **low_engagement** | SDNN < 20 ms 且 HR < 65 | 變異低但喚醒度也低 → 可能疲倦／脫離 |
| **ambiguous** | 以上皆非 | 無明確訊號，下游應視為「無資訊」 |

### 重要注意事項

- 這是**單通道代理**。實際的 Fusion Engine 必須同時看 prosody + 表情才能輸出狀態。
- 閾值刻意保守，寧可回 `ambiguous` 也不要對噪音過度解讀。
- HRV 受咖啡因、藥物、姿勢、年齡影響極大 — **不可診斷使用**。

## 隱私

HRV 屬個資保護法定義下的「健康資料」。本 skeleton 遵守：

- 樣本只存本機 Postgres，**不**上傳第三方雲端。
- 不寫入 `audit_logs/*.jsonl` 中的原始 RR — 稽核事件只記錄聚合指標（SDNN/RMSSD/state）。
- MinIO/S3 keyframe bucket 不接收任何 HRV 資料；HRV 為 DB-only。
- 不送任何 RR 給 LLM（E/S/A-Agent 拿到的是聚合狀態標籤）。

## API 介面

| 方法 | 路徑 | 用途 |
|---|---|---|
| POST | `/physio/sessions/{sid}/samples` | 批次 ingest（5 秒批） |
| GET | `/physio/sessions/{sid}/hrv?window_seconds=60` | 滑動窗時間域摘要 + state_proxy |
| GET | `/physio/sessions/{sid}/timeseries?limit=500` | 最近 N 筆 RR（畫圖） |
| DELETE | `/physio/sessions/{sid}/samples` | admin-only 清除 |

稽核事件：`physio.samples_ingested`、`physio.hrv_computed`、`physio.device_connected`。

## Wave 3 後續工作（尚未實作）

- [ ] **Fusion Engine**：合併 HRV / prosody / vision 為 `LearnerState`，餵入 S-Agent / A-Agent context。
- [ ] **頻率域 HRV**（LF/HF ratio）— 需要至少 2 分鐘穩定窗口與重採樣。
- [ ] **跨 session baseline**：個人化 RMSSD 基準線（同一人比較有效）。
- [ ] **品質判斷**：自動偵測 ectopic beats / motion artifact 並標 `noisy`。
- [ ] **OSCE 整場匯出**：把 RR 時間序列匯出為 CSV / EDF 供研究分析。

## 參考文獻

- Shaffer F, Ginsberg JP. *An Overview of Heart Rate Variability Metrics and Norms*. Front Public Health. 2017;5:258. doi:10.3389/fpubh.2017.00258.
- Task Force of the European Society of Cardiology and the North American Society of Pacing and Electrophysiology. *Heart rate variability: standards of measurement, physiological interpretation, and clinical use*. Circulation. 1996;93(5):1043-1065.
- Bluetooth SIG. *Heart Rate Service v1.0* (0x180D) & *Heart Rate Measurement* (0x2A37) characteristic spec.
