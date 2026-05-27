# TICDSS Operations Runbook

Day-to-day operations, health checks, and incident response for TICDSS (Wave 1, local-dev / single-host deployment).

> Audience: developer-operators running TICDSS on a research workstation. Production / cluster deployment is out of Wave 1 scope.

---

## 1. System Overview

TICDSS (Technology-Integrated Clinical Decision Support System) is a multi-agent OSCE assessment platform for Taiwan NP (Nurse Practitioner) clinical-reasoning training. A student conducts an LQQOPERA history + PE on a simulated case; the **DUAT** (Distributed Unified Assessment Tribunal) — five cooperating agents (O / E / S / A / M) — extracts evidence, scores each rubric item via independent reviewers, and routes results through a rule-based Consensus Arbiter for accept / flag / human-review.

### Component map

| Service | Port | Process | Purpose |
|---|---|---|---|
| Web | **3000** | Next.js 15 (`pnpm dev:web`) | Student / teacher / admin UI |
| API | **8001** | FastAPI (`uvicorn src.main:app`) | DUAT orchestration, RAG, auth, sessions |
| ASR | **8002** | FastAPI (Breeze-ASR-25, GPU) | zh-TW + en code-switched transcription |
| Postgres | **5433** | Docker (`ticdss-postgres`) | Sessions, users, audit index, pgvector |
| Langfuse | **3001** | Docker | LLM trace + span observability |

Ports are deliberately offset from `../cdss-training/` (old system on 8000 / 5432) — both stacks can run on one host.

---

## 2. Service Health Checks

### Web (3000)
```bash
curl -sf http://localhost:3000/login >/dev/null && echo OK || echo DOWN
```
If down: check the `pnpm dev:web` terminal; restart with `pnpm dev:web`. Build errors usually mean stale `packages/shared-types` — run `pnpm install` from the repo root.

### API (8001)
```bash
curl -sf http://localhost:8001/healthz
# expect: {"status":"ok"}
```
If down: tail the uvicorn terminal. Most common cause is Postgres unavailability (see §6). Restart:
```bash
cd apps/api && uv run uvicorn src.main:app --reload --port 8001
```

### ASR (8002)
```bash
curl -sf http://localhost:8002/healthz
```
If down or CUDA OOM: fall back to stub mode:
```bash
ASR_STUB_MODE=true uv run uvicorn src.main:app --reload --port 8002
```

### Postgres + Langfuse (Docker)
```bash
docker compose ps
# both ticdss-postgres and langfuse should be "healthy"

docker compose logs --tail=100 postgres
docker compose logs --tail=100 langfuse
```
Restart a single service: `docker compose restart postgres`.
Full reset (destroys data): `docker compose down -v && docker compose up -d`.

---

## 3. Common Operations

### Add a new case

1. Drop the case file under `data/cases/<case_id>.json` (or `.md` per existing convention).
2. Re-run the importer:
   ```bash
   cd apps/api
   uv run python ../../scripts/import_cases.py
   ```
3. Verify in DB:
   ```bash
   psql postgresql://ticdss:change_me_locally@localhost:5433/ticdss \
     -c "SELECT case_id, title FROM cases ORDER BY created_at DESC LIMIT 5;"
   ```

### Add a new participant

**Option A — admin UI:** log in as `ADMIN001`, go to `/admin`, click "Add participant".

**Option B — seed script:** append to `scripts/seed_users.py`'s recipe list and re-run:
```bash
cd apps/api
uv run python ../../scripts/seed_users.py
```
The script is idempotent — existing rows are not duplicated.

### Regenerate the RAG knowledge base (Bibliotheke)

After editing any file under `data/bibliotheke_seeds/*.md`:
```bash
cd apps/api
uv run python scripts/seed_bibliotheke.py
```
This re-embeds with BAAI/bge and refreshes pgvector. The seed script truncates and rewrites the `bibliotheke_chunks` table — no manual cleanup needed. Bibliotheke is therefore **always regeneratable** from `data/bibliotheke_seeds/` and does not need a backup.

### Re-run DUAT on an existing session

```bash
curl -X POST http://localhost:8001/sessions/{session_id}/duat/score-all-lqqopera \
  -H "Authorization: Bearer <jwt>"
```
Idempotent for the audit log: each retry writes a new event chain with a fresh `event_id` but reuses `session_id` and `rubric_item_id`. Useful after rubric or prompt changes — the older audit chain stays for comparison.

### Rotate JWT secret

1. Stop the API.
2. Edit `.env`: set a new `JWT_SECRET` (any high-entropy string).
3. Restart the API.
4. **All existing tokens are invalidated**; every user must re-login. Notify users beforehand.

---

## 4. Monitoring

### Audit log

- Location on disk: `audit_logs/{session_id}.jsonl` (one file per session, one JSON event per line).
- Schema: see `docs/architecture/audit-log-spec.md`.
- Event types of interest: `duat.score_computed`, `grader.action`, `mdrift.alert`.

