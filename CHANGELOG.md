# Changelog

All notable changes to TICDSS. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [0.3.0-hrv-skeleton] — 2026-05-28

### Added — Wave 3 HRV skeleton

第一個生理訊號 vertical slice 落地。骨架完整覆蓋裝置接入 → 儲存 → 計算 → UI；
Fusion Engine 整合到 DUAT 評分留給後續 Wave 3 工作。

#### Backend
- `apps/api/src/physio/`：純 stdlib 時間域 HRV 計算（SDNN / RMSSD / pNN50 / mean HR）
  + `state_proxy_from_hrv` 將指標映射為 `flow` / `anxious` / `low_engagement` /
  `ambiguous`（Shaffer & Ginsberg 2017 健康成人短時段參考）。
- `apps/api/src/routers/physio.py`：4 個端點
  (`POST /physio/sessions/{sid}/samples`, `GET .../hrv`, `GET .../timeseries`,
  admin-only `DELETE .../samples`)，全部接 audit logger。
- `apps/api/src/db/models.py` + alembic `0003_physio`：新增 `physio_samples` 表
  （`BigInteger timestamp_ms`、quality_flag enum、`(session_id, timestamp_ms)` 索引）。
- `apps/api/src/audit/schema.py`：3 個新事件
  (`physio.samples_ingested`, `physio.hrv_computed`, `physio.device_connected`)。
- 在 `main.py` 註冊 physio router。
- Tests: `test_hrv.py` — 對手算值校驗 SDNN/RMSSD/pNN50；變異 vs 穩態 sanity；
  state_proxy 四種分類；空輸入 raise、gap 樣本過濾。

#### Frontend
- `apps/web/lib/bluetoothHrv.ts`：Polar H10 Web Bluetooth client，解析
  0x2A37 GATT notification（含 8/16-bit HR flag + 1/1024 s RR 單位轉 ms）。
- `apps/web/lib/physio.ts`：API client（mock fallback 與 vision.ts 一致）。
- `apps/web/components/physio/HRVMonitor.tsx`：3 態 UI（disconnected /
  connecting / connected）、4 大統計磚（HR / SDNN / RMSSD / 狀態徽章）、
  inline SVG sparkline（最近 60 RR），示範模式（Box-Muller 合成 RR
  μ=800ms σ=30ms）讓無 BLE 裝置也能跑流程。
- `apps/web/components/physio/PhysioStateBadge.tsx`：4 + no_data 顏色映射。
- `packages/shared-types/src/physio.ts`：PhysioSample / TimeDomainSummary /
  PhysioStateProxy / HrvWindowResult / IngestSampleInput 共用型別。
- 整合：`StepPE.tsx` 在 vision toggle 上方常駐 `<HRVMonitor compact />`。

#### Docs
- `docs/architecture/hrv-pipeline.md`：BLE 流程圖、儲存 schema、指標公式 +
  生理意義、state_proxy 閾值來源、隱私原則、Fusion Engine TODO。

#### 注意
- HRV **尚未**參與 DUAT 評分（S-Agent context 不變）。Fusion Engine 整合是
  Wave 3 下一步工作 — 詳見 `docs/architecture/hrv-pipeline.md` 末段 TODO。
- 不新增任何 Python / npm 依賴。

## [0.2.0-skeleton] — 2026-05-28

### Added — Wave 1.5 vision skeleton

Frame for the visual evaluation layer landed; implementations are stubs but
the full API + UI contract is in place so subsequent work can fill in
without architecture changes.

#### Backend
- `apps/api/src/vision/`: anatomy_map (15 ArUco IDs → anatomical regions),
  marker_detector (lazy OpenCV DICT_4X4_50 with stub fallback), frame_capture
  helpers, occlusion-tracking utility (1.5s threshold → "region touched").
- `apps/api/src/agents/v_agent.py`: V-Agent (Gemini 3.5 Flash Vision) shell —
  schemas + prompt + stub return; multimodal SDK wiring marked as next step.
- `apps/api/src/routers/vision.py`: 5 endpoints (`/vision/anatomy-map`,
  `/vision/markers/detect`, `/vision/sessions/{id}/track`,
  `/vision/sessions/{id}/v-agent`, `/vision/health`) + admin tracker reset.
