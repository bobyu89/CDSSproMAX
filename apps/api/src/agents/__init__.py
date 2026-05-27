"""DUAT five-agent pipeline + Consensus Arbiter.

Naming maps 1:1 to Protocol §四:
  - O-Agent: orchestrator / state machine
  - E-Agent: evidence extractor (sole RAG accessor)
  - S-Agent: scorer (Claude Opus 4.7, CoT)
  - A-Agent: adversarial reviewer (Gemini)
  - M-Agent: drift monitor (rule + LLM, runs continuously)
  - Arbiter: rule-based consensus (NOT an LLM)
"""

from src.agents.a_agent import AAgent
from src.agents.arbiter import ArbiterDecision, arbitrate
from src.agents.base import Agent, AgentResult
from src.agents.e_agent import EAgent
from src.agents.m_agent import MAgent
from src.agents.o_agent import OAgent
from src.agents.s_agent import SAgent

__all__ = [
    "AAgent",
    "Agent",
    "AgentResult",
    "ArbiterDecision",
    "EAgent",
    "MAgent",
    "OAgent",
    "SAgent",
    "arbitrate",
]
