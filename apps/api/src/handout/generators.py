"""LLM-driven generators for the personal handout.

- ``generate_study_notes``        → Claude (narrative-friendly)
- ``generate_mindmap``            → Gemini (structured output)
- ``generate_discussion_prompts`` → Claude

All three gracefully fall back to deterministic 繁體中文 stubs when the
relevant API key is missing — mirrors ``v_agent.py``'s ``_stub_output``
pattern so tests can run offline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.handout.schema import (
    DiscussionPrompt,
    MindMapNode,
    StudyNoteSection,
)
from src.services.llm_clients import claude_generate_json, gemini_generate_json

logger = logging.getLogger(__name__)

_PROMPTS_DIR = (
    Path(__file__).resolve().parents[3].parent / "packages" / "shared-prompts"
)


def _load_prompt(name: str, fallback: str) -> str:
    path = _PROMPTS_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("prompt file %s not found, using minimal fallback", path)
        return fallback


# ─── Study notes (Claude) ────────────────────────────────────────────────


def _study_notes_stub(weak_dimensions: list[str]) -> list[StudyNoteSection]:
    if not weak_dimensions:
        return [
            StudyNoteSection(
                heading="維持優勢",
                body=(
                    "本次表現整體穩定，無明顯弱項。建議延續目前的問診結構（LQQOPERA），"
                    "並於下次練習挑戰更複雜的鑑別診斷情境，例如非典型胸痛或腹痛。"
                ),
                citations=["LQQOPERA 框架"],
            )
        ]
    out: list[StudyNoteSection] = []
    for dim in weak_dimensions[:5]:
        out.append(
            StudyNoteSection(
                heading=f"加強：{dim}",
                body=(
                    f"本次評分顯示『{dim}』維度為弱點。建議下次練習時，"
                    f"先以開放式問句引導病人描述，再以封閉式問句確認細節，"
                    f"並於每次練習後對照 LQQOPERA 框架自我檢查是否完整。"
                ),
                citations=["Bickley & Szilagyi, 2021", "LQQOPERA 框架"],
            )
        )
    return out


async def generate_study_notes(
    *,
    case_title: str,
    weak_dimensions: list[str],
    dimension_scores: dict[str, int],
    transcript_excerpt: str = "",
) -> list[StudyNoteSection]:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return _study_notes_stub(weak_dimensions)

    system = _load_prompt(
        "handout_study_notes.txt",
        "Generate 3-5 study-note sections as JSON {sections: [...]} in 繁體中文.",
    )
    user_msg = (
        f"案例：{case_title}\n"
        f"弱項維度：{weak_dimensions or '（無）'}\n"
        f"各維度分數：{dimension_scores}\n"
        f"逐字稿節錄：{transcript_excerpt[:600]}\n"
    )
    try:
        data = await claude_generate_json(
            model=settings.s_agent_model,
            system=system,
            user_message=user_msg,
            max_tokens=2048,
        )
    except Exception as exc:  # pragma: no cover - network/api errors
        logger.warning("study-notes Claude call failed: %s", exc)
        return _study_notes_stub(weak_dimensions)

    raw = data.get("sections") or []
    out: list[StudyNoteSection] = []
    for s in raw:
        try:
            out.append(StudyNoteSection.model_validate(s))
        except Exception:
            continue
    return out or _study_notes_stub(weak_dimensions)


# ─── Mind map (Gemini structured) ────────────────────────────────────────


def _mindmap_stub(
    case_title: str, weak_dimensions: list[str]
) -> list[MindMapNode]:
    nodes: list[MindMapNode] = [
        MindMapNode(
            id="root",
            label=case_title or "本次 OSCE 案例",
            level=1,
            parent_id=None,
            kind="key_concept",
        )
    ]
    for i, dim in enumerate(weak_dimensions[:4], start=1):
        wid = f"w{i}"
        nodes.append(
            MindMapNode(
                id=wid,
                label=f"弱項：{dim}",
                level=2,
                parent_id="root",
                kind="weakness",
            )
        )
        nodes.append(
            MindMapNode(
                id=f"a{i}",
                label=f"行動：強化 {dim} 問句模板",
                level=3,
                parent_id=wid,
                kind="action",
            )
        )
    nodes.append(
        MindMapNode(
            id="ref1",
            label="LQQOPERA 框架",
            level=2,
            parent_id="root",
            kind="reference",
        )
    )
    return nodes


async def generate_mindmap(
    *,
    case_title: str,
    weak_dimensions: list[str],
    dimension_scores: dict[str, int],
) -> list[MindMapNode]:
    settings = get_settings()
    if not settings.google_api_key:
        return _mindmap_stub(case_title, weak_dimensions)

    system = _load_prompt(
        "handout_mindmap.txt",
        "Output JSON {nodes: [...]} with 10-15 nodes, max depth 3, 繁體中文.",
    )
    prompt = (
        f"案例標題：{case_title}\n"
        f"弱項維度：{weak_dimensions or '（無）'}\n"
        f"各維度分數：{dimension_scores}\n"
        f"請以本案例為根節點建立心智圖。"
    )
    try:
        data = await gemini_generate_json(
            model=settings.e_agent_model,
            prompt=prompt,
            system_instruction=system,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("mindmap Gemini call failed: %s", exc)
        return _mindmap_stub(case_title, weak_dimensions)

    raw = data.get("nodes") or []
    out: list[MindMapNode] = []
    for n in raw:
        try:
            out.append(MindMapNode.model_validate(n))
        except Exception:
            continue
    return out or _mindmap_stub(case_title, weak_dimensions)


# ─── Discussion prompts (Claude) ─────────────────────────────────────────


def _discussion_stub(
    weak_dimensions: list[str], narrative_growth: str | None
) -> list[DiscussionPrompt]:
    out: list[DiscussionPrompt] = []
    for dim in (weak_dimensions or ["整體問診流程"])[:4]:
        out.append(
            DiscussionPrompt(
                question=f"在臨床上，如何在有限時間內完整評估『{dim}』？",
                why=(
                    f"本次評分顯示『{dim}』為弱項，"
                    "向督導確認實務取捨策略可加速臨床轉化。"
                ),
                related_dimension=dim,
            )
        )
    if narrative_growth:
        out.append(
            DiscussionPrompt(
                question=f"關於我設定的成長目標『{narrative_growth[:30]}』，督導建議的具體練習步驟是？",
                why="把學生自評的成長目標放到督導視角下，能避免閉門造車。",
                related_dimension=None,
            )
        )
    return out[:5]


async def generate_discussion_prompts(
    *,
    case_title: str,
    weak_dimensions: list[str],
    dimension_scores: dict[str, int],
    narrative_growth: str | None = None,
) -> list[DiscussionPrompt]:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return _discussion_stub(weak_dimensions, narrative_growth)

    system = _load_prompt(
        "handout_discussion.txt",
        "Output JSON {prompts: [...]} with 3-5 supervisor-facing questions, 繁體中文.",
    )
    user_msg = (
        f"案例：{case_title}\n"
        f"弱項維度：{weak_dimensions or '（無）'}\n"
        f"各維度分數：{dimension_scores}\n"
        f"學生自填成長目標：{narrative_growth or '（未填寫）'}\n"
    )
    try:
        data = await claude_generate_json(
            model=settings.s_agent_model,
            system=system,
            user_message=user_msg,
            max_tokens=1500,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("discussion Claude call failed: %s", exc)
        return _discussion_stub(weak_dimensions, narrative_growth)

    raw = data.get("prompts") or []
    out: list[DiscussionPrompt] = []
    for p in raw:
        try:
            out.append(DiscussionPrompt.model_validate(p))
        except Exception:
            continue
    return out or _discussion_stub(weak_dimensions, narrative_growth)
