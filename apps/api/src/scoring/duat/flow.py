"""
DUAT 協調流程 (Builder duat-flow.md + TICDSS 驗證層)
=====================================================
迴圈結束後的深度驗證。O → (E‖S) → A → M,並在 E 之後加跑驗證層。
五代理皆用 LLM(System 2 深度分析);驗證層為 TICDSS 研究亮點。

並行依賴:
    O 觀察(先跑)
      ├── E 評估 ┐(並行,都只依賴 O)
      └── S 綜整 ┘
      ↓
    驗證層(對抗 + Arbiter,依賴 E)  ‖  A 分析(依賴 E + S)
      ↓
    M 記憶(依賴 A)
"""

from __future__ import annotations

import asyncio

from src.scoring.duat.analyze import run_analyze
from src.scoring.duat.evaluate import run_evaluate
from src.scoring.duat.memory import run_memory
from src.scoring.duat.observe import run_observe
from src.scoring.duat.synthesize import run_synthesize
from src.scoring.duat.verification import run_verification


async def deep_verify(session, student_id=None, history_loader=None) -> dict:
    """DUAT 主流程。回傳最終深度驗證結果(供 output 使用)。"""
    # 1. O-Agent 先跑:彙整全程資料
    observation = await run_observe(session)

    # 2. E-Agent 與 S-Agent 並行(都只依賴 O)
    evaluation, synthesis = await asyncio.gather(
        run_evaluate(session, observation),
        run_synthesize(session, observation),
    )

    # 3. 驗證層(對抗 + Arbiter,依賴 E)與 A-Agent(依賴 E+S)並行
    verification, analysis = await asyncio.gather(
        run_verification(session, evaluation),
        run_analyze(session, evaluation, synthesis),
    )

    # 4. M-Agent 記憶(依賴 A,比對歷程)
    memory = await run_memory(
        session, analysis, student_id=student_id, history_loader=history_loader
    )

    return {
        "observation": observation,
        "evaluation": evaluation,
        "synthesis": synthesis,
        "verification": verification,  # TICDSS 驗證層
        "analysis": analysis,
        "memory": memory,
    }
