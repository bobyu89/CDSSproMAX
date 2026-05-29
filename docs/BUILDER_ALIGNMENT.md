# Builder 規格對齊報告（2026-05-29）

來源：`docs/builder-spec/`（從 `ticdss-builder.zip` 解壓）
比對對象：當前 `apps/api/src/`、`apps/web/`

## 一句話結論

**Builder 規格跟我們目前的代碼是兩套架構**，不是補強，是重新對齊。
但 80% 的「肉」可以留 — 真正要動的是「**骨頭**」（契約 + 註冊表 + LLM router），
然後把現有 agents 包進新契約裡。

---

## 架構衝突點（必須決策的 5 個）

### 衝突 1：DUAT 角色含義完全不同

| 字母 | 我們現在的定義 | Builder 的定義 |
|---|---|---|
| **O** | Orchestrator（流程狀態機） | Observe（彙整全程資料，先跑） |
| **E** | Evidence Extractor（**唯一** RAG 存取者） | Evaluate（評估，依賴 O） |
| **S** | Scorer（Claude） | Synthesize（綜整，與 E 並行） |
| **A** | Adversarial（對抗審查） | Analyze（依賴 E + S） |
| **M** | Drift Monitor（統計監控） | Memory（比對歷程） |

**這不是命名問題，是設計哲學差異**：
- 我們的 DUAT 是「item-scoped 即時評分」（一個 rubric item 跑一輪 E→S→A）
- Builder 的 DUAT 是「session 結束後的深度驗證」（System 2 慢思考）

**Builder 規格還有第二層**：迴圈中用 `realtime-scorer`（System 1 快評分），
迴圈結束才用 DUAT。我們現在**沒有 realtime-scorer 這層**。

### 衝突 2：契約抽象層缺失

| | 我們現在 | Builder |
|---|---|---|
| Agent 介面 | 各 agent 自己一個 class | `StageAgent` 統一抽象 + `StageScore`/`EvalResult` 二種輸出 |
| 註冊機制 | 寫死 import | `AgentRegistry` 熱插拔 |
| 替換成本 | 改代碼 + 改 router | 改一行 register |

我們現有的 agents 沒有實作 `StageAgent`。

### 衝突 3：LLM 呼叫沒抽象

我們現在：每個 agent 直接 `from src.services.llm_clients import gemini_generate_json`。
Builder 要：`from llm.router import call_llm` — 任務路由 + 備援 + 成本控制。
換 LLM 要改一行設定，不改代碼。

### 衝突 4：問診邏輯路線不同

| | 我們現在 | Builder |
|---|---|---|
| 問診 UX | ASR 自由問診 | ASR 自由問診（同） |
| LQQOPERA 檢核 | 結束後 E-Agent + S-Agent 跑 LLM 評 8 維度 | **即時混合**：關鍵字 80%（規則）+ LLM 20%（模糊） |
| anxiety 動態 | 沒做 | 第一版即做（病人語氣隨學員語速變） |

Builder 路線更便宜（80% 規則）+ 更即時（每句話評）+ 更教學化（病人會反應）。

### 衝突 5：訊號融合範圍不同

| | 我們現在 | Builder |
|---|---|---|
| HRV 採集 | ✅ Polar H10 → physio_samples | ✅ 同 |
| 語音停頓 | ❌ | ✅ `signal-pause.md` |
| 臉部表情 | ❌ | ✅ `signal-expression.md`（本地 FER + Gemini） |
| 融合分類 | ❌（HRV state_proxy 只是告警） | ✅ 加權投票（HRV 0.5 + pause 0.25 + expr 0.25）→ 即時調難度 |
| 壓力曲線 | ✅ 講義有 HRV 曲線 | ✅ 同（但用融合後狀態） |

---

## 可以留的「肉」（不要動）

| 模組 | 對應 Builder 規格 | 評估 |
|---|---|---|
| `apps/api/src/agents/e_agent.py` | Builder evaluate 角色 | **保留** — 證據萃取邏輯本身對；只是命名要換 |
| `apps/api/src/agents/s_agent.py` | Builder synthesize | **保留** — Claude 跨廠商評分對 |
| `apps/api/src/agents/a_agent.py` | Builder analyze | **保留** — 對抗 reviewer 對 |
| `apps/api/src/agents/v_agent.py` | Builder vision (techinque part) | **保留** — Gemini 視覺手法評對 |
| `apps/api/src/agents/arbiter.py` | Builder 沒對應（Builder 走 M-Agent memory） | **保留** — Arbiter 是我們研究亮點 |
| `apps/api/src/vision/marker_detector.py` | Builder vision v2.0 連續追蹤 | **保留** — 已是連續追蹤 |
| `apps/api/src/vision/anatomy_map.py` | Builder ANATOMY_MARKERS | **保留** — 15 個標籤 vs Builder 的 9 個（我們更全） |
| `apps/api/src/rag/*` | Builder knowledge-base + rag-note | **保留** — pgvector + BAAI/bge |
| `apps/api/src/physio/hrv.py` | Builder signal-hrv | **保留** |
| `apps/api/src/handout/*` | Builder output（6 種輸出） | **保留** — 已涵蓋 5/6 種 |
| `apps/web/components/handout/*` | Builder output 視覺化 | **保留** |
| `apps/api/src/audit/*` | Builder 沒對應（這是我們的研究亮點） | **保留** |
| `apps/api/src/services/storage.py` | Builder 沒對應 | **保留** |
| 前端 practice / osce / login / home | Builder UI 沒規格 | **保留** |

