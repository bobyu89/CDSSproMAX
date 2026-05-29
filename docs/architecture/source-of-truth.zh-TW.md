# TICDSS Source of Truth（繁體中文）

> 英文版 `source-of-truth.md` 為唯一權威來源。本檔僅為閱讀輔助；兩者衝突時以英文版為準。

TICDSS 是面向台灣護理師 OSCE 訓練與評核的可稽核評量系統，涵蓋 LQQOPERA 病史問診、PE 身體檢查、教師複核與可重現的稽核紀錄。它**不是聊天機器人**。研究核心為 DUAT（Distributed Unified Assessment Tribunal，分散式統一評核審議）。本 repo 與 `../cdss-training/` 完全獨立，**不共用** DB、port 或 runtime。

## 文件權威順序

來源衝突時：

1. 本檔（英文版）
2. `AGENTS.md` / `CLAUDE.md`
3. 其他 `docs/architecture/*.md`
4. 當前 branch 上的程式碼（程式碼與規格不一致時視為漂移 — 要決策，不要默默「修正」其中一邊）
5. 協定 manuscript 草稿
6. 技術提案草稿
7. README / changelog
8. 本檔（繁中翻譯）

## Canonical 技術棧

| 層 | 選用 |
|---|---|
| 前端 | Next.js 15 App Router + TypeScript、pnpm、Zustand |
| 後端 | FastAPI + Pydantic v2、SQLAlchemy 2.x async、uv |
| 資料庫 | PostgreSQL 17 + pgvector（**非** ChromaDB） |
| ASR | Breeze-ASR-25 sidecar（HTTP，port 8002）— 非 Deepgram、非瀏覽器 STT |
| 觀測 | JSONL 稽核日誌（**強制**）+ 選用 Langfuse |
| 測試 | pytest + Playwright |

Ports：Web 3000、API 8001、ASR 8002、Postgres 5433、Langfuse 3001。

## Canonical 模型對應

| Agent | 模型 | 備註 |
|---|---|---|
| O-Agent | 規則型狀態機 | 例外狀態恢復才允許 LLM 輔助 |
| E-Agent | `gemini-3.5-flash` | **唯一** 可存取 RAG 的 agent |
| S-Agent | `claude-opus-4-7` | Anthropic — 與 A-Agent 跨廠商是刻意設計 |
| A-Agent | `gemini-3.5-flash` | 必須獨立判斷，不可附和 S-Agent |
| M-Agent | 規則 + 統計監控 | 之後可選用 LLM 摘要 |
| V-Agent | `gemini-3.5-flash` multimodal | 視覺路徑 |

更換任何模型 = 協定變更：必須同步本表、`.env.example`、prompts、稽核日誌期待值、manuscript。舊草稿提到的 Gemini 3.1 Pro / Deepgram / ElevenLabs / ChromaDB / Stream Vision Agents 屬草稿用詞，**非** canonical。

## DUAT

### 不可妥協原則

1. **E-Agent 是唯一 RAG 存取者。** S/A/M 絕不可查 Bibliotheke 或 pgvector — 它們只能透過 Evidence Bundle 取得事實。
2. **Arbiter 為規則型。** 純函式、可測試，**非** LLM 呼叫。
3. **Context 以 item 為界。** 一次 agent 呼叫 = 一個 rubric item。不可把整份逐字稿丟給評分 agent。
4. **JSONL 稽核強制。** 每條評分路徑必須記錄 prompt hash、模型版本、rubric item id、可重播 payload。
5. **人類問責為最終裁決。** DUAT 提供建議與旗標；教師可接受 / 修改 / 駁回。

### Agent 介面

| Agent | 輸入 | 輸出 |
|---|---|---|
| O-Agent | Session 狀態、phase、模式 | 下一階段、路由、時限 |
| E-Agent | Rubric item id、scoped 逐字稿、case context | Evidence Bundle JSON |
| S-Agent | Rubric item + Evidence Bundle | 0–5 分、推理、引用 evidence id |
| A-Agent | Rubric item + Evidence Bundle | Advocate 分數、爭議點 |
| M-Agent | 歷史分數 / override 統計 | Override 率告警 |

**不可** 使用技術提案早期的 observation/evaluation/synthesis/analysis/memory 對應 — 那是另一個概念。

### Arbiter（v1 閾值）

動作：`accept` / `flag` / `force_human`。

| `e_confidence` | `a_advocate_score` | 動作 |
|---|---|---|
| ≥ 0.80 | < 0.30 | `accept`（高） |
| ≥ 0.50 | < 0.50 | `flag`（中） |
| 其他 | 其他 | `force_human`（低） |

協定中的「High Confidence / Review Needed / Uncertainty Flag」對應到 `accept` / `flag` / `force_human`。

## Wave 範圍

新功能必須標註所屬 wave。後續 wave 在使用者明示變更前暫停。允許跨序交付，但必須在此記錄（見 Wave 4）。

### Wave 1 — DUAT LQQOPERA *（已交付）*

垂直切片：登入 → case/session/逐字稿 → rubric → E/S/A → Arbiter → `duat_scores` → 教師複核 → 稽核 JSONL。含 pgvector Bibliotheke RAG（僅 E）、基本 admin 後台、ablation 評估 scripts。

不在範圍：Avatar、Dialog Agent、Fusion Engine、HRV 影響評分、視覺影響 LQQOPERA、講義擴充。

驗收：API 在 8001 啟動、migrations 乾淨、`/health` OK、可從建立 session → 評分 → 複核 → 重播稽核；agent/arbiter/audit/rubric/router 的 pytest 通過。

### Wave 1.5 + 1.7 — PE 視覺評核與融合 *（已交付）*

