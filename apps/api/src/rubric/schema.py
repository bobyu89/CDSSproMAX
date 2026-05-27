"""Rubric Pydantic models — matches docs/architecture/rubric-schema.md.

Supports both LQQOPERA (interview) and PE (physical exam) rubric items.
PE-only fields (`body_region`, `expected_action`, `min_duration_seconds`)
are optional so the same schema covers both tracks.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RubricType = Literal["lqqopera", "pe"]


class RubricCriterion(BaseModel):
    """One scoring-level descriptor inside a rubric item."""

    model_config = ConfigDict(extra="forbid")

    level: int = Field(..., ge=0, le=5)
    descriptor: str

    @field_validator("descriptor")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("descriptor must be non-empty")
        return v


class RubricItem(BaseModel):
    """A single scored item (one LQQOPERA dimension or one PE manoeuvre)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    dimension: str
    weight: float = 1.0
    max_score: int = 5
    criteria: list[RubricCriterion] = Field(default_factory=list)
    evidence_anchors: list[str] | None = None

    # PE-only optionals (Wave 1.5 Vision Agent)
    body_region: str | None = None
    expected_action: str | None = None
    min_duration_seconds: float | None = None

    @field_validator("criteria")
    @classmethod
    def _criteria_present(cls, v: list[RubricCriterion]) -> list[RubricCriterion]:
        # Allow empty at construction time, but the loader's validator enforces
        # coverage of 0/5 endpoints for shipped rubrics.
        return v


class Rubric(BaseModel):
    """Top-level rubric document (one assessment track)."""

    model_config = ConfigDict(extra="forbid")

    rubric_id: str
    type: RubricType
    version: str = "1.0.0"
    items: list[RubricItem]

    def get_item(self, item_id: str) -> RubricItem | None:
        for it in self.items:
            if it.id == item_id:
                return it
        return None
