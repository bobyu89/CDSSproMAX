"""DUAT Pipeline orchestrator.

Per docs/architecture/duat-pipeline.md the per-item flow is:

    E-Agent ──► Evidence Bundle ──┬──► S-Agent ──┐
                                  │              ├──► Consensus Arbiter
                                  └──► A-Agent ──┘

S-Agent and A-Agent each consume the Evidence Bundle INDEPENDENTLY and run
in parallel via ``asyncio.gather``. The Consensus Arbiter (rule-based, NOT
an LLM) is what compares their outputs.

Every step emits a Langfuse span (when configured) and an audit-log event
keyed on ``session_id``.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

import asyncio

from src.agents.a_agent import AAgent, AAgentInput, AAgentOutput
from src.agents.arbiter import ArbiterDecision, arbitrate
from src.agents.e_agent import EAgent, EAgentInput, EAgentOutput
from src.agents.s_agent import SAgent, SAgentInput, SAgentOutput
from src.audit import AuditEventType, get_audit_logger
from src.observability import trace_span


class DuatItemResult(BaseModel):
    """Aggregate output for a single rubric item — all four agent outputs + Arbiter."""

    rubric_item_id: str
    evidence: EAgentOutput
    score: SAgentOutput
    advocate: AAgentOutput
    arbiter: ArbiterDecision


class DuatPipeline:
    """Orchestrates E → (S ∥ A) → Arbiter for one rubric item at a time."""

    def __init__(
        self,
        e_agent: EAgent | None = None,
        s_agent: SAgent | None = None,
        a_agent: AAgent | None = None,
    ) -> None:
        # Allow injection (tests pass stubs); fall back to defaults otherwise.
        # NOTE: default EAgent() constructs a Bibliotheke client which may fail
        # without a configured DB. Callers running offline tests should inject.
        self._e = e_agent if e_agent is not None else EAgent()
        self._s = s_agent if s_agent is not None else SAgent()
        self._a = a_agent if a_agent is not None else AAgent()
        self._audit = get_audit_logger()

    @staticmethod
    def _as_uuid(session_id: str | uuid.UUID) -> uuid.UUID:
        if isinstance(session_id, uuid.UUID):
            return session_id
        try:
            return uuid.UUID(str(session_id))
        except (ValueError, AttributeError):
            # Deterministic-ish placeholder so audit log paths stay valid in tests
            return uuid.uuid5(uuid.NAMESPACE_OID, str(session_id))

    async def score_item(
        self,
        *,
        session_id: str | uuid.UUID,
        rubric_item: dict[str, Any],
        evidence_inputs: EAgentInput,
    ) -> DuatItemResult:
        """Run the full DUAT pipeline for a single rubric item.

        Args:
            session_id: OSCE session UUID (or stringified UUID).
            rubric_item: serialized RubricItem dict (passed to S/A).
            evidence_inputs: payload for the E-Agent.

        Returns:
            DuatItemResult bundling E / S / A outputs + Arbiter decision.
        """
        sid_uuid = self._as_uuid(session_id)
        sid_str = str(sid_uuid)
        rubric_item_id = evidence_inputs.rubric_item_id

        # === Step 1: E-Agent extraction ===========================
        with trace_span("duat.e_agent", session_id=sid_str, input_data=evidence_inputs.model_dump()) as span:
            evidence = await self._e.run(evidence_inputs)
            if span is not None:
                span.update(output=evidence.model_dump())

        await self._audit.log(
            session_id=sid_uuid,
            event_type=AuditEventType.DUAT_E_EXTRACTED,
            rubric_item_id=rubric_item_id,
            prompt_hash=evidence.prompt_hash,
            model_version=evidence.model_version,
            payload={
                "confidence": evidence.confidence,
                "n_segments": len(evidence.evidence_segments),
                "n_rag_hits": len(evidence.rag_hits),
            },
        )

        bundle = evidence.as_bundle()

        # === Step 2: S-Agent and A-Agent in parallel ==============
        s_input = SAgentInput(
            rubric_item_id=rubric_item_id,
            rubric_item_spec=rubric_item,
            evidence_bundle=bundle,
        )
        a_input = AAgentInput(
            rubric_item_id=rubric_item_id,
            rubric_item_spec=rubric_item,
            evidence_bundle=bundle,
        )

        async def _run_s() -> SAgentOutput:
            with trace_span("duat.s_agent", session_id=sid_str, input_data=s_input.model_dump()) as span:
                out = await self._s.run(s_input)
                if span is not None:
                    span.update(output=out.model_dump())
                return out

        async def _run_a() -> AAgentOutput:
            with trace_span("duat.a_agent", session_id=sid_str, input_data=a_input.model_dump()) as span:
                out = await self._a.run(a_input)
                if span is not None:
                    span.update(output=out.model_dump())
                return out

        score, advocate = await asyncio.gather(_run_s(), _run_a())

        await self._audit.log(
            session_id=sid_uuid,
            event_type=AuditEventType.DUAT_S_SCORED,
            rubric_item_id=rubric_item_id,
            prompt_hash=score.prompt_hash,
            model_version=score.model_version,
            payload={
                "score": score.score,
                "cited_evidence_ids": score.cited_evidence_ids,
            },
        )
        await self._audit.log(
            session_id=sid_uuid,
            event_type=AuditEventType.DUAT_A_REVIEWED,
            rubric_item_id=rubric_item_id,
            prompt_hash=advocate.prompt_hash,
            model_version=advocate.model_version,
            payload={
                "advocate_score": advocate.advocate_score,
                "n_challenged_points": len(advocate.challenged_points),
            },
        )

        # === Step 3: Consensus Arbiter (rule-based) ===============
        with trace_span("duat.arbiter", session_id=sid_str) as span:
            decision = arbitrate(
                e_confidence=evidence.confidence,
                s_score=score.score,
                a_advocate_score=advocate.advocate_score,
            )
            if span is not None:
                span.update(output=decision.model_dump())

        await self._audit.log(
            session_id=sid_uuid,
            event_type=AuditEventType.DUAT_ARBITER_DECIDED,
            rubric_item_id=rubric_item_id,
            payload={
                "action": decision.action,
                "confidence": decision.confidence,
                "flag_reason": decision.flag_reason,
                "thresholds_version": decision.thresholds_version,
            },
        )

        # === Step 4: Final score-computed audit row ===============
        await self._audit.log(
            session_id=sid_uuid,
            event_type=AuditEventType.DUAT_SCORE_COMPUTED,
            rubric_item_id=rubric_item_id,
            payload={
                "score": score.score,
                "e_confidence": evidence.confidence,
                "a_advocate_score": advocate.advocate_score,
                "action": decision.action,
            },
        )

        return DuatItemResult(
            rubric_item_id=rubric_item_id,
            evidence=evidence,
            score=score,
            advocate=advocate,
            arbiter=decision,
        )
