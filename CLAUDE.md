# Claude 工作指引（TICDSS 專案）

## 專案脈絡

這是 **TICDSS**（Technology-Integrated CDSS），對應 JMIR Medical Education 投稿論文 *TICDSS-DUAT：護理 OSCE 多驗證性評量機制系統設計研究*。

**獨立於舊專案 `../cdss-training/`**——不共用 repo / DB / port，舊系統繼續運作。

## 核心設計（不可違反）

### 1. DUAT 五代理人架構

| Agent | 角色 | 模型 | Context 上限 |
|---|---|---|---|
| **O-Agent** | 主控/狀態機 | FastAPI 邏輯（例外時 Claude） | 結構化狀態圖 |
| **E-Agent** | 證據萃取（**唯一**接 RAG） | Gemini 3.5 Flash | 300-500 tokens |
| **S-Agent** | 評分（逐條 CoT） | Claude Opus 4.7 | 600-800 tokens |
| **A-Agent** | 對抗審查 | Gemini 3.5 Flash | 400-600 tokens |
| **M-Agent** | 漂移監控（**全程運作**） | 規則 + LLM 統計 | 跨 session |

### 2. 不可妥協的設計原則

- **E-Agent 唯一存取原則**：只有 E-Agent 能查 RAG / Bibliotheke。S、A、M 收到的「事實」必須由 E-Agent 產出的 Evidence Bundle 提供。
- **Consensus Arbiter 是規則型，不是 LLM**：三層決策（accept / flag / force_human）必須是純函式、可單元測試、可稽核。
- **Context 最小化**：每個 Agent 一次只處理一個 rubric item，禁止整場逐字稿丟給單一 Agent。
- **Audit Log 完整性**：每筆評分必須寫 JSONL，欄位含 prompt hash 與 model version，供後續論文重現。

### 3. 模型選擇

- `S_AGENT_MODEL=claude-opus-4-7`
- `E_AGENT_MODEL=gemini-3.5-flash`（已 GA，1M context, thinking, vision）
- `A_AGENT_MODEL=gemini-3.5-flash`
- `V_AGENT_MODEL=gemini-3.5-flash`（Wave 1.5）

**禁止隨意換模型**——論文要求模型版本可追溯，要換得改 Protocol。

### 3a. Wave 1.5 — Vision 雙層設計

PE 評分採「**ArUco 解位置 + V-Agent 解手法**」雙層：

| 層 | 解決 | 技術 | 信心 |
|---|---|---|---|
| Layer 1 | 位置 (80%) | OpenCV ArUco DICT_4X4_50 | deterministic |
| Layer 2 | 手法 (20%) | Gemini 3.5 Flash Vision (V-Agent) | LLM 語意 |

- 15 個 marker 對應半身假人解剖位置 — 定義在 `apps/api/src/vision/anatomy_map.py`
- 連續遮蔽 ≥ 1.5 秒 = 該位置被觸碰
- V-Agent 不評位置（職責切割），只評動作正確性 / 技巧 / 持續時間
- V-Agent 為 Wave 1.5 階段 stub — 真接 Gemini Vision multimodal 在 Wave 1.6
- 詳見 `docs/architecture/vision-pipeline.md`

### 4. 技術棧

| 層 | 技術 | 不可換 |
|---|---|---|
| 前端 | Next.js 15 (App Router) + TS | 是 |
| 後端 | FastAPI + Pydantic v2 + SQLAlchemy 2.x async | 是 |
| DB | PostgreSQL 17 + pgvector | 是 |
| ORM Migration | Alembic | 是 |
| 前端套件管理 | pnpm | 是 |
| 後端套件管理 | uv | 是 |
| 前端 state | Zustand | 偏好 |
| 測試 | pytest（後端）+ Playwright（前端 E2E） | 偏好 |

### 5. Port 分配（不撞舊專案）

- Web: **3000**
- API: **8001**（舊 CDSS 用 8000）
- ASR: **8002**
- Postgres: **5433**（舊系統若用 5432）
- Langfuse: **3001**

## 工作習慣

- **不要動到 `../cdss-training/`**——這是舊系統，要保持穩定運作
- **不要過早優化**——Wave 1 都本地跑，不做 K8s / CI/CD / RBAC
- **不要加 Wave 範圍外的功能**——Vision (Wave 1.5)、Avatar (Wave 2)、Fusion (Wave 3) 都不要先寫
- **資料夾路徑含中文**——`G:\其他電腦\我的筆記型電腦\Desktop\AI 專案\ticdss\`，PowerShell 命令注意引號
- **每完成一步要可驗證**——Step N 結束 = 跑得起來 / test 過 / curl 通

## 論文對應

程式碼結構應該能對應到 Protocol §四（DUAT 系統設計）的描述。寫 code 時：
- agent class 名稱 = Protocol 中的 Agent 名稱
- Rubric JSON schema 對應 Protocol §四.(四)
- Audit Log 欄位對應 Protocol §四.(七)
- Arbiter 規則對應 Protocol §四.(三) 表二

如果發現程式碼跟 Protocol 不一致，**先停下來問使用者**——可能是設計變更，要同步更新 Protocol。

## 參考文件位置

- 技術計畫書：`docs/技術計畫書.docx`（待複製）
- DUAT v4 Protocol：`docs/DUAT_v4_Protocol.docx`（待複製）
- 架構決策：`docs/architecture/`
