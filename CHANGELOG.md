# Changelog

All notable changes to TICDSS. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

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
