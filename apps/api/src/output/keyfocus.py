"""重點提示:從弱點分析挑最該注意的一個(依賴 weakness)。(Builder output.md)"""

from __future__ import annotations


def build_keyfocus(weakness: dict) -> dict:
    items = weakness["items"]
    top = items[0] if items else "整體表現良好,維持目前水準"
    return {"type": "keyfocus", "focus": top, "rationale": weakness["duat_analysis"]}
