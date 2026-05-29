"""
個人化學習講義(Zettelkasten 雙卡) (Builder rag-note.md / v2.0)
================================================================
弱點 → 檢索 → 永久卡(知識,累積)+ 訓練卡(失誤,新增)。Obsidian 格式。

與 builder 規格的差異(已對齊使用者決定):
- 知識庫用我們既有的 pgvector(非 ChromaDB)。檢索器以 retrieve_fn 注入,
  預設為 no-op(回 []),production 由 router 傳入 src.rag 的 pgvector 檢索器。
"""

from __future__ import annotations

import datetime
import json

from src.llm.router import call_llm


def _default_retrieve(query: str, k: int = 4):
    """預設檢索器(no-op)。production 注入 pgvector 檢索。"""
    return []


def _topic_of(weak_point: str) -> str:
    return weak_point.split(":")[-1].strip()


async def generate_cards(session, weakness, duat_result, retrieve_fn=None, student_id=None):
    """依弱點生成/更新雙卡。回傳要寫入 Obsidian 的卡片清單。"""
    retrieve = retrieve_fn or _default_retrieve
    weak_items = weakness["items"]
    if not weak_items:
        return {"type": "zettel_cards", "cards": [], "message": "本次無明顯弱點。"}

    today = datetime.date.today().isoformat()
    scenario = session.scenario_id
    analysis = duat_result["analysis"].payload.get("analysis", "")
    memory = duat_result["memory"].payload.get("memory", "")

    cards = []
    for wp in weak_items:
        topic = _topic_of(wp)
        contexts = retrieve(wp)

        perm = await call_llm(
            "diagnosis",
            prompt=(
                f"知識主題:{topic}\n參考資料:{[c.get('text') for c in contexts]}\n"
                f"請寫一張 Zettelkasten 永久卡的核心概念與重要性(知識本身,不綁定特定訓練)。"
                f'回傳JSON:{{"core":"...","why":"...","links":["相關主題"]}}'
            ),
            session=session,
            json_mode=True,
        )
        perm_data = _parse(perm.text)
        sources = [
            {"source": c.get("source"), "ref": c.get("ref"), "type": c.get("type")}
            for c in contexts
        ]

        train = await call_llm(
            "diagnosis",
            prompt=(
                f"弱點:{wp}\n本次分析:{analysis}\nM-Agent歷程:{memory}\n"
                f"請寫一張訓練卡:這次失誤的具體描述 + 當時情境。"
                f'回傳JSON:{{"failure":"...","context":"..."}}'
            ),
            session=session,
            json_mode=True,
        )
        train_data = _parse(train.text)

        cards.append({
            "permanent": _render_permanent(topic, perm_data, sources, today),
            "training": _render_training(topic, wp, scenario, train_data, memory, today),
            "topic": topic,
        })

    return {"type": "zettel_cards", "cards": cards}


def _render_permanent(topic, data, sources, today) -> str:
    links = "\n".join(f"- [[{l}]]" for l in data.get("links", []))
    refs = "\n".join(
        f"- {s['source']} *{s['ref'] or ''}* ({s['type']})" for s in sources
    )
    return f"""---
type: permanent
topic: {topic}
created: {today}
---

> [!note] 核心概念
> {data.get('core', '')}

## 為什麼重要
{data.get('why', '')}

## 延伸
{links}

## 文獻出處
{refs}

## 訓練紀錄(自動累積)
- [[{today} {topic} 失誤紀錄]]
"""


def _render_training(topic, wp, scenario, data, memory, today) -> str:
    return f"""---
type: training
date: {today}
scenario: {scenario}
weak_point: {wp}
---

> [!warning] 這次的失誤
> {data.get('failure', '')}

## 當時情境
{data.get('context', '')}

## 連結知識
- [[{topic}]]

## M-Agent 歷程提示
> {memory}
"""


def _parse(txt):
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return {}
