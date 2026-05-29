"""DUAT 深度驗證 (Builder duat-agents/duat-flow.md) + TICDSS 驗證層.

O→(E‖S)→A→M,E 之後加跑對抗式 + 規則 Arbiter 驗證層(可重播稽核)。
"""

from src.scoring.duat.flow import deep_verify

__all__ = ["deep_verify"]
