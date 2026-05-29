"""
流程引擎 + 註冊表 (Builder core.md / contract-v1.0)
===================================================
流程引擎只認契約,不認任何階段的內部實作。
註冊表是熱插拔的開關:換版本 = 改一行註冊。
"""

from __future__ import annotations

import logging

from src.core.contract import CONTRACT_VERSION, StageAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """熱插拔核心:管理階段名稱 → Agent 類別的對應。"""

    def __init__(self) -> None:
        self._reg: dict[str, type[StageAgent]] = {}

    def register(self, stage: str, agent_cls: type[StageAgent]) -> None:
        # 相容性檢查:確認 Agent 遵守的契約版本與 core 一致。
        agent_version = getattr(agent_cls, "contract_version", None)
        if agent_version != CONTRACT_VERSION:
            logger.warning(
                "agent %s registered for stage '%s' declares contract %s, "
                "core is %s — hot-swap compatibility not guaranteed",
                agent_cls.__name__,
                stage,
                agent_version,
                CONTRACT_VERSION,
            )
        self._reg[stage] = agent_cls

    def get_agent(self, stage: str) -> StageAgent | None:
        cls = self._reg.get(stage)
        return cls() if cls else None

    def registered_stages(self) -> list[str]:
        return list(self._reg.keys())


# 全域單例 — 各模組 import 它來註冊/取用。
registry = AgentRegistry()


async def run_phase(session, receive_inputs):
    """
    流程引擎核心。任何 Agent 被替換都不需修改這段,
    因為它只呼叫契約定義的四個方法。

    receive_inputs: async generator,yield 該階段的 payload。
    """
    agent = registry.get_agent(session.phase.value)
    if agent is None:
        return  # 無對應 Agent 的階段(如過渡期)
    yield {"type": "enter", "state": agent.on_enter(session)}
    async for payload in receive_inputs(session):
        resp = await agent.handle_input(session, payload)
        yield {"type": "response", "data": resp}
    score = agent.score(session)
    session.phase_scores[session.phase.value] = score
    agent.on_exit(session)
    yield {"type": "score", "score": score}
