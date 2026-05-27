"""Abstract base for all DUAT agents.

Wave 1 shell: every agent returns a deterministic stub so the pipeline
can be wired end-to-end before real LLM calls land (Step 12+).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class AgentResult(BaseModel):
    """Base shape of any agent's output — concrete agents extend this."""

    model_config = ConfigDict(extra="allow")

    agent_name: str
    model_version: str
    prompt_hash: str | None = None
    raw: dict[str, Any] = {}


class Agent(ABC, Generic[TInput, TOutput]):
    """Abstract DUAT agent.

    Concrete agents implement ``run`` and declare their input/output
    Pydantic models via the class type parameters.
    """

    name: str
    model_id: str

    @abstractmethod
    async def run(self, payload: TInput) -> TOutput:
        """Execute the agent on the given payload."""
        ...
