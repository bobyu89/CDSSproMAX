"""E2E live LLM tests — hits real Anthropic + Google APIs.

These are **opt-in only** and require:
  - ANTHROPIC_API_KEY (for S-Agent)
  - GOOGLE_API_KEY (for E-Agent and A-Agent)

Run with::

    cd apps/api
    uv run pytest -m live -v

Or just one test::

    uv run pytest -m live -k test_e_agent_extracts_location -v

The tests use a fixed chest-pain scenario to exercise the LQQOPERA Location
dimension. We assert structural correctness (JSON parses, required fields
present, non-trivial output) rather than exact text — LLM responses vary
across calls.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from src.agents.a_agent import AAgent, AAgentInput
from src.agents.arbiter import arbitrate
from src.agents.e_agent import EAgent, EAgentInput
from src.agents.pipeline import DuatItemResult, DuatPipeline
from src.agents.s_agent import SAgent, SAgentInput
from src.rubric.loader import load_lqqopera_default

# Tag every test in this module — must opt in with `-m live`
pytestmark = [pytest.mark.live, pytest.mark.asyncio]


SAMPLE_TRANSCRIPT = """\
(student) 您好，我是負責照顧您的護理師，請問您今天哪裡不舒服？
(patient) 我胸口悶悶的，從早上就開始痛。
(student) 可以請您用手指出最痛的位置嗎？
(patient) 大概在這裡，胸口正中間偏左一點。
(student) 這個位置會不會跑到其他地方？例如手臂、背部或下巴？
(patient) 會耶，我覺得會傳到左邊肩膀和左手。
(student) 痛起來的感覺是什麼樣子的？是壓迫感、刺痛還是悶悶的？
(patient) 比較像是壓迫感，好像有人壓在我胸口上。
"""

SAMPLE_CASE_CONTEXT = (
    "62 歲男性，主訴突發性胸痛 2 小時。"
    "過去病史：高血壓、糖尿病、高血脂、30 年菸史（3 年前戒菸）。"
    "懷疑急性冠心症。"
)


class _NullBibliotheke:
    """In-memory stub so E-Agent doesn't need a live Postgres + pgvector."""

    async def search(self, *_args, **_kwargs):
        return []


def _skip_if_no_keys():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")


# === Single-agent live checks ==============================================

async def test_e_agent_extracts_location():
    _skip_if_no_keys()
    e = EAgent(bibliotheke=_NullBibliotheke())
    out = await e.run(
        EAgentInput(
            rubric_item_id="lqqopera.location",
            transcript_text=SAMPLE_TRANSCRIPT,
            case_context=SAMPLE_CASE_CONTEXT,
        )
    )
    assert out.rubric_item_id == "lqqopera.location"
    assert 0.0 <= out.confidence <= 1.0
    assert out.model_version.startswith("gemini")
    assert out.prompt_hash and out.prompt_hash.startswith("sha256:")
    # Should find at least one student utterance about location.
    assert len(out.evidence_segments) >= 1


async def test_s_agent_scores_location():
    _skip_if_no_keys()
    rubric = load_lqqopera_default()
    item = next(it for it in rubric.items if it.id == "lqqopera.location")

    bundle = {
        "rubric_item_id": "lqqopera.location",
        "evidence_segments": [
            {"speaker": "student", "text": "可以請您用手指出最痛的位置嗎？", "relevance_score": 0.95},
            {"speaker": "patient", "text": "大概在這裡，胸口正中間偏左一點。", "relevance_score": 0.8},
        ],
        "rag_hits": [],
        "confidence": 0.85,
        "extraction_notes": "student actively asked patient to point at the location",
    }

    s = SAgent()
    out = await s.run(
        SAgentInput(
            rubric_item_id="lqqopera.location",
            rubric_item_spec=item.model_dump(),
            evidence_bundle=bundle,
        )
    )
    assert 0 <= out.score <= 5
    # Asking patient to point at the location is a high-quality move per the
    # rubric — score should not be trivially low.
    assert out.score >= 2, f"unexpected low score {out.score}; cot={out.cot_reasoning!r}"
    assert out.cot_reasoning
    assert out.model_version.startswith("claude")


async def test_a_agent_reviews_independently():
    _skip_if_no_keys()
    rubric = load_lqqopera_default()
    item = next(it for it in rubric.items if it.id == "lqqopera.location")

    bundle = {
        "rubric_item_id": "lqqopera.location",
        "evidence_segments": [
            {"speaker": "student", "text": "請問哪裡不舒服？", "relevance_score": 0.5},
        ],
        "rag_hits": [],
        "confidence": 0.4,
        "extraction_notes": "thin evidence",
    }

    a = AAgent()
    out = await a.run(
        AAgentInput(
            rubric_item_id="lqqopera.location",
            rubric_item_spec=item.model_dump(),
            evidence_bundle=bundle,
        )
    )
    assert 0.0 <= out.advocate_score <= 1.0
    # Thin evidence should produce *some* dissent (>0); allow zero-tolerance though.
    assert out.advocate_report


# === Full pipeline =========================================================

async def test_full_duat_pipeline_one_item(tmp_path):
    _skip_if_no_keys()

    rubric = load_lqqopera_default()
    item = next(it for it in rubric.items if it.id == "lqqopera.location")

    # Inject a Null bibliotheke into the E-Agent so we don't need pgvector.
    e_agent = EAgent(bibliotheke=_NullBibliotheke())
    pipeline = DuatPipeline(e_agent=e_agent)

    # Use an isolated audit logger directory so we don't litter the repo
    from src.audit.logger import AuditLogger
    pipeline._audit = AuditLogger(log_dir=tmp_path / "audit")

    session_id = uuid.uuid4()
    result: DuatItemResult = await pipeline.score_item(
        session_id=session_id,
        rubric_item=item.model_dump(),
        evidence_inputs=EAgentInput(
            rubric_item_id="lqqopera.location",
            transcript_text=SAMPLE_TRANSCRIPT,
            case_context=SAMPLE_CASE_CONTEXT,
        ),
    )

    # Structural assertions
    assert result.rubric_item_id == "lqqopera.location"
    assert result.evidence.confidence >= 0.0
    assert 0 <= result.score.score <= 5
    assert 0.0 <= result.advocate.advocate_score <= 1.0
    assert result.arbiter.action in ("accept", "flag", "force_human")
    assert result.arbiter.confidence in ("high", "medium", "low")

    # Audit log should have the 5 events
    audit_path = tmp_path / "audit" / f"{session_id}.jsonl"
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    event_types = {Path(line).name for line in lines}  # don't actually need stems
    import json
    events = [json.loads(line)["event_type"] for line in lines]
    assert "duat.e_extracted" in events
    assert "duat.s_scored" in events
    assert "duat.a_reviewed" in events
    assert "duat.arbiter_decided" in events
    assert "duat.score_computed" in events


# === Arbiter sanity (cheap; doesn't need API) ==============================

def test_arbiter_unchanged_by_live_flag():
    """Sanity — live tests should not have inadvertently broken the rule layer."""
    d = arbitrate(e_confidence=0.9, s_score=4, a_advocate_score=0.1)
    assert d.action == "accept"
