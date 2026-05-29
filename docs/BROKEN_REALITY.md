# TICDSS Broken Reality Check（2026-05-28）

**目的**：誠實列出「從 `docker-compose up` 到 `/handout/[id]` 這條 demo path」實際會壞在哪。**只看代碼，不寫修補**。

## 🔴 BLOCKERS（路徑直接斷）

### B1. `vision` router 沒被註冊到 main.py

- 檔案：`apps/api/src/main.py` 第 13–24 行
- 現況：import 了 `admin / auth / cases / duat / grading / handout / health / physio / sessions / transcripts`，**沒有 vision**
- 影響：所有 `/vision/*` 端點都 404 — `markers/detect` / `markers/track` / `v-agent` / `anatomy-map` / `health` 全部
- 連鎖：StepPE / VisionPeAssist / `/admin/calibration` / `AnatomyHeatmap` 全部跑不起來
- **這就是「Wave 1.5 + 1.7 shipped」其實沒在跑的根因**

### B2. DUAT scoring 要求 teacher/admin 角色

- 檔案：`apps/api/src/routers/duat.py` 第 97, 142 行
- 現況：`score-item` 和 `score-all-lqqopera` 都用 `require_role("teacher", "admin")`
- 影響：學生在 StepSummary 自動觸發 `scoreAllLqqopera()` 會 **403 Forbidden**
- 連鎖：`api.ts` 的 try/catch 把 403 吃掉 → fallback 到 `MOCK_DUAT_SCORES` → **使用者「看到」評分但其實是假資料**
- 講義頁的 confidence calibration / annotated transcript 全部依賴真 score → 全部會走 mock

### B3. PE 評分沒有從學生練習流程觸發

- 學生在 StepPE 走 `vision/sessions/{sid}/v-agent`（B1 已死）
- 即便 vision router 註冊，學生流程裡沒有「打完 PE → DUAT 也評分」的橋
- 結果：講義頁的 PE radar 永遠是空

---

## 🟠 BREAKS（會跑但行為錯）

### Br4. ASR 前端直接打 port 8002，違反 spec

- 檔案：`apps/web/lib/asr.ts` 第 32 行 — `fetch('http://localhost:8002/transcribe')`
- spec 寫：「browser 絕不直接打 8002，由 FastAPI proxy」
- 風險：跨 origin CORS、無法在 audit log 記錄是哪個 ASR 跑的
- demo 在 localhost 會 work，部署到別人機器很可能炸

### Br5. `vision.py` 用 occluded_regions 沒帶 max_touch_window_s

- 檔案：`apps/api/src/routers/vision.py` 第 200 行 — `occluded_regions(tracker, now, _OCCLUSION_THRESHOLD_S)`
- 上次 code review 修 marker_detector 加了 `max_touch_window_s=8.0`，但 router 沒帶
- 結果：marker 一次消失就被永遠標記為「觸碰過」— 跟單元測試不符

---

## 🟡 SILENT FALLBACKS（看起來有資料、其實是假的）

### Sf6. `fetchRubric` 永遠回 MOCK_RUBRIC

- 檔案：`apps/web/lib/api.ts` 第 411 行
- 即便後端有 rubric router，前端永遠不會問

### Sf7. `api.ts` 所有 catch 都 silently fall back to mock

- 影響：使用者看到的所有畫面都「看起來在跑」，但其實任何一個後端錯都被吞掉
- 這就是為什麼你覺得「東西做一半」— UI 用 mock 撐起一個假象

### Sf8. 案例不是 LLM 生成

- 38 份預寫 markdown 由 `import_cases.py` 灌進 DB
- 你原本舊 CDSS 設計用 LLM 動態生成，但既然賣點換成「DUAT + ArUco」，案例 LLM 生成可以**先不做**

---

## ❌ MISSING（已宣告的賣點，根本沒做）

### M1. Intent-First 閉環沒有打通（**這是新賣點，要做**）

- `IntentRecorder.tsx` 元件存在
- `VisionPeAssist.tsx` 會傳 `student_intent` 字串給 backend
- **但沒有**：ASR 即時辨識 → 解析「auscultation/palpation/percussion」→ 觸發對應子評分窗 → V-Agent 只看那段 keyframes
- 現在的行為：學生口頭講什麼 backend 都當 plain string，V-Agent 一視同仁

### M2. Top-3 排名診斷沒做

- `StepDiagnosis.tsx` 我推測是單一文字框（page.tsx 只看到 `diagnosis` 單值）
- 你要的是 `[{rank:1, dx, reason}, {rank:2,...}, {rank:3,...}]` 結構

### M3. OSCE 虛擬病人對話 (Dialog Agent) 沒做

- 這是 Wave 2 規劃中的東西，目前完全是 0

### M4. OSCE Live streaming 評分沒做

- 目前 V-Agent 是「收完一批 keyframes → 一次評分」
- 你要的是 OSCE 6 分鐘內邊做邊評

---

## 修復優先順序（給 demo path 用）

| 優先 | 動作 | 解的 break |
|---|---|---|
| P0 | main.py 加 `vision` router 註冊 | B1 |
| P0 | duat.py 把 scoring 改成「session 擁有者 or teacher/admin」 | B2 |
| P0 | StepSummary 完成 session 後同時觸發 vision 評分（如果該 case 有 PE rubric） | B3 |
| P1 | api.ts 移除 silent mock fallback — 失敗就顯示「後端錯」橫幅 | Sf7 |
| P1 | vision.py 補 `max_touch_window_s=8.0` | Br5 |
| P1 | StepDiagnosis 改 Top-3 排名 | M2 |
| P2 | Intent-First 閉環（賣點 — 論文亮點） | M1 |
| P2 | ASR 改走 API proxy | Br4 |
| P3 | fetchRubric 真的接 API | Sf6 |
| 暫緩 | Dialog Agent + OSCE Live streaming | M3, M4 |
| 暫緩 | LLM 案例生成 | Sf8 |

P0–P1 大約 1 個工作天可以完成；P2（Intent-First）大約半天到 1 天；P3 之後再說。

**修完 P0–P1 = 一條完整的 demo path 跑得起來**：登入 → 練習 → 真實 DUAT 評分 → 真實 PE 評分 → 講義。**P2 加上 Intent-First = 論文 + 創新獎的差異化亮點**。