- `apps/api/src/db/models.py` + alembic `0002_vision`: new `pe_observations`
  table to persist per-rubric-item V-Agent verdicts and keyframe paths.
- `apps/api/src/audit/schema.py`: 3 new vision audit events
  (`vision.frame_detected`, `vision.region_touched`, `vision.v_agent_scored`).
- `apps/api/pyproject.toml`: optional `[vision]` extra (opencv-python +
  numpy + reportlab) so the base install stays light.
- Tests: `test_vision_anatomy_map.py` (invariants), `test_vision_marker_detector.py`
  (occlusion tracker semantics + cv2-missing graceful degrade),
  `test_v_agent.py` (stub correctness on intent match / duration / hash).

#### Frontend
- `apps/web/lib/vision.ts`: typed client for all vision endpoints with
  mock fallback for offline dev.
- `apps/web/components/vision/CameraCapture.tsx`: getUserMedia preview +
  500ms polling detection loop + STUB/OPENCV backend badge.
- `apps/web/components/vision/MarkerOverlay.tsx`: SVG marker boxes + labels.
- `apps/web/components/vision/TouchedRegionsPanel.tsx`: live state of all 15
  markers with "目標" highlight for the expected region.
- `packages/shared-types/src/vision.ts`: AnatomyRegion / MarkerDetection /
  FrameDetectResult / TrackSampleResult / VAgentResult shared types.
- `packages/shared-prompts/v_agent.txt`: V-Agent system prompt (strict JSON
  schema, position-vs-technique separation).

#### Tooling & docs
- `scripts/generate_aruco_pdf.py`: produces an A4 PDF with all 15 markers
  (5×5 cm each) + 繁中 labels + print hints, ready to laminate.
- `data/aruco/README.md`: marker ↔ region map + printing & calibration
  walkthrough.
- `docs/architecture/vision-pipeline.md`: full design rationale for the
  two-layer (ArUco + V-Agent) split, threshold choices, DUAT integration plan.

### Not yet (Wave 1.6)
- V-Agent real multimodal call (google-genai inline image bytes)
- DUAT pipeline integration: V-Agent result fan-in to Consensus Arbiter
  alongside S/A for PE rubric items
- StepPE wiring: trigger V-Agent on Intent-First voice declaration
- Calibration page under /admin for verifying all 15 markers detect

## [0.1.0] — 2026-05-27

First Wave 1 milestone — end-to-end vertical slice from login through DUAT-scored session, with the evaluation harness and RAG online.

### Added — Wave 1 (closed)

#### Backend (`apps/api/`)
- DUAT 5-agent pipeline (`src/agents/`): **E-Agent** (Gemini 3.5 Flash, sole RAG accessor), **S-Agent** (Claude Opus 4.7, G-Eval CoT scorer), **A-Agent** (Gemini 3.5 Flash, independent adversarial reviewer), **O-Agent** (rule-based session state machine), **M-Agent** (rule-based drift monitor with override-rate alerting at the 30% threshold).
- `DuatPipeline` orchestrator in `src/agents/pipeline.py` — runs S-Agent and A-Agent in parallel via `asyncio.gather` over each Evidence Bundle.
- Rule-based **Consensus Arbiter** (`src/agents/arbiter.py`) with the three-layer accept / flag / force_human decision and a versioned threshold stamp for auditable recalibration.
- **RAG layer (Bibliotheke)**: pgvector dense retrieval with `BAAI/bge` embeddings + CrossEncoder rerank; confidence derived from blended cosine + rerank scores; graceful degradation when DB is unavailable.
- **LQQOPERA + PE rubric loaders** with JSON schemas (`docs/architecture/rubric-schema.md`).
- Endpoints: auth (login / JWT), sessions, transcripts, DUAT scoring (`/sessions/{id}/duat/score-all-lqqopera`), admin.
- **Audit log** writer (JSONL per session, indexed in `audit_events` table) — full event chain: `session.started → transcript.appended → duat.e_extracted → duat.s_scored → duat.a_reviewed → duat.arbiter_decided → duat.score_computed → grader.action`, plus `mdrift.alert`.
- **Langfuse** tracing integration — per-agent spans keyed on `session_id`.
- Alembic migrations for the full Wave 1 schema (users, sessions, cases, transcripts, duat_scores, audit_events, bibliotheke_chunks).

