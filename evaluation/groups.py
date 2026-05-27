"""Three ablation-group runners (Protocol §五.(二) Level 1b).

  - A: full DUAT (E + S + A + Arbiter)
  - B: S-Agent only, no A-Agent (Arbiter passes through with a_advocate=0)
  - C: Single Claude Opus 4.7 + RAG baseline (one LLM does extract + score)

All three implement::

    async def score_sample(sample: GoldenSample) -> EvalResult

To keep the harness testable without live LLMs each runner accepts a
``score_fn`` injection in the constructor. The default ``score_fn`` is a stub
that raises ``NotImplementedError`` — production wiring lives behind that hook
so tests stay hermetic.

The full DuatPipeline import is **late-bound**: Agent A may not have built
``apps.api.src.agents.pipeline`` yet, and we do not want this module to fail to
import in that case. We use ``TYPE_CHECKING`` plus a runtime ``importlib`` call
inside Group A's default ``score_fn``.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .schema import EvalResult, GoldenSample

if TYPE_CHECKING:  # pragma: no cover — type hints only
    pass

# Make ``src.*`` importable when groups need to reach into apps/api/. Mirrors
# the pattern used by ``scripts/import_cases.py``.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_API_PATH = _REPO_ROOT / "apps" / "api"
if str(_API_PATH) not in sys.path:
    sys.path.insert(0, str(_API_PATH))


ScoreFn = Callable[[GoldenSample], Awaitable[dict[str, Any]]]
"""Signature: returns dict with keys:
    predicted_score:int, arbiter_decision:str, arbiter_confidence:str, notes:str
"""


async def _not_implemented(sample: GoldenSample) -> dict[str, Any]:  # noqa: ARG001
    raise NotImplementedError(
        "No score_fn injected. Provide one in the constructor or wire the "
        "production pipeline before calling .score_sample()."
    )


class _BaseGroup:
    group_name: str = "?"

    def __init__(self, score_fn: ScoreFn | None = None) -> None:
        self._score_fn: ScoreFn = score_fn or self._default_score_fn

    async def _default_score_fn(self, sample: GoldenSample) -> dict[str, Any]:
        return await _not_implemented(sample)

    async def score_sample(self, sample: GoldenSample) -> EvalResult:
        t0 = time.perf_counter()
        out = await self._score_fn(sample)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return EvalResult(
            sample_id=sample.sample_id,
            group=self.group_name,  # type: ignore[arg-type]
            predicted_score=int(out["predicted_score"]),
            arbiter_decision=out.get("arbiter_decision", "accept"),
            arbiter_confidence=out.get("arbiter_confidence", "high"),
            latency_ms=latency_ms,
            notes=out.get("notes", ""),
        )


class GroupA_FullDuat(_BaseGroup):
    """Full pipeline: E → (S, A) → Arbiter."""

    group_name = "A"

    async def _default_score_fn(self, sample: GoldenSample) -> dict[str, Any]:
        # Late import — pipeline.py may not exist yet (Agent A WIP).
        try:
            from importlib import import_module

            pipeline_mod = import_module("src.agents.pipeline")
        except ImportError as exc:  # pragma: no cover — depends on sibling work
            raise NotImplementedError(
                "apps/api/src/agents/pipeline.py not available — inject a "
                "score_fn or wait for the DuatPipeline implementation."
            ) from exc
        pipeline = pipeline_mod.DuatPipeline()  # type: ignore[attr-defined]
        result = await pipeline.run(
            rubric_item_id=sample.rubric_item_id,
            transcript=sample.transcript_text,
            case_context=sample.case_context,
        )
        return {
            "predicted_score": result.s_score,
            "arbiter_decision": result.arbiter.action,
            "arbiter_confidence": result.arbiter.confidence,
            "notes": "full_duat",
        }


class GroupB_NoAdversary(_BaseGroup):
    """E + S only. Arbiter still runs but A-advocate is forced to 0.0."""

    group_name = "B"

    async def _default_score_fn(self, sample: GoldenSample) -> dict[str, Any]:
        try:
            from importlib import import_module

            arbiter_mod = import_module("src.agents.arbiter")
            e_mod = import_module("src.agents.e_agent")
            s_mod = import_module("src.agents.s_agent")
        except ImportError as exc:  # pragma: no cover
            raise NotImplementedError(
                "E/S/Arbiter modules not available — inject a score_fn."
            ) from exc
        # Production wiring left as TODO — placeholder so the shape is clear.
        e_out = await e_mod.EAgent().run(...)  # type: ignore[attr-defined]
        s_out = await s_mod.SAgent().run(...)  # type: ignore[attr-defined]
        decision = arbiter_mod.arbitrate(
            e_confidence=e_out.confidence,
            s_score=s_out.score,
            a_advocate_score=0.0,  # A-Agent ablated
        )
        return {
            "predicted_score": s_out.score,
            "arbiter_decision": decision.action,
            "arbiter_confidence": decision.confidence,
            "notes": "no_adversary",
        }


class GroupC_SingleLlmBaseline(_BaseGroup):
    """Single Claude Opus 4.7 + RAG, no E/A/Arbiter decomposition.

    The prompt instructs the model to (1) extract evidence from the transcript,
    (2) consult RAG, (3) produce a 0-5 score — all in one shot. There is no
    arbitration, so ``arbiter_decision`` is always ``accept``.

    NOTE: prompt design is documented in the README; semantics are open for
    review by the protocol authors (see report-back).
    """

    group_name = "C"

    async def _default_score_fn(self, sample: GoldenSample) -> dict[str, Any]:
        # Default: no live LLM in tests. Production caller should inject.
        raise NotImplementedError(
            "GroupC baseline requires a live LLM client — inject score_fn."
        )

    async def score_sample(self, sample: GoldenSample) -> EvalResult:
        t0 = time.perf_counter()
        out = await self._score_fn(sample)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        # Force decision='accept' (no arbitration in the baseline).
        return EvalResult(
            sample_id=sample.sample_id,
            group="C",
            predicted_score=int(out["predicted_score"]),
            arbiter_decision="accept",
            arbiter_confidence=out.get("arbiter_confidence", "high"),
            latency_ms=latency_ms,
            notes=out.get("notes", "single_llm_baseline"),
        )


GROUP_REGISTRY: dict[str, type[_BaseGroup]] = {
    "A": GroupA_FullDuat,
    "B": GroupB_NoAdversary,
    "C": GroupC_SingleLlmBaseline,
}
