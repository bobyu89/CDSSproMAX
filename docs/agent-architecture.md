# DUAT Agent Architecture — Deep Dive

Companion document to `docs/architecture/duat-pipeline.md`. The pipeline doc defines the data flow; this doc explains each agent in depth, plus the Arbiter, the Bibliotheke (RAG), and a per-session cost model.

> Authoritative source for design constraints is the JMIR submission's Protocol §四. This document explains what is in code today; where they diverge, the Protocol wins and code should be updated.

---

## 1. The Five Agents

Per `CLAUDE.md` and `docs/architecture/duat-pipeline.md`, the DUAT stack is **O / E / S / A / M**. E, S, and A run per rubric item; O drives session state; M runs continuously across sessions.

### Per-item flow

```
                   E-Agent
                     │
              Evidence Bundle
                     │
            ┌────────┴────────┐
        S-Agent             A-Agent       (run in parallel — asyncio.gather)
            │                  │
            └────────┬─────────┘
                     │
            Consensus Arbiter (rule-based)
                     │
            duat_scores + audit_events
```

Source: `apps/api/src/agents/pipeline.py` (`DuatPipeline`).

---

### O-Agent — Orchestrator

- **Role**: session state machine. Owns `Session.phase` and per-phase time limits in exam mode.
- **Implementation**: pure FastAPI/Python logic — `apps/api/src/agents/o_agent.py`. Phases are an enum (`SCENARIO → INQUIRY → TRANSITION → EXAMINATION → DIAGNOSIS → REVIEW`); `next_phase()` is a deterministic lookup.
- **Inputs / outputs**: `OAgentInput` / `OAgentOutput` (Pydantic models in `o_agent.py`).
- **Model**: **none in Wave 1**. The Protocol allows a Claude call for exceptional routing, but Wave 1 keeps it rule-based for predictability.
- **Context budget**: N/A.
- **Failure modes**: a phase out of `_PHASE_ORDER` would raise `ValueError`; treated as a programming bug, not a runtime case.
- **Pipeline position**: top of the call tree — selects rubric items to score and hands each to the per-item pipeline.

### E-Agent — Evidence Extractor

- **Role**: the **sole RAG accessor** (CLAUDE.md §2: "E-Agent 唯一存取原則"). Produces an Evidence Bundle that S- and A-Agent consume as their entire factual context.
- **Implementation**: `apps/api/src/agents/e_agent.py` (`EAgent`). Calls `Bibliotheke.search()`, formats RAG hits as a reference block, asks Gemini for an evidence-bundle JSON.
- **Inputs / outputs**: `EAgentInput` (rubric item id + transcript + case context) → `EAgentOutput` (evidence segments + RAG hits + confidence). Bundle schema in `docs/architecture/duat-pipeline.md`.
- **Model**: Gemini 3.5 Flash (`E_AGENT_MODEL` env). Chosen for cheap, fast structured-JSON extraction at 1M context — RAG passages can be long.
- **Context budget**: 300–500 tokens (Protocol §四.(六)). Enforced informally by prompt design; one rubric item at a time.
- **Failure modes**:
  - **RAG miss / DB down** → `_retrieve()` logs a warning, returns `[]`. The agent still produces a bundle with model-reported confidence (graceful degradation, documented at the top of `e_agent.py`).
  - **Gemini JSON parse failure** → handled in `gemini_generate_json`; falls back to a zero-confidence empty bundle so downstream agents still run.
- **Pipeline position**: first per-item step; gates everything below.

### S-Agent — Scorer

- **Role**: assigns the 0–5 score with G-Eval CoT reasoning.
- **Implementation**: `apps/api/src/agents/s_agent.py` (`SAgent`).
- **Inputs / outputs**: `SAgentInput` (rubric item id + spec + Evidence Bundle) → `SAgentOutput` (`score: int 0..5`, `cot_reasoning`, `cited_evidence_ids`). **Never** receives raw transcript — only the bundle (Protocol §四.(六) Context Minimisation).
- **Model**: Claude Opus 4.7 (`S_AGENT_MODEL` env). Chosen for highest-quality clinical reasoning + faithful CoT.
- **Context budget**: 600–800 tokens.
- **Failure modes**: invalid / out-of-range score is clamped to 0..5 by `_clamp_score`. JSON parse failure surfaces as a score of 0 with empty CoT — visible in audit log and flagged downstream by low effective confidence.
- **Pipeline position**: parallel with A-Agent.

