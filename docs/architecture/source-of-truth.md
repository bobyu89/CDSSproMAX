> ⚠️ **DEPRECATED (2026-05-29).** Architecture authority moved to
> `docs/builder-spec/` (the ticdss-builder sub-agent specs + `core.md`
> contract). This file is kept only for the research invariants it records
> (mandatory audit JSONL, human accountability, rule-based Arbiter,
> cross-vendor adversarial S/A) — those now live as the **DUAT Verification
> Tier**, an additive module on top of the builder's two-tier design.
> When this file disagrees with `docs/builder-spec/`, the builder wins.

# TICDSS Source of Truth (DEPRECATED — see docs/builder-spec/)

Authoritative engineering definition for the TICDSS repo. The Chinese
translation (`source-of-truth.zh-TW.md`) is a reading aid only — if it
disagrees with this file, this file wins.

TICDSS is an auditable OSCE assessment system for Taiwan nurse practitioners,
covering LQQOPERA history-taking, PE physical examination, teacher review,
and reproducible audit logs. It is not a chatbot. The research core is DUAT
(Distributed Unified Assessment Tribunal). This repo is independent from
`../cdss-training/` — no shared DB, ports, or runtime.

## Authority Order

When sources disagree:

1. This file
2. `AGENTS.md` / `CLAUDE.md`
3. Other `docs/architecture/*.md`
4. Code on the active branch (treat code↔spec disagreement as drift — decide,
   don't silently "fix" one side)
5. Protocol manuscript drafts
6. Technical proposal drafts
7. README / changelog
8. `source-of-truth.zh-TW.md` (translation)

## Canonical Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 App Router + TypeScript, pnpm, Zustand |
| Backend | FastAPI + Pydantic v2, SQLAlchemy 2.x async, uv |
| Database | PostgreSQL 17 + pgvector (not ChromaDB) |
| ASR | Breeze-ASR-25 sidecar (HTTP, port 8002) — not Deepgram, not browser STT |
| Observability | JSONL audit logs (mandatory) + optional Langfuse |
| Tests | pytest + Playwright |

Ports: Web 3000, API 8001, ASR 8002, Postgres 5433, Langfuse 3001.

## Canonical Models

| Agent | Model | Notes |
|---|---|---|
| O-Agent | Rule-based state machine | LLM-assisted repair only for exceptional recovery |
| E-Agent | `gemini-3.5-flash` | Sole RAG accessor |
| S-Agent | `claude-opus-4-7` | Anthropic — cross-vendor with A-Agent is deliberate |
| A-Agent | `gemini-3.5-flash` | Must reach independent verdict, not echo S-Agent |
| M-Agent | Rules + statistical monitoring | Optional LLM summary later |
| V-Agent | `gemini-3.5-flash` multimodal | Vision path |

Changing any model is a protocol change: update this table, `.env.example`,
prompts, audit-log expectations, and the manuscript. Older drafts mention
Gemini 3.1 Pro / Deepgram / ElevenLabs / ChromaDB / Stream Vision Agents —
those are draft terms, not canonical.

## DUAT

### Non-negotiable principles

1. **E-Agent is the only RAG accessor.** S/A/M never query Bibliotheke or
   pgvector — they receive facts only through the Evidence Bundle.
2. **Arbiter is rule-based.** A pure, testable function — not an LLM call.
3. **Context is item-scoped.** One agent call = one rubric item. Do not pass
   the whole transcript to a scoring agent.
4. **Audit JSONL is mandatory.** Each score path records prompt hash, model
   version, rubric item id, and replay payload.
5. **Human accountability is final.** DUAT outputs recommendations and flags;
   teachers accept/modify/reject.

### Agent contracts

| Agent | Inputs | Outputs |
|---|---|---|
| O-Agent | Session state, phase, mode | Next phase, routing, time limits |
| E-Agent | Rubric item id, scoped transcript, case context | Evidence Bundle JSON |
| S-Agent | Rubric item + Evidence Bundle | 0–5 score, reasoning, cited evidence ids |
| A-Agent | Rubric item + Evidence Bundle | Advocate score, challenged points |
| M-Agent | Historical score / override stats | Override-rate alerts |

Do *not* use the technical proposal's older
observation/evaluation/synthesis/analysis/memory mapping — that's a different
concept.

### Arbiter (v1 thresholds)

Actions: `accept` / `flag` / `force_human`.

| `e_confidence` | `a_advocate_score` | Action |
|---|---|---|
| ≥ 0.80 | < 0.30 | `accept` (high) |
| ≥ 0.50 | < 0.50 | `flag` (medium) |
| else | else | `force_human` (low) |

Protocol language "High Confidence / Review Needed / Uncertainty Flag" maps
to `accept` / `flag` / `force_human`.

## Wave Scope

Before adding a feature, label its wave. Later-wave work is paused unless
the user explicitly changes scope. Out-of-order delivery is allowed but must
be recorded here (see Wave 4).

### Wave 1 — DUAT LQQOPERA *(shipped)*

Vertical slice: auth → case/session/transcript → rubric → E/S/A → Arbiter →
`duat_scores` → teacher review → audit JSONL. Includes pgvector Bibliotheke
RAG (E-only), basic admin dashboard, ablation evaluation scripts.

Out of scope: avatar, Dialog Agent, Fusion Engine, HRV-into-score, vision-
into-LQQOPERA, handout expansion.

Gate: API boots on 8001, migrations clean, `/health` OK, session can be
created → scored → reviewed → audit replayed; agent/arbiter/audit/rubric/
router pytest passes.

### Wave 1.5 + 1.7 — PE Vision and Fusion *(shipped)*

Two-layer PE assessment, fused into a single auditable score.

| Layer | Does | Must not do |
|---|---|---|
| ArUco (OpenCV `DICT_4X4_50`) | Body region / position | Judge technique |
| V-Agent (Gemini multimodal) | Action, technique, duration | Override deterministic position |
| `pe_fusion.py` | Combine → one PE row in `duat_scores` | Live elsewhere |

Canonical rules:

- 15 anatomy markers in `apps/api/src/vision/anatomy_map.py`.
- Touch = marker occluded for a **continuous 1.5 s – 8.0 s** gap. The upper
  bound is a re-arm window — without it, a marker that vanishes once is
  forever flagged.
- Fusion v1: `position 0.80 + technique 0.20 + duration bonus when rubric
  minimum met`. Single PE row in `duat_scores`.
- Keyframes → S3-compatible storage (MinIO in dev) via `services/storage.py`.
  `NoopStorage` is the fallback — endpoints must work without MinIO.
- Re-score endpoint fetches keyframes from storage; client never re-uploads.
- 90-day ILM lifecycle on the `keyframes` bucket.

Hardware baseline: standard webcam (≥ 720p, 15 fps), printed markers ≥ 5 cm
on matte paper, single fixed angle. `/admin/calibration` must show all 15
markers stable ≥ 3 s before an OSCE session is allowed.

Gate: `/vision/health` reachable; anatomy map returns 15; detector degrades
to empty (never raises) without OpenCV; PE observations persist; fusion
deterministic for fixed inputs; re-score reuses stored keyframes; tests
cover both occlusion bounds, fusion, and storage fallback.

### Wave 2 — Dialog Agent and Avatar *(not started)*

Begins only after Wave 1 / 1.5 / 1.7 gates hold. Scope:

- Dialog Agent for standardized-patient responses (practice = variable,
  exam = standardized).
- Avatar / TTS / lip sync.
- Prosody extraction for later Fusion.
- **Candidate addition here, not in Wave 1.5:** MediaPipe Tasks Vision
  (Hands + Pose Landmarker) as a deterministic gesture-feature input to
  V-Agent's technique judgment. ArUco remains the position source of truth.

Deepgram, ElevenLabs, external avatar services are proposal-era — adding
any is a protocol change.

### Wave 3 — HRV and Fusion Engine *(HRV ingest shipped, Fusion not started)*

HRV today: Web Bluetooth Polar H10 ingest → `physio_samples`; SDNN, RMSSD,
pNN50, mean HR; `state_proxy` as non-diagnostic training signal.

**HRV is monitoring only. It must not enter S/A context until Fusion is
explicitly designed.**

Fusion Engine future scope: combine HRV + prosody + vision behavior into
`LearnerState`; decide whether and how it enters scoring context; exam-mode
behavior stays conservative and auditable.

Gate (when revisited): HRV summaries work; raw RR stays DB-only unless
exported; Fusion rules are documented and tested before influencing scoring.

### Wave 4 — Personal Handout *(minimal slice shipped out-of-order)*

Sequenced ahead of Wave 2/3 by explicit user request to validate the
end-to-end debrief UX on top of Wave 1 scores. v1 feature-complete;
expansion (richer mindmap, multi-session trends) paused until Wave 2/3.

Shipped: `apps/api/src/handout/` (schema, aggregator, LLM generators);
`apps/web/app/handout/[sessionId]/` page with 10 cards (radar, confidence
calibration, study notes, mindmap, HRV curve, flow prediction, discussion
prompts, spaced-repetition, self-assessment, annotated transcript). Cached
on `sessions.generated_handout_json`; invalidated on regenerate or
self-assessment submit.

Rules:

- Handout never feeds DUAT scoring. HRV / self-assessment / confidence-
  calibration signals are read-only on this path.
- Generation runs only after the scoring record is complete.
- AI-generated reflection must be visually distinct from teacher-confirmed
  assessment.
- Annotated transcript matches turns to `e_evidence_json.evidence_segments`
  by substring fuzzy match — **UX-grade, not evidence-grade**. Do not
  promote these matches into scoring inputs.

## Data Ownership

| Data | Source of truth |
|---|---|
| Participants | `participants` |
| Cases | `cases` (seeded from `data/cases`) |
| Rubrics | `data/rubrics` + `rubrics` table when imported |
| Transcripts | `transcripts` |
| DUAT scores | `duat_scores` |
| Audit | JSONL logs; `audit_events` is a query mirror |
| RAG chunks | `bibliotheke_chunks` (pgvector) |
| HRV | `physio_samples` |
| PE observations | `pe_observations` |

Every migration must have a matching ORM model, and vice versa. No
half-wired schema.

## Development Rule

Per-commit drift checks for any commit touching a canonical layer:

- `apps/api/src/config.py` models match the Canonical Models table.
- `apps/api/src/agents/arbiter.py` constants match the Arbiter thresholds.
- `apps/api/src/vision/anatomy_map.py` has exactly 15 markers.
- Every Alembic migration has a matching ORM model.

Every completed step must be verifiable by at least one of: a passing test,
a successful API request, a clean migration, a reproducible script, or a
documented manual verification path.
