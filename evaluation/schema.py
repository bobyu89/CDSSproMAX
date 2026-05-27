"""Pydantic models for the TICDSS ablation harness.

Mirrors the data contract used by Protocol §五.(二) Level 1b Ablation Study.
Lives intentionally outside ``apps/api/`` so the harness can be reasoned about
independently of the production pipeline (read-only consumer).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt

GroupName = Literal["A", "B", "C"]
ArbiterAction = Literal["accept", "flag", "force_human"]


class GoldenSample(BaseModel):
    """One human-graded rubric item used as ground truth."""

    sample_id: str
    rubric_item_id: str
    case_id: str
    transcript_text: str
    case_context: str = ""
    human_score: int = Field(ge=0, le=5)
    human_rater_id: str | None = None


class EvalResult(BaseModel):
    """Per-(sample, group) output row."""

    sample_id: str
    group: GroupName
    predicted_score: int = Field(ge=0, le=5)
    arbiter_decision: ArbiterAction
    arbiter_confidence: Literal["high", "medium", "low"]
    latency_ms: NonNegativeInt = 0
    notes: str = ""


class MetricsReport(BaseModel):
    """Aggregate metrics for a single ablation group."""

    group: GroupName
    n: NonNegativeInt
    icc: float
    kappa: float
    mae: NonNegativeFloat
    pct_agree_exact: float
    pct_agree_within_1: float
    n_accept: NonNegativeInt
    n_flag: NonNegativeInt
    n_force_human: NonNegativeInt


class PairwiseDelta(BaseModel):
    """Delta between two groups on the core metrics (left - right)."""

    left: GroupName
    right: GroupName
    d_icc: float
    d_kappa: float
    d_mae: float


class AblationReport(BaseModel):
    """Top-level report serialised to JSON alongside the per-row CSV."""

    timestamp: str
    dataset_path: str
    n_samples: NonNegativeInt
    groups: dict[str, MetricsReport]
    pairwise_deltas: list[PairwiseDelta] = Field(default_factory=list)
