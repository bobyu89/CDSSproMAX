"""core 契約驗證 — 對應 builder-spec/sub-agents/core.md「驗證方式」。

1. DummyAgent(StageAgent) 實作四方法。
2. registry.register("inquiry", DummyAgent)。
3. run_phase 在不知道實作細節下完成一個階段。
4. score() 回傳的 StageScore 含正確 contract_version。
"""

from __future__ import annotations

import pytest

from src.core import (
    CONTRACT_VERSION,
    Phase,
    StageAgent,
    StageScore,
    TrainingSession,
    registry,
    run_phase,
)


class DummyAgent(StageAgent):
    stage_name = "inquiry"

    def on_enter(self, session) -> dict:
        return {"prompt": "請開始問診"}

    async def handle_input(self, session, payload: dict) -> dict:
        session.scratch.setdefault("turns", []).append(payload.get("text", ""))
        return {"ack": True}

    def score(self, session) -> StageScore:
        n = len(session.scratch.get("turns", []))
        return StageScore(stage="inquiry", raw_score=min(100.0, n * 25.0))

    def on_exit(self, session) -> dict:
        return {"summary": f"{len(session.scratch.get('turns', []))} turns"}


@pytest.mark.asyncio
async def test_run_phase_with_dummy_agent():
    registry.register("inquiry", DummyAgent)
    session = TrainingSession(mode="practice", scenario_id="case-x", phase=Phase.INQUIRY)

    async def feed(_session):
        for text in ["哪裡痛", "什麼時候開始", "會不會擴散"]:
            yield {"text": text, "silence": 0.5, "prosody": None}

    events = [evt async for evt in run_phase(session, feed)]
    kinds = [e["type"] for e in events]

    assert kinds[0] == "enter"
    assert kinds[-1] == "score"
    assert kinds.count("response") == 3

    score = events[-1]["score"]
    assert isinstance(score, StageScore)
    assert score.stage == "inquiry"
    assert score.raw_score == 75.0
    assert score.contract_version == CONTRACT_VERSION
    # phase_scores 應已寫入
    assert session.phase_scores["inquiry"].raw_score == 75.0


def test_registry_compat_check(caplog):
    """註冊契約版本不符的 agent 應發出 warning,但仍註冊。"""

    class StaleAgent(DummyAgent):
        contract_version = "0.9"

    registry.register("diagnosis", StaleAgent)
    assert "diagnosis" in registry.registered_stages()
    assert any("compatibility" in r.message for r in caplog.records)


def test_session_advance_and_time_limit():
    s = TrainingSession(mode="exam", scenario_id="c", phase=Phase.INQUIRY)
    assert s.time_limit() == 360
    assert s.advance() == Phase.TRANSITION
    assert s.time_limit() == 30
    # practice 模式無時限
    s2 = TrainingSession(mode="practice", scenario_id="c", phase=Phase.INQUIRY)
    assert s2.time_limit() is None