雙層 PE 評核，融合為單一可稽核分數。

| 層 | 負責 | 不可做 |
|---|---|---|
| ArUco（OpenCV `DICT_4X4_50`） | 身體區域 / 位置 | 判斷技巧 |
| V-Agent（Gemini multimodal） | 動作、技巧、時長 | 覆寫確定性位置判定 |
| `pe_fusion.py` | 合併 → `duat_scores` 一列 | 不可放在他處 |

Canonical 規則：

- 15 個解剖標籤定義於 `apps/api/src/vision/anatomy_map.py`。
- 觸碰 = 標籤連續被遮蔽 **1.5s – 8.0s**。上限是 re-arm 視窗 — 沒有上限的話，標籤一旦消失就永遠被視為觸碰。
- Fusion v1：`位置 0.80 + 技巧 0.20 + rubric 達標時的時長加分`。`duat_scores` 寫單一列。
- Keyframes → S3 相容儲存（dev 用 MinIO），經 `services/storage.py`。`NoopStorage` 是 fallback — 沒 MinIO 也要正常運作。
- Re-score endpoint 從儲存取回 keyframes；client **絕不** 重新上傳。
- `keyframes` bucket 套 90 天 ILM lifecycle。

硬體基線：標準 webcam（≥ 720p、15 fps）、印製標籤 ≥ 5 cm 邊長、霧面紙、單一固定角度。`/admin/calibration` 必須顯示 15 個標籤全部穩定 ≥ 3 秒，才能開始 OSCE。

驗收：`/vision/health` 可達；anatomy map 回傳 15 個；OpenCV 缺席時 detector 回傳空（不可拋例外）；PE observations 持久化；固定輸入下 fusion 確定性；re-score 重用儲存中的 keyframes；測試涵蓋兩個 occlusion 邊界、fusion、儲存 fallback。

### Wave 2 — Dialog Agent 與 Avatar *（未開始）*

Wave 1 / 1.5 / 1.7 驗收穩定後才開始。範圍：

- Dialog Agent 標準化病人回應（練習 = 變化、考試 = 標準化）。
- Avatar / TTS / 對嘴。
- Prosody 萃取供日後 Fusion 使用。
- **這層的候選項目，不放在 Wave 1.5：** MediaPipe Tasks Vision（Hands + Pose Landmarker）作為 V-Agent 技巧判斷的確定性手勢特徵輸入。ArUco 仍是位置的 source of truth。

Deepgram、ElevenLabs、外部 avatar 服務屬提案期選項 — 加入任何一項都是協定變更。

### Wave 3 — HRV 與 Fusion Engine *（HRV 擷取已交付，Fusion 未開始）*

HRV 現況：Web Bluetooth Polar H10 擷取 → `physio_samples`；SDNN、RMSSD、pNN50、mean HR；`state_proxy` 為非診斷性訓練訊號。

**HRV 僅供監看。在 Fusion 被明確設計前，不可進入 S/A 的 context。**

Fusion Engine 未來範圍：把 HRV + prosody + 視覺行為合成 `LearnerState`；決定是否與如何進入評分 context；考試模式行為保守且可稽核。

驗收（屆時）：HRV 摘要可用；原始 RR 僅留 DB（除非明確匯出）；Fusion 規則先文件化、測試完成，再用於影響評分。

### Wave 4 — 個人講義 *（跨序交付的最小版本）*

依使用者明示要求提前到 Wave 2/3 之前，目的是在現有 Wave 1 分數上驗證 end-to-end debrief UX。v1 功能完成；擴充（更豐富的 mindmap、多 session 趨勢）暫停，等 Wave 2/3 穩定。

已交付：`apps/api/src/handout/`（schema、aggregator、LLM 生成器）；`apps/web/app/handout/[sessionId]/` 頁面含 10 張卡片（雷達圖、信心校準、學習要點、心智圖、HRV 曲線、心流預測、討論提示、間隔重複、自我評估、逐字稿標註）。生成結果快取於 `sessions.generated_handout_json`；重新生成或提交自我評估時 invalidate。

規則：

- 講義**絕不**回饋 DUAT 評分。HRV / 自我評估 / 信心校準訊號在此路徑只能讀。
- 評分紀錄完成後才生成。
- AI 生成的反思必須在視覺上與「教師確認的評核」明確區隔。
- 逐字稿標註用 substring fuzzy match 比對 `e_evidence_json.evidence_segments` — **UX 級，非 evidence 級**。**不可** 把這些 match 升級為評分輸入。

## 資料所有權

| 資料 | Source of truth |
|---|---|
| 學員 | `participants` |
| Cases | `cases`（由 `data/cases` seed） |
| Rubrics | `data/rubrics` + 匯入後的 `rubrics` 表 |
| 逐字稿 | `transcripts` |
| DUAT 分數 | `duat_scores` |
| 稽核 | JSONL 日誌；`audit_events` 為查詢 mirror |
| RAG chunks | `bibliotheke_chunks`（pgvector） |
| HRV | `physio_samples` |
| PE 觀察 | `pe_observations` |

每個 migration 必須對應一個 ORM model，反之亦然。**不允許半連線的 schema**。

## 開發規則

碰到 canonical 層的每次 commit 必跑漂移檢查：

- `apps/api/src/config.py` 的模型對應 Canonical Models 表。
- `apps/api/src/agents/arbiter.py` 的常數對應 Arbiter 閾值表。
- `apps/api/src/vision/anatomy_map.py` 剛好 15 個標籤。
- 每個 Alembic migration 都有對應 ORM model。

每個完成的步驟必須以下列至少一項可驗證：通過的測試、成功的 API 呼叫、乾淨的 migration、可重現的 script、或文件化的手動驗證路徑。