Quick tail:
```bash
tail -f audit_logs/$(ls -t audit_logs/ | head -1)
```

### DB queries

Recent sessions:
```sql
SELECT id, participant_id, case_id, mode, status, created_at
FROM sessions
ORDER BY created_at DESC
LIMIT 20;
```

Per-rubric override rate (input to M-Agent alerting):
```sql
SELECT rubric_item_id,
       COUNT(*) FILTER (WHERE grader_action IN ('modify','reject'))::float
       / NULLIF(COUNT(*), 0) AS override_rate,
       COUNT(*) AS n
FROM audit_events
WHERE event_type = 'grader.action'
GROUP BY rubric_item_id
ORDER BY override_rate DESC;
```

### Langfuse trace lookup

Each session emits Langfuse spans keyed on `session_id`. In the Langfuse UI (`http://localhost:3001`), search → metadata → `session_id=<uuid>`. Per-agent spans are named `e_agent.run`, `s_agent.run`, `a_agent.run`, `arbiter.decide`.

### M-Agent override-rate alert

M-Agent fires `mdrift.alert` when, for a rubric item with `total_scored ≥ 10`, the override rate sustains `> 30%`. Threshold lives in `apps/api/src/agents/m_agent.py::OVERRIDE_RATE_ALERT_THRESHOLD`. Treat sustained alerts as a signal to:

1. Pause automated scoring for that item.
2. Re-examine the rubric criteria + S-Agent prompt.
3. Consider re-calibrating Arbiter thresholds (see `docs/agent-architecture.md` §Arbiter).

---

## 5. Incident Response

### Backend won't start

| Symptom | Likely cause | Fix |
|---|---|---|
| `psycopg.OperationalError: connection refused` | Postgres not up | `docker compose ps` → restart `postgres` |
| `sqlalchemy.exc.ProgrammingError: relation ... does not exist` | Migrations not applied | `cd apps/api && uv run alembic upgrade head` |
| `pydantic_settings ValidationError` | Missing env var (`DATABASE_URL`, `JWT_SECRET`) | Check `.env` against `.env.example` |
| `ImportError: cannot import name ...` | Stale virtualenv after dep change | `cd apps/api && uv sync` |

### LLM API errors

- **Rate limit (HTTP 429)**: SDK calls in `apps/api/src/services/llm_clients.py` rely on the providers' default retry. Sustained 429s = lower concurrency: the DUAT pipeline scores items sequentially per session, but parallel sessions multiply load. Reduce concurrent sessions or upgrade the provider tier.
- **401 Unauthorized**: invalid / revoked `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY`. Rotate the key in `.env`; restart API.
- **Budget exhausted**: API returns a billing error. Top up the provider account, or switch the session to manual-grading mode (skip DUAT) by setting `DUAT_ENABLED=false` and restarting.
- **Bibliotheke search failure**: E-Agent degrades gracefully — emits an Evidence Bundle with empty `rag_hits[]` and uses the model-reported confidence. Inspect `audit_events.evidence_bundle.rag_hits` for affected sessions.

### ASR service crash

- **CUDA OOM** at startup: another process holds VRAM. Check with `nvidia-smi`; kill the offender, or restart in stub mode (`ASR_STUB_MODE=true`).
- **Mid-session crash**: clients automatically receive a 5xx from `/transcribe`. The web UI falls back to a "請改用文字輸入" path. Restart the ASR service.

---

## 6. Backup

### Postgres
```bash
docker exec ticdss-postgres pg_dump -U ticdss -d ticdss --format=custom \
  > backups/ticdss-$(date +%Y%m%d).dump
```
Schedule daily (cron / Task Scheduler). Restore with `pg_restore -U ticdss -d ticdss --clean backups/ticdss-YYYYMMDD.dump`.

### Audit logs
```bash
rsync -av audit_logs/ /path/to/backup/audit_logs/
```
Append-only JSONL — `rsync` is sufficient. Daily snapshot retains forensic value even if the DB is rebuilt.

### Bibliotheke
**No backup needed.** Re-derive any time from `data/bibliotheke_seeds/*.md` via `scripts/seed_bibliotheke.py`. Treat the embedded chunks as a build artifact.

---

## 7. Open TODOs

The following items need a human owner / decision before they can be documented concretely:

- [ ] **Production deployment story** — Wave 1 is single-host dev. Operations under multi-user load (RBAC, HA Postgres, ASR autoscaling) are not designed.
- [ ] **Exact LLM pricing** to plug into the cost section of `agent-architecture.md` — current numbers are ranges, not contractual.
- [ ] **Arbiter threshold recalibration procedure** — Protocol commits to recalibration after Phase 1 Pilot but the exact algorithm (ROC sweep? grid search vs. override rate?) is unspecified.
- [ ] **Audit-log retention policy** — IRB protocol says "duration of study"; concrete purge / archive schedule TBD.
- [ ] **Disaster-recovery RPO/RTO targets** — not yet set; current backup cadence is "best-effort daily".
- [ ] **On-call rotation / escalation contacts** — single-developer project at present.
