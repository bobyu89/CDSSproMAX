"""Generator tests — stub fallbacks + monkey-patched LLM clients."""

from __future__ import annotations

import pytest

from src.handout import generators
from src.handout.schema import (
    DiscussionPrompt,
    MindMapNode,
    StudyNoteSection,
)


pytestmark = pytest.mark.asyncio


# ─── Stub paths (no API keys set) ────────────────────────────────────────


async def test_study_notes_stub_no_api_key(monkeypatch):
    """With no anthropic_api_key, generator returns deterministic stub."""
    settings = generators.get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    out = await generators.generate_study_notes(
        case_title="60 歲男性胸痛",
        weak_dimensions=["Quality", "Onset"],
        dimension_scores={"Quality": 1, "Onset": 2},
    )
    assert all(isinstance(s, StudyNoteSection) for s in out)
    assert len(out) >= 1
    # Stub content is 繁體中文
    assert any("Quality" in s.heading or "加強" in s.heading for s in out)


async def test_mindmap_stub_no_api_key(monkeypatch):
    settings = generators.get_settings()
    monkeypatch.setattr(settings, "google_api_key", "")
    out = await generators.generate_mindmap(
        case_title="胸痛案例",
        weak_dimensions=["Quality"],
        dimension_scores={"Quality": 1},
    )
    assert all(isinstance(n, MindMapNode) for n in out)
    # Has a root and at least one weakness
    assert any(n.kind == "key_concept" and n.level == 1 for n in out)
    assert any(n.kind == "weakness" for n in out)


async def test_discussion_stub_includes_growth_question(monkeypatch):
    settings = generators.get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    out = await generators.generate_discussion_prompts(
        case_title="胸痛案例",
        weak_dimensions=["Quality"],
        dimension_scores={"Quality": 1},
        narrative_growth="想練習更系統性的鑑別診斷",
    )
    assert all(isinstance(p, DiscussionPrompt) for p in out)
    assert 1 <= len(out) <= 5
    # The narrative-growth-derived prompt should appear
    assert any("成長目標" in p.question for p in out)


# ─── Monkey-patched LLM clients (real-API path) ──────────────────────────


async def test_study_notes_parses_claude_json(monkeypatch):
    settings = generators.get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "fake-key")

    async def fake_claude(**kwargs):
        return {
            "sections": [
                {
                    "heading": "強化 Quality 維度",
                    "body": "下次練習時請使用開放式提問引導病人描述疼痛性質。",
                    "citations": ["LQQOPERA 框架"],
                }
            ]
        }

    monkeypatch.setattr(generators, "claude_generate_json", fake_claude)
    out = await generators.generate_study_notes(
        case_title="胸痛案例",
        weak_dimensions=["Quality"],
        dimension_scores={"Quality": 1},
    )
    assert len(out) == 1
    assert out[0].heading == "強化 Quality 維度"
    assert "LQQOPERA 框架" in out[0].citations


async def test_mindmap_parses_gemini_json(monkeypatch):
    settings = generators.get_settings()
    monkeypatch.setattr(settings, "google_api_key", "fake-key")

    async def fake_gemini(**kwargs):
        return {
            "nodes": [
                {"id": "root", "label": "胸痛案例", "level": 1, "parent_id": None,
                 "kind": "key_concept"},
                {"id": "w1", "label": "弱項：Quality", "level": 2, "parent_id": "root",
                 "kind": "weakness"},
            ]
        }

    monkeypatch.setattr(generators, "gemini_generate_json", fake_gemini)
    out = await generators.generate_mindmap(
        case_title="胸痛案例",
        weak_dimensions=["Quality"],
        dimension_scores={"Quality": 1},
    )
    assert len(out) == 2
    assert out[0].id == "root"
    assert out[1].kind == "weakness"


async def test_discussion_falls_back_on_claude_error(monkeypatch):
    settings = generators.get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "fake-key")

    async def boom(**kwargs):
        raise RuntimeError("api down")

    monkeypatch.setattr(generators, "claude_generate_json", boom)
    out = await generators.generate_discussion_prompts(
        case_title="胸痛案例",
        weak_dimensions=["Quality"],
        dimension_scores={"Quality": 1},
        narrative_growth=None,
    )
    # Stub fallback engaged → still produces prompts
    assert len(out) >= 1
    assert all(isinstance(p, DiscussionPrompt) for p in out)
