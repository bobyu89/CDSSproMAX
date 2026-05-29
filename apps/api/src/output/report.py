"""
個人化報告(康乃爾筆記格式) (Builder output.md)
================================================
把五種輸出組裝成 Cornell 三欄:線索欄 / 筆記欄 / 總結欄。
總結欄連結到 rag-note 的 Zettelkasten 卡片,單次複盤導向長期累積。
"""

from __future__ import annotations


def build_cornell_report(outputs: dict, zettel_cards: dict) -> dict:
    radar = outputs["radar"]["dimensions"]
    stress = outputs["stress"]
    analysis = outputs["weakness"]["duat_analysis"]

    rows = [
        {"cue": "問診", "notes": f"分數 {radar['問診']};{str(analysis)[:80]}"},
        {"cue": "身評", "notes": f"分數 {radar['身評']};操作軌跡見附錄"},
        {"cue": "診斷", "notes": f"分數 {radar['診斷']};三診斷排序與推理"},
        {"cue": "壓力", "notes": f"壓力峰值 {stress.get('peak')}"},
    ]
    card_links = [f"[[{c['topic']}]]" for c in zettel_cards.get("cards", [])]
    summary = {
        "narrative": outputs["narrative"]["text"],
        "key_focus": outputs["keyfocus"]["focus"],
        "linked_cards": card_links,
    }
    return {"type": "cornell_report", "rows": rows, "summary": summary}
