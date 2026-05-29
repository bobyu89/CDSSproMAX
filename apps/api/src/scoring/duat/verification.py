"""
DUAT 驗證層 (TICDSS 研究亮點 — builder 第 25 個模組)
=====================================================
這是 builder DUAT 之上「額外的可稽核驗證層」(使用者決定:全部保留)。
保留三個原系統的研究差異化:
  1. 跨廠商對抗式審查(adversarial)— 用獨立 LLM 挑戰 evaluate 的評估
  2. 規則型 Arbiter(accept/flag/force_human)— 純函式、可測試、可重播
  3. Audit 事件 — 產出 JSONL-ready 稽核 payload(prompt_hash/model/decision)

設計:本層不直接寫 DB / JSONL,而是把稽核事件累加到
session.scratch["audit_events"];實際 sink(JSONL + audit_events 表)由
router/persistence 層 flush。如此本層可獨立測試、不綁 DB。
"""

from __future__ import annotations

import hashlib
import json

from src.agents.arbiter import arbitrate
from src.core.contract import EvalResult
from src.llm.router import call_llm


def _prompt_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return f"sha256:{h.hexdigest()[:32]}"


def _parse(txt):
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return {}


async def run_verification(session, evaluation: EvalResult) -> EvalResult:
    """對 evaluate 的評估跑對抗式審查 + 規則仲裁,並產出稽核事件。"""
    eval_text = evaluation.payload.get("evaluation", "")
    prompt = (
        f"你是對抗式審查代理。以下是另一個 AI 對學員臨床表現的評估:\n{eval_text}\n\n"
        f"請獨立挑戰這份評估,不要附和。回傳JSON:\n"
        f'{{"advocate_score": 0到1之間(你對此評估的異議強度,越高代表越不同意),'
        f'"eval_confidence": 0到1之間(此評估證據是否充分),'
        f'"challenged_points": ["..."]}}'
    )
    resp = await call_llm("duat", prompt=prompt, session=session, json_mode=True)
    data = _parse(resp.text)

    advocate_score = _clamp(data.get("advocate_score", 0.5))
    e_confidence = _clamp(data.get("eval_confidence", 0.5))
    challenged = data.get("challenged_points", [])
    if not isinstance(challenged, list):
        challenged = [str(challenged)]

    # 規則型仲裁(純函式,可重播)
    decision = arbitrate(
        e_confidence=e_confidence, s_score=0, a_advocate_score=advocate_score
    )

    # 產出稽核事件(JSONL-ready;sink 由上層 flush)
    audit_event = {
        "event_type": "duat.verification",
        "prompt_hash": _prompt_hash(prompt),
        "model_version": resp.usage.model,
        "e_confidence": e_confidence,
        "a_advocate_score": advocate_score,
        "arbiter_action": decision.action,
        "arbiter_confidence": decision.confidence,
        "thresholds_version": decision.thresholds_version,
        "challenged_points": challenged,
    }
    session.scratch.setdefault("audit_events", []).append(audit_event)

    return EvalResult(
        source="duat-verification",
        payload={
            "advocate_score": advocate_score,
            "e_confidence": e_confidence,
            "challenged_points": challenged,
            "arbiter_action": decision.action,
            "arbiter_confidence": decision.confidence,
            "thresholds_version": decision.thresholds_version,
        },
    )


def _clamp(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, f))
