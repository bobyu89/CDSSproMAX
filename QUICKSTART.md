# TICDSS 快速啟動

從零到能登入 `localhost:3000`、進行一次練習的最短路徑。

## 前置需求

- **Node.js 20+** 與 **pnpm 9+**（前端）
- **uv**（Python 套件管理；後端 + ASR）
- **Docker Desktop**（Postgres + Langfuse）
- **NVIDIA GPU** 與 **CUDA 12.4 驅動**（ASR 服務；無 GPU 也可跳過用 stub mode）
- API keys：`ANTHROPIC_API_KEY`（S-Agent）、`GOOGLE_API_KEY`（E/A/V-Agent）

## 1. Clone + 安裝

```bash
git clone https://github.com/bobyu89/CDSSproMAX.git ticdss
cd ticdss

# 後端依賴
cd apps/api && uv sync && cd ../..

# ASR 服務依賴（要 CUDA wheels）
cd apps/asr && uv sync && cd ../..

# 前端依賴（pnpm 會把 packages/shared-types 連起來）
pnpm install
```

## 2. 環境變數

```bash
cp .env.example .env
# 編輯 .env，填入：
#   ANTHROPIC_API_KEY=sk-ant-...
#   GOOGLE_API_KEY=...
#   JWT_SECRET=改成隨機字串
```

如果想跑 Langfuse trace，多填：
```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

## 3. 起 Postgres + Langfuse

```bash
docker compose up -d
# 等 30 秒，等 Postgres healthy
docker compose ps
```

連線確認：`psql postgresql://ticdss:change_me_locally@localhost:5433/ticdss -c "SELECT 1"`

## 4. 建表 + 灌資料

```bash
cd apps/api

# 建立 schema
uv run alembic upgrade head

# 灌 38 個案例（從 cdss-training 複製過來的）
uv run python ../../scripts/import_cases.py

# 建立示範使用者
uv run python ../../scripts/seed_users.py
# 輸出：
#   OK   P001 (student) — password: demo1234
#   OK   P002 (student) — password: demo1234
#   OK   T001 (teacher) — password: demo1234
#   OK   ADMIN001 (admin) — password: admin1234

# 灌 RAG 知識庫（16 個 LQQOPERA + PE 種子文件）
uv run python scripts/seed_bibliotheke.py

cd ../..
```

## 5. 啟動三個服務

開三個終端：

**終端 A — Backend (8001)**
```bash
cd apps/api
uv run uvicorn src.main:app --reload --port 8001
```

**終端 B — Frontend (3000)**
```bash
pnpm dev:web
# 或 cd apps/web && pnpm dev
```

**終端 C — ASR (8002)**
```bash
cd apps/asr
# 有 GPU：
uv run uvicorn src.main:app --reload --port 8002
# 沒 GPU：開 stub mode
ASR_STUB_MODE=true uv run uvicorn src.main:app --reload --port 8002
```

## 6. 登入 + 試跑

打開 `http://localhost:3000`，自動導向 `/login`。

| 帳號 | 密碼 | 角色 | 進入頁面 |
|---|---|---|---|
| P001 | demo1234 | 學員 | /home |
| P002 | demo1234 | 學員 | /home |
| T001 | demo1234 | 教師 | /home（可看其他人 session） |
| ADMIN001 | admin1234 | 管理員 | /admin |

### 學員流程
1. /home → 點「練習模式」
2. /practice → 選一個案例（如 CASE-01 急性胸痛）
3. 選擇應評估系統（心血管 + 呼吸）
4. LQQOPERA 問診：點 8 個維度 chip 或按住麥克風講話
5. 身體評估：勾項目
6. 鑑別診斷：寫 3 個 ranks
7. 系統觸發 DUAT pipeline → 8 個 LQQOPERA 維度評分

### OSCE 流程
1. /home → 點「OSCE 模式」
2. PreExamCard 說明 → 「我已了解，開始考試」
3. 3 站 × 14 分鐘輪轉（計時自動推進，無法暫停）
4. 全部完成 → OsceSummary 顯示三站總成績

## 7. 跑測試

```bash
# 後端單元測試（不打 LLM API）
cd apps/api
uv run pytest -v

# E2E live test（會打 Claude + Gemini，~$0.10/run）
ANTHROPIC_API_KEY=... GOOGLE_API_KEY=... uv run pytest -m live -v

# Ablation Study
cd ../../evaluation
uv sync
uv run python -m evaluation.run_ablation --dataset golden_sessions/example.jsonl --groups A,B,C
```

## 常見問題

### Postgres 連不上
- 確認 docker compose ps 顯示 `ticdss-postgres` 為 `healthy`
- 確認 `.env` 的 `DATABASE_URL` 用 `localhost:5433`（不是 5432，避免撞舊系統）

### ASR `/transcribe` 報 GPU 錯
- 用 `ASR_STUB_MODE=true` 跳過模型載入
- 或裝 CUDA 12.4 對應的 `torch` wheel

### Frontend 顯示 mock 資料而非真實 session
- 表示前端 `fetch` 後端失敗 — 檢查瀏覽器 DevTools Network tab
- 確認 `.env` 的 `NEXT_PUBLIC_API_URL=http://localhost:8001` 與後端 port 對得起來

### Live test 全部 skip
- 沒設 ANTHROPIC_API_KEY / GOOGLE_API_KEY，這是預期行為

## 進入論文里程碑

當你跑完 Wave 1 全流程，下一步是：
1. 收集 30~50 份人工標註的 LQQOPERA session 作為 Golden dataset
2. 跑 Ablation Study（Group A / B / C）算 ICC、Cohen's κ、MAE
3. 七位 NP 督導做 CVI 評定 Rubric 內容效度
4. n=20-30 學員做 SUS 使用性測試
5. 全部結果 → JMIR Medical Education Phase 1 投稿

詳見 `docs/architecture/` 與 `evaluation/README.md`。