### A-Agent — Adversarial Reviewer

- **Role**: critique the evidence independently and emit an **advocate score** in [0, 1] (0 = full agreement, 1 = strong dissent). Compared to S-Agent only by the Arbiter — never sees the S-Agent output (Protocol §四.(三) independence requirement, enforced by `a_agent.py` keeping `s_score`/`s_cot` out of the prompt).
- **Implementation**: `apps/api/src/agents/a_agent.py` (`AAgent`).
- **Inputs / outputs**: `AAgentInput` → `AAgentOutput` with `advocate_report`, `advocate_score`, `challenged_points`.
- **Model**: Gemini 3.5 Flash (`A_AGENT_MODEL` env). Different family from S-Agent (Claude) on purpose — reduces correlated-error risk.
- **Context budget**: 400–600 tokens.
- **Failure modes**: `_clamp_unit` forces `advocate_score ∈ [0, 1]`. JSON parse failure → score 0.0, empty report. Note this biases the Arbiter toward "accept" — see `docs/runbook.md` §M-Agent for the override-rate safety net.
- **Pipeline position**: parallel with S-Agent.

### M-Agent — Drift Monitor

- **Role**: cross-session governance. Tracks override rate per rubric item; emits `mdrift.alert` when sustained > 30% with `total_scored ≥ 10`.
- **Implementation**: `apps/api/src/agents/m_agent.py`. Pure rule for Wave 1; Protocol allows occasional LLM call to summarise drift narratively, but that's deferred.
- **Inputs / outputs**: `MAgentInput` (counts) → `MAgentOutput` (`override_rate`, `alert`, `alert_reason`).
- **Model**: rule-based.
- **Context budget**: N/A — cross-session aggregate, not LLM context.
- **Failure modes**: `total_scored == 0` short-circuits to 0%. Counts pulled by the caller (typically a periodic job over `audit_events`); a stale read just delays an alert by one cycle.
- **Pipeline position**: outside the per-item flow — runs continuously / periodically.

---

## 2. Consensus Arbiter

Source: `apps/api/src/agents/arbiter.py`.

### Why rule-based, not an LLM

Per CLAUDE.md §2: "Consensus Arbiter 是規則型，不是 LLM — 三層決策必須是純函式、可單元測試、可稽核." The Arbiter is the audit-critical step where automatic scoring routes to human review. Replacing it with an LLM would re-introduce the very stochasticity the DUAT design is meant to constrain. Pure-function form means:

- Deterministic — same input always produces the same decision.
- Unit-testable — `tests/test_arbiter.py` covers the layer boundaries.
- Auditable — `thresholds_version` stamp on every decision lets us re-run historical evidence against new thresholds.

### Three-layer decision

| Layer | Trigger | Action | Confidence |
|---|---|---|---|
| 1 | `e_confidence ≥ 0.80` **and** `a_advocate_score < 0.30` | `accept` | high |
| 2 | `e_confidence ≥ 0.50` **and** `a_advocate_score < 0.50` | `flag` | medium |
| 3 | otherwise | `force_human` | low |