---

## 必須新增的「骨頭」

| 新檔案 | 對應規格 | 影響 |
|---|---|---|
| `apps/api/src/core/contract.py` | `core.md` | 定義 StageAgent / StageScore / EvalResult |
| `apps/api/src/core/session_state.py` | `core.md` | TrainingSession + Phase enum |
| `apps/api/src/core/registry.py` | `core.md` | AgentRegistry 熱插拔 |
| `apps/api/src/llm/router.py` | `llm-adapter.md` | 統一 LLM 呼叫入口 |
| `apps/api/src/agents/inquiry_agent.py` | `inquiry.md` | 包裝現有 E/S 為 StageAgent 子類 + 加關鍵字混合檢核 |
| `apps/api/src/agents/diagnosis_agent.py` | `diagnosis.md` | **新增** Top-3 排名診斷評分（之前 Q2 已決定要） |
| `apps/api/src/scoring/realtime.py` | `realtime-scorer.md` | 60% 規則 + 40% LLM 即時評分 |
| `apps/api/src/fusion/classifier.py` | `fusion-classifier.md` | 加權投票（HRV 0.5 + pause 0.25 + expr 0.25） |

---

## 暫不做的（Wave 2+ 或低優先）

| 模組 | 規格 | 暫緩理由 |
|---|---|---|
| `voice-output` (TTS) | `voice-output.md` | Wave 2，OSCE 虛擬病人才需要 |
| `avatar-presenter` | `avatar-presenter.md` | Wave 2 |
| `signal-pause` | `signal-pause.md` | 沒 HRV+pause+expr 三者一起不能融合，先做最有效的 HRV |
| `signal-expression` | `signal-expression.md` | 同上，且需 webcam 額外算力 |
| `case-generator` | `case-generator.md` | 38 份預寫 case 已夠 demo |
| `concurrency-manager` | `concurrency-manager.md` | Builder 自己說 prototype 不實作 |
| `roles-access` | `roles-access.md` | 我們已有 student/teacher/admin（與規格一致） |
| `dev-tools` | `dev-tools.md` | 低優先 |

---

## 對齊方案：三選一

### Plan A — 全部砍掉重練（不建議）
嚴格按 Builder 從 `core/contract.py` 開始重寫。
**成本**：丟掉 60+ commit、50+ 檔案。
**收穫**：架構乾淨。
**評估**：✗ 浪費已驗證的代碼，且 demo 路徑要重做。

### Plan B — 漸進對齊（**強烈建議**）
分四階段把 Builder 的「骨頭」植入現有代碼：

**Phase 1：契約層**（半天）
1. 建 `core/contract.py` — StageAgent / StageScore / EvalResult
2. 建 `core/registry.py` — AgentRegistry
3. 把現有 E/S/A/V agents wrap 成 `StageAgent` 子類（不動內部邏輯）
4. 註冊到 registry，duat router 改走 registry 而非直接 import

**Phase 2：LLM router**（2 小時）
1. 建 `llm/router.py` 包住 `llm_clients`
2. 把現有 agents 的 LLM 呼叫改走 router
3. `.env` 加任務 → 模型映射表

**Phase 3：缺的功能補**（1–2 天）
1. `agents/diagnosis_agent.py` — Top-3 排名診斷（新賣點）
2. `scoring/realtime.py` — 60% rule + 40% LLM 即時評分（新賣點）
3. `agents/inquiry_agent.py` — LQQOPERA 關鍵字 80% + LLM 20% 混合檢核
4. `core/session_state.py` — TrainingSession 統一狀態

**Phase 4：DUAT 重新對齊**（半天）
1. 把現有 E/S/A 的職責「文件上」對應到 Builder 的 evaluate/synthesize/analyze
2. 補 O-Agent（observe）和 M-Agent（memory）— 我們已有空殼，補實作
3. 重排執行順序為 `O → (E‖S) → A → M`
4. **不改名**，只在 docstring 標清楚對應關係（避免重命名引發大爆炸）

**總成本**：3–4 個工作天。
**收穫**：拿到 Builder 的熱插拔架構，且現有功能全保留。

### Plan C — Builder 當未來路線圖（保守）
現在不動代碼，只把 Builder 當「下版本目標」。
**評估**：✗ 已知有缺的功能（realtime-scorer、Top-3 診斷、融合分類）會繼續沒做。

---

## 我的建議

**選 Plan B**，並且：

1. **先做 Phase 1 + 3**，跳過 Phase 2 和 4 — 真正的論文/得獎賣點在「Top-3 診斷」+「realtime-scorer」+「fusion classifier」這三個新功能，契約層是好架構但不是賣點。
2. **DUAT 角色衝突**：我們的 E/S/A/M/O 命名已經寫進 source-of-truth + audit log + manuscript draft，**不要改名**。在 `BUILDER_ALIGNMENT.md` 留一個對照表給讀 Builder 的人看就好。
3. **Phase 2 (LLM router)** 可以晚一點再做 — 現在硬綁定 Claude/Gemini 不會立刻出事。

---

## 下一步請你決定

**Q：採用哪個 Plan？**
- A. Plan B 完整版（4 個 phase 全做，4 天）
- B. **Plan B 精簡版（只做 Phase 1 + Phase 3，2 天）** ← 我建議
- C. Plan C（先觀望，繼續 demo path 驗證）
- D. 其他想法

回答後我會：
- 開新 Wave（Wave 1.9: Builder Alignment）
- 把任務拆成具體 step
- 開始動工
