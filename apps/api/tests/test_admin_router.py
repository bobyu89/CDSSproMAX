"""Admin router — Pydantic input validation (no DB)."""

from __future__ import annotations

import uuid

import pydantic
import pytest

from src.routers.admin import (
    CreateParticipantRequest,
    ParticipantScoreSummary,
    WithheldUpdateRequest,
)


# === ParticipantScoreSummary ==============================================


def test_participant_score_summary_accepts_valid():
    s = ParticipantScoreSummary(
        participant_id=uuid.uuid4(),
        participant_code="P001",
        name="Alice",
        role="student",
        session_count=3,
        mean_score=4.2,
    )
    assert s.session_count == 3
    assert s.mean_score == 4.2


def test_participant_score_summary_allows_null_mean():
    s = ParticipantScoreSummary(
        participant_id=uuid.uuid4(),
        participant_code="P002",
        name="Bob",
        role="teacher",
        session_count=0,
        mean_score=None,
    )
    assert s.mean_score is None


# === CreateParticipantRequest =============================================


def test_create_participant_accepts_valid():
    r = CreateParticipantRequest(
        participant_code="P001",
        name="Alice",
        role="student",
        password="secret12",
    )
    assert r.participant_code == "P001"
    assert r.email is None


def test_create_participant_accepts_all_roles():
    for role in ("student", "teacher", "admin"):
        CreateParticipantRequest(
            participant_code="ABC123",
            name="x",
            role=role,
            password="password",
        )


def test_create_participant_rejects_lowercase_code():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="p001",
            name="Alice",
            role="student",
            password="secret12",
        )


def test_create_participant_rejects_special_chars():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="P-001",
            name="Alice",
            role="student",
            password="secret12",
        )


def test_create_participant_rejects_starting_digit():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="1ABC",
            name="Alice",
            role="student",
            password="secret12",
        )


def test_create_participant_rejects_too_short_code():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="AB",
            name="Alice",
            role="student",
            password="secret12",
        )


def test_create_participant_rejects_too_long_code():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="A" * 13,
            name="Alice",
            role="student",
            password="secret12",
        )


def test_create_participant_rejects_short_password():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="P001",
            name="Alice",
            role="student",
            password="short",
        )


def test_create_participant_rejects_invalid_role():
    with pytest.raises(pydantic.ValidationError):
        CreateParticipantRequest(
            participant_code="P001",
            name="Alice",
            role="superadmin",  # not in enum
            password="secret12",
        )


# === WithheldUpdateRequest ================================================


def test_withheld_update_accepts_bool():
    assert WithheldUpdateRequest(is_withheld=True).is_withheld is True
    assert WithheldUpdateRequest(is_withheld=False).is_withheld is False


def test_withheld_update_requires_bool_field():
    with pytest.raises(pydantic.ValidationError):
        WithheldUpdateRequest()  # type: ignore[call-arg]
