# TICDSS

**Technology-Integrated Clinical Decision Support System** — 多代理人 OSCE 評量系統，專為台灣 NP（專科護理師）臨床推理訓練設計。

> 對應 JMIR Medical Education 投稿論文：*TICDSS-DUAT：護理 OSCE 多驗證性評量機制系統設計研究*

## 系統定位

- **DUAT**（Distributed Unified Assessment Tribunal）—— 五代理人並行驗證 OSCE 評分架構
- **LQQOPERA + PE 雙軌評分**
- **Intent-First 互動**：學員語音宣告 → 系統聚焦評核
- **Breeze-ASR-25 本地 ASR**：台灣中英混碼語音辨識，資料不出機構

## 與舊系統的關係

本專案**獨立於** `cdss-training/`（舊 CDSS 系統），不共用 repo / DB / port。
舊系統繼續維運 peOsce 等功能，新系統重新設計架構以支援 DUAT。

## 目錄結構

```
ticdss/
├── apps/
│   ├── web/      Next.js 15 前端
│   ├── api/      FastAPI 後端（DUAT 五代理人 + RAG）
│   └── asr/      Breeze-ASR-25 語音辨識服務
├── packages/
│   ├── shared-types/    前後端共用 TypeScript types
│   └── shared-prompts/  Agent prompts
├── data/         案例、Rubric、知識庫種子
├── evaluation/   Ablation Study 框架
├── scripts/      DB seed / 匯入工具
└── docs/         計畫書、Protocol、架構文件
```

## 快速啟動（開發環境）

```bash
# 1. 安裝依賴
pnpm install                          # 前端 / monorepo
cd apps/api && uv sync && cd ../..    # 後端
cd apps/asr && uv sync && cd ../..    # ASR 服務

# 2. 設定環境變數
cp .env.example .env
# 編輯 .env 填入 ANTHROPIC_API_KEY / GOOGLE_API_KEY

# 3. 起基礎設施（Postgres + Langfuse）
pnpm infra:up

# 4. 跑 DB migration
cd apps/api && uv run alembic upgrade head && cd ../..

# 5. 啟動各服務（分別開三個終端）
pnpm dev:api   # http://localhost:8001
pnpm dev:web   # http://localhost:3000
pnpm dev:asr   # http://localhost:8002 (需 GPU)
```

## 技術棧

| 層 | 技術 |
|---|---|
| 前端 | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui |
| 後端 | FastAPI + Pydantic v2 + SQLAlchemy 2.x async |
| 資料庫 | PostgreSQL 17 + pgvector |
| LLM | Claude Opus 4.7（S-Agent）、Gemini 3.5 Flash（E/A/V-Agent） |
| ASR | MediaTek Breeze-ASR-25（本地 GPU） |
| Embedding | BAAI/bge + Cross-Encoder reranker |
| 觀測 | Langfuse（self-host）+ Audit Log (JSONL) |

## 開發狀態

- [x] Wave 1 骨架（repo / docker / FastAPI / DB / agent shells / Arbiter）
- [ ] Wave 1 完成（LLM 真接 + LQQOPERA + RAG + Audit + Evaluation）
- [ ] Wave 1.5 Vision Agent（ArUco + Gemini 3.5 Flash Vision）
- [ ] Wave 2 Dialog Agent + Avatar + Case Authoring
- [ ] Wave 3 Fusion Engine（HRV + 表情）

## 授權

研究用途。模型權重與外部 API 依各自授權。
