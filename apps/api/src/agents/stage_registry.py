"""
三軌 StageAgent 註冊 (Builder inquiry/vision/diagnosis.md)
==========================================================
把三個階段 Agent 註冊到 core.registry。明確呼叫,避免 import 副作用。

熱插拔升級:把某 stage 換成 V2 只要改這裡一行 register。
"""

from __future__ import annotations

from src.agents.diagnosis_agent import DiagnosisAgentV1
from src.agents.inquiry_agent import InquiryAgentV1
from src.agents.vision_agent import VisionAgentV2
from src.core.registry import registry


def register_stage_agents() -> None:
    registry.register("inquiry", InquiryAgentV1)
    registry.register("examination", VisionAgentV2)
    registry.register("diagnosis", DiagnosisAgentV1)


__all__ = ["register_stage_agents"]
