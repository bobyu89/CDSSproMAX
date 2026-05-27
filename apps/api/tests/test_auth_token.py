"""Auth — JWT issuance + decoding round-trip (no DB)."""

import uuid
from datetime import datetime, timezone

import jwt

from src.config import get_settings
from src.db.models import Participant
from src.routers.auth import _make_token


def _fake_participant() -> Participant:
    p = Participant()
    p.id = uuid.uuid4()
    p.participant_code = "T001"
    p.role = "teacher"
    p.name = "Tester"
    return p


def test_token_round_trip():
    settings = get_settings()
    p = _fake_participant()
    token, expires_at = _make_token(p)
    decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"] == str(p.id)
    assert decoded["code"] == "T001"
    assert decoded["role"] == "teacher"
    assert decoded["name"] == "Tester"
    assert decoded["exp"] == expires_at
    assert expires_at > int(datetime.now(timezone.utc).timestamp())


def test_token_invalid_signature_rejected():
    p = _fake_participant()
    token, _ = _make_token(p)
    try:
        jwt.decode(token, "wrong-secret", algorithms=["HS256"])
    except jwt.InvalidSignatureError:
        return
    raise AssertionError("expected InvalidSignatureError")