Constants live in `arbiter.py` (`E_CONF_HIGH`, `E_CONF_MEDIUM`, `A_ADVOCATE_LOW`, `A_ADVOCATE_MEDIUM`). `s_score` is recorded but not used to route (it's the *output* the Arbiter is gating, not an input to gating).

### Threshold sources & recalibration

- **Origin**: Protocol §四.(三) 表二. Starting values are conservative defaults pending Phase 1 Pilot data.
- **Recalibration trigger**: M-Agent override-rate alerts and / or completed Pilot's ICC analysis.
- **Procedure** (proposed — see runbook TODOs):
  1. Snapshot all `audit_events` over the calibration window.
  2. Sweep thresholds; minimise human-graded disagreement (maximise ICC vs human consensus) subject to a force-human budget.
  3. Bump `THRESHOLDS_VERSION` in `arbiter.py` (e.g. `v1.0` → `v1.1`).
  4. Re-run DUAT on the Golden dataset to confirm regression-free behaviour.

The `thresholds_version` field on every `ArbiterDecision` means historical evidence can be re-decided with new thresholds offline, without touching the live audit chain.

---

## 3. Bibliotheke — the RAG Layer

### Why only E-Agent has access

The "E-Agent 唯一存取原則" exists so:

- **S-Agent isolation**: the scorer reasons over a fixed, citable Evidence Bundle. If S could fetch its own RAG, the audit log could not faithfully reproduce its inputs.
- **A-Agent isolation**: the adversarial reviewer must challenge **the same evidence** S saw — otherwise dissent is noise, not signal.
- **Single point of citation**: every `rag_hits[]` entry in the audit log is provably the only RAG content that touched the decision.

### Two-stage retrieval

Implemented in `apps/api/src/rag/bibliotheke.py`:

1. **Dense retrieval** — query embedded with BAAI/bge; pgvector ANN search over `bibliotheke_chunks`. Returns top-K candidates (default K ≈ 20–50).
2. **Cross-encoder rerank** — candidates re-scored with a cross-encoder reranker. Returns top-`top_k_final` (default 5).

### Confidence derivation

`confidence_from_hits()` (in `rag/bibliotheke.py`) blends per-hit `cosine_similarity` and `rerank_score` into a single [0, 1] confidence. When the search returns **no hits**, `EAgent.run()` falls back to the model's self-reported confidence — preserving graceful degradation while making the lack of RAG support visible in the audit log (empty `rag_hits[]`).

---

## 4. Cost Analysis (per session)

> Pricing is volatile. Numbers below are **ranges based on Anthropic / Google list pricing as of late 2025**; substitute current pricing before quoting to stakeholders.

### Per-call breakdown

A full LQQOPERA scoring round = 8 dimensions × {E + S + A} = 24 LLM calls.

| Agent | Model | Approx. in / out tokens | Per-call cost (USD, ballpark) |
|---|---|---|---|
| E | Gemini 3.5 Flash | ~1 500 in / ~400 out | $0.001–0.003 |
| S | Claude Opus 4.7 | ~1 200 in / ~600 out | $0.04–0.08 |
| A | Gemini 3.5 Flash | ~1 200 in / ~400 out | $0.001–0.003 |

**Per LQQOPERA dimension**: roughly $0.04–0.09 (S-Agent dominates).

**Per session (8 dimensions)**: roughly **$0.30 – $0.75**.

**Add PE rubric (when Vision/Wave 1.5 lands)** — similar order of magnitude per PE item; expect total session cost to roughly double.

### Optimisation levers

1. **Anthropic prompt caching** for the S-Agent system prompt + rubric spec — these are stable across rubric items in a session. Realistic ~30–50% S-Agent input-cost reduction.
2. **Batching** — Gemini supports batch mode at lower per-token pricing for non-realtime work. The E/A Agents (Gemini) for completed sessions could run via batch; not applicable to live practice flow.
3. **Skip A-Agent when E-confidence is very high** — Arbiter Layer 1 already accepts when `e_confidence ≥ 0.80` regardless of A. A short-circuit could skip the A call in those cases (save ~10–15% per session), at the cost of weakening the independent-review audit story. **Not recommended for Wave 1** — preserve the full audit chain until Pilot data justifies the change.
4. **Smaller S-Agent on low-stakes practice mode** — switch `S_AGENT_MODEL` to a lighter Claude tier for practice, keep Opus for exam mode. Requires Protocol amendment (model version is part of the audit record).

---

## 5. Cross-references

- Pipeline diagram & Arbiter pseudocode: `docs/architecture/duat-pipeline.md`
- Rubric JSON schema: `docs/architecture/rubric-schema.md`
- Audit event schema: `docs/architecture/audit-log-spec.md`
- Operational playbook: `docs/runbook.md`
- Constraints / non-negotiables: `CLAUDE.md`