#### Frontend (`apps/web/`)
- Next.js 15 App Router with warm-beige palette + Manrope typography.
- `/login` — participant code + password.
- `/home` — mode selection (practice / OSCE).
- `/practice` — 6-step flow (case pick → system selection → LQQOPERA inquiry → PE → differential → review).
- `/osce` — 3-station timed exam, 14 min/station, auto-advance, PreExamCard + OsceSummary.
- `/history` — session list and detail.
- `/admin` — role-gated participant management.
- **ASR recording UI** — push-to-talk + MediaRecorder client, POSTing to ASR service.
- Zustand stores for session / UI state.

#### Data (`data/`)
- 38 OSCE cases ported from the legacy `cdss-training` repo.
- 16 LQQOPERA + PE knowledge-base seeds under `data/bibliotheke_seeds/` (regenerable via `scripts/seed_bibliotheke.py`).
- LQQOPERA rubric JSON: 8 dimensions × levels 0–5 with evidence anchors.
- PE rubric JSON with `expected_action` and `min_duration_seconds` hooks for Wave 1.5 Vision Agent.

#### ASR (`apps/asr/`)
- FastAPI service for MediaTek Breeze-ASR-25 (zh-TW + en code-switched), local-GPU only — no audio leaves the host.
- `ASR_STUB_MODE` for GPU-less development environments.

#### Evaluation (`evaluation/`)
- Ablation Study harness: Group A (full DUAT) / B (no A-Agent) / C (no RAG) runners.
- Metric pipeline: ICC, Cohen's κ, MAE against the Golden human-annotated dataset.
- Example Golden session JSONL fixture.

#### Tests
- Backend `pytest` suite, 50+ unit tests across agents, arbiter, RAG, routers.
- E2E **live tests** opt-in via `pytest -m live` — exercise real Claude + Gemini calls end-to-end (skipped without API keys).

#### Documentation
- `README.md`, `CLAUDE.md` (working constraints), `QUICKSTART.md`.
- `docs/runbook.md` — operational playbook.
- `docs/agent-architecture.md` — DUAT deep dive + cost model.
- `docs/architecture/duat-pipeline.md`, `docs/architecture/rubric-schema.md`, `docs/architecture/audit-log-spec.md`.

### Infrastructure
- `docker-compose.yml` for Postgres 17 + pgvector (port **5433**) and Langfuse (port **3001**).
- pnpm workspace + `packages/shared-types` and `packages/shared-prompts`.
- `uv`-managed Python environments for `apps/api` and `apps/asr`.

### Constraints honoured
- Legacy `../cdss-training/` repo untouched — runs alongside on disjoint ports / DB.
- All UI text in 繁體中文.
- IRB-friendly: ASR runs locally (Breeze-ASR-25); audit logs are append-only JSONL with full prompt-hash + model-version provenance.
- E-Agent is the sole RAG accessor — S- and A-Agent receive only the Evidence Bundle, never the raw transcript or RAG hits directly.
- Consensus Arbiter remains a pure rule-based function — never an LLM call.

### Notable commits in this release
- `f0cca6d` feat(ui): rebuild frontend flow to match cdss-training UX
- `310502e` feat: Wave 1 finale — RAG seeds, live E2E tests, ASR recording UI
- `82a8e8d` feat: Wave 1 core — DUAT pipeline live, RAG, frontend, evaluation, API routers
- `e3fcc66` chore: initial Wave 1 skeleton (Steps 1-6)

### Not yet shipped (planned)
- **Wave 1.5** — Vision Agent (ArUco + Gemini 3.5 Flash Vision) for PE action detection.
- **Wave 2** — Dialog Agent + Avatar + Case Authoring UI.
- **Wave 3** — Fusion Engine (HRV + facial-expression cues).
