# Vision Pipeline 設計文件 (Wave 1.5)

對應原技術計畫書「Vision Agent」設計與 §四.(三) 表二 DUAT Arbiter 規則。

## 雙層架構

```
            攝影機 (webcam, getUserMedia)
                        │
            ┌───────────▼────────────┐
            │  前端 CameraCapture     │
            │  每 500ms 擷取一張 JPEG │
            └───────────┬────────────┘
                        │ base64 frame
            ┌───────────▼─────────────────────┐
            │ Backend /vision/markers/detect  │
            │ Layer 1 — ArUco DICT_4X4_50    │
            │ OpenCV CPU, sub-second          │
            └───────────┬─────────────────────┘
                        │ MarkerDetection[]
                        │
            ┌───────────▼─────────────────────┐
            │ /vision/sessions/{id}/track     │
            │ in-memory tracker per session   │
            │ 連續遮蔽 ≥ 1.5s → "region touched"│
            └───────────┬─────────────────────┘
                        │
                        │ 學員口頭宣告 (Intent-First, ASR)
                        │ + 持續時間 (動作開始到結束)
                        │
            ┌───────────▼─────────────────────┐
            │ /vision/sessions/{id}/v-agent    │
            │ Layer 2 — Gemini 3.5 Flash Vision│
            │ keyframes burst → JSON score    │
            └───────────┬─────────────────────┘
                        │
                        ▼
              PeObservation 寫入 DB
              + audit event (vision.v_agent_scored)
              + DUAT 整合 (與 E/S/A 並列入 Arbiter)
```

## 為什麼分兩層

| 維度 | Layer 1 (ArUco) | Layer 2 (V-Agent) |
|---|---|---|
| 角色 | 解「**位置**」 | 解「**手法品質**」 |
| 信心 | 確定性（毫秒） | 語意（秒級） |
| 成本 | 0 (CPU) | ~$0.005/burst |
| 失敗模式 | marker 偵測不到 → 無輸出 | LLM 不可用 → 跳過評分 |
| 覆蓋 | 80% PE 評分 | 補 20% (手法、流程、姿態) |

由於 OSCE 情境的位置評分是「對 or 錯」（毫米級的位置精度不重要），
deterministic ArUco 比 LLM-as-judge 更可靠且免費。
V-Agent 只在 Layer 1 確認位置正確之後才介入評估手法。

## 與 DUAT pipeline 的關係

對於 LQQOPERA 8 維度（純問診），V-Agent 不參與。
對於 PE 評分項目，pipeline 變成：

```
                     ┌→ S-Agent (語意評分: Rubric vs PeObservation)
E-Agent (RAG) ───────┼→ A-Agent (對抗審查)
                     └→ V-Agent (視覺評核, optional)
                                 │
                                 ▼
                         Consensus Arbiter
```

當 V-Agent 結果不可用時（OpenCV 缺、Gemini 失敗、無攝影機），系統
退回到「只有 S+A 評分」的 DUAT 模式 — 不阻斷學員作答。

## 設計決策

### 為什麼 ArUco 不是其他 marker？

- **OpenCV 內建**: 不需自訓模型，cv2.aruco 開箱即用
- **DICT_4X4_50 已夠**: 我們只需 16 個 marker
- **論文好引用**: ArUco 已是視覺定位的事實標準（Garrido-Jurado et al., 2014）
- **A4 列印就能用**: 5cm marker 在 1-2 公尺距離可穩定偵測

### 為什麼 1.5 秒遮蔽閾值？

- 真實觸診/聽診動作至少 2-3 秒
- 1.5 秒可避免「手揮過去」的誤判
- 可在 `routers/vision.py` 的 `_OCCLUSION_THRESHOLD_S` 調整
- Phase 1 Pilot 後依誤判率重新校準

### 為什麼 V-Agent 不評位置？

避免 ArUco 與 V-Agent 在同一面向上意見衝突。職責分明 → 容易排查 → 容易解釋
給 reviewer。Prompt 明確要求 V-Agent「不評位置」。

### 不考慮深度的取捨

- ✓ 系統簡單（單鏡頭、無立體視覺、無 depth sensor）
- ✓ 學員只需一台筆電 + USB webcam
- ✗ 觸診壓力深淺無法評估（在 Wave 3 用 HRV/EMG 補）
- ✗ 「聽診器是否平貼皮膚」要靠 V-Agent 從多角度 keyframes 推斷

## 校準流程

第一次裝置上線時：

1. 列印 `data/aruco/anatomy_markers.pdf` (15 頁 × 1 marker)
2. 依 README 對照表貼到假人
3. 將攝影機架在距假人約 1-1.5 公尺、與胸部同高的位置
4. 進入「校準頁面」(待建)：
   - 即時顯示所有偵測到的 marker ID
   - 若某 marker 偵測不到 → 重新貼附或調光
   - 確認所有 15 個 marker 都能被穩定偵測再開始正式評核

## 目前實作狀態

| 元件 | 檔案 | 狀態 |
|---|---|---|
| Anatomy map | `apps/api/src/vision/anatomy_map.py` | ✅ 15 markers |
| Marker detector | `apps/api/src/vision/marker_detector.py` | ✅ lazy OpenCV |
| Frame helpers | `apps/api/src/vision/frame_capture.py` | ✅ |
| Vision router | `apps/api/src/routers/vision.py` | ✅ 5 endpoints |
| V-Agent | `apps/api/src/agents/v_agent.py` | 🚧 stub (待接 Gemini multimodal) |
| PeObservation ORM | `apps/api/src/db/models.py` | ✅ + alembic 0002 |
| Audit event types | `apps/api/src/audit/schema.py` | ✅ 3 個 vision 事件 |
| Frontend CameraCapture | `apps/web/components/vision/CameraCapture.tsx` | ✅ |
| MarkerOverlay SVG | `apps/web/components/vision/MarkerOverlay.tsx` | ✅ |
| TouchedRegionsPanel | `apps/web/components/vision/TouchedRegionsPanel.tsx` | ✅ |
| Vision API client | `apps/web/lib/vision.ts` | ✅ |
| Shared types | `packages/shared-types/src/vision.ts` | ✅ |
| ArUco PDF 生成器 | `scripts/generate_aruco_pdf.py` | ✅ |
| Tests | `apps/api/tests/test_vision_*.py` | ✅ 3 個 |
| DUAT pipeline 整合 | `apps/api/src/agents/pipeline.py` | ⏳ Wave 1.6 |
| StepPE 介接 V-Agent | `apps/web/components/practice/StepPE.tsx` | ⏳ Wave 1.6 |
| Gemini Vision multimodal | `apps/api/src/agents/v_agent.py` | ⏳ Wave 1.6 |
| 校準頁面 | `apps/web/app/admin/calibration/` | ⏳ Wave 1.6 |
