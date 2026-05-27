"""DUAT pipeline orchestration tests.

Verifies:
  - E → (S ∥ A) → Arbiter ordering produces a complete DuatItemResult
  - All 5 audit events (E, S, A, Arbiter, SCORE_COMPUTED) land in JSONL
  - Arbiter receives the correct E confidence + A advocate score
  - All four agent outputs are present on the result
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from src.agents.a_agent import AAgent
from src.agents.e_agent import EAgent
from src.agents.pipeline import DuatPipeline
from src.agents.s_agent import SAgent
from src.audit.logger import AuditLogger

pytestmark = pytest.mark.asyncio


class _NullBibliotheke:
    async def search(self, *args, **kwargs):  # noqa: ARG002
        return []


async def test_pipeline_runs_all_five_audit_events(monkeypatch, tmp_path: Path):
    # Stub all three LLM helpers — no network.
    from src.agents import a_agent as a_module
    from src.agents import e_agent as e_module
    from src.agents import s_agent as s_module

    async def fake_e_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "rubric_item_id": "lqqopera.location",
            "evidence_segments": [
                {"speaker": "student", "text": "請問痛在哪裡？會傳到哪邊嗎？", "relevance_score": 0.92}
            ],
            "confidence": 0.9,
            "extraction_notes": "asked location + radiation",
        }

    async def fake_claude(*, model, system, user_message, max_tokens=2048):  # noqa: ARG001
        return {
            "score": 4,
            "cot_reasoning": "詢問位置與放射路徑，達 level 4。",
            "cited_evidence_ids": [0],
        }

    async def fake_a_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "advocate_report": "未請病人指認部位。",
            "advocate_score": 0.2,
            "challenged_points": ["未請病人指認部位"],
        }

    monkeypatch.setattr(e_module, "gemini_generate_json", fake_e_gemini)
    monkeypatch.setattr(s_module, "claude_generate_json", fake_claude)
    monkeypatch.setattr(a_module, "gemini_generate_json", fake_a_gemini)

    # Per-test AuditLogger so JSONL lands in tmp_path
    logger = AuditLogger(log_dir=tmp_path)

    pipeline = DuatPipeline(
        e_agent=EAgent(bibliotheke=_NullBibliotheke()),
        s_agent=SAgent(),
        a_agent=AAgent(),
    )
    pipeline._audit = logger  # inject per-test logger

    session_id = uuid.uuid4()
    rubric_item = {
        "id": "lqqopera.location",
        "dimension": "Location",
        "max_score": 5,
        "criteria": [
            {"level": 5, "descriptor": "主動詢問位置與放射"},
            {"level": 0, "descriptor": "未詢問"},
        ],
    }

    result = await pipeline.score_item(
        session_id=session_id,
        rubric_item=rubric_item,
        evidence_inputs=e_module.EAgentInput(
            rubric_item_id="lqqopera.location",
            transcript_text="(student): 請問痛在哪裡？會傳到哪邊嗎？",
            case_context="chest pain",
        ),
    )

    # (c) result contains all four agent outputs
    assert result.rubric_item_id == "lqqopera.location"
    assert result.evidence.confidence == 0.9
    assert result.score.score == 4
    assert result.advocate.advocate_score == 0.2

    # (b) arbiter invoked with correct inputs: e=0.9 (>=0.8) and a=0.2 (<0.3) → accept/high
    assert result.arbiter.action == "accept"
    assert result.arbiter.confidence == "high"

    # (a) all 5 audit events written
    log_file = tmp_path / f"{session_id}.jsonl"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    event_types = [json.loads(line)["event_type"] for line in lines]
    assert "duat.e_extracted" in event_types
    assert "duat.s_scored" in event_types
    assert "duat.a_reviewed" in event_types
    assert "duat.arbiter_decided" in event_types
    assert "duat.score_computed" in event_types
    assert len(event_types) == 5


async def test_pipeline_force_human_on_low_confidence(monkeypatch, tmp_path: Path):
    """Low E confidence + strong A dissent → arbiter forces human review."""
    from src.agents import a_agent as a_module
    from src.agents import e_agent as e_module
    from src.agents import s_agent as s_module

    async def fake_e_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {
            "rubric_item_id": "lqqopera.quality",
            "evidence_segments": [],
            "confidence": 0.3,
            "extraction_notes": "thin",
        }

    async def fake_claude(*, model, system, user_message, max_tokens=2048):  # noqa: ARG001
        return {"score": 2, "cot_reasoning": "evidence weak", "cited_evidence_ids": []}

    async def fake_a_gemini(*, model, prompt, system_instruction, response_schema=None):  # noqa: ARG001
        return {"advocate_report": "no quality terms", "advocate_score": 0.7, "challenged_points": ["missing quality"]}

    monkeypatch.setattr(e_module, "gemini_generate_json", fake_e_gemini)
    monkeypatch.setattr(s_module, "claude_generate_json", fake_claude)
    monkeypatch.setattr(a_module, "gemini_generate_json", fake_a_gemini)

    pipeline = DuatPipeline(
        e_agent=EAgent(bibliotheke=_NullBibliotheke()),
        s_agent=SAgent(),
        a_agent=AAgent(),
    )
    pipeline._audit = AuditLogger(log_dir=tmp_path)

    result = await pipeline.score_item(
        session_id=uuid.uuid4(),
        rubric_item={"id": "lqqopera.quality", "max_score": 5, "criteria": []},
        evidence_inputs=e_module.EAgentInput(
            rubric_item_id="lqqopera.quality",
            transcript_text="(student): ...",
        ),
    )

    assert result.arbiter.action == "force_human"
    assert result.arbiter.confidence == "low"
