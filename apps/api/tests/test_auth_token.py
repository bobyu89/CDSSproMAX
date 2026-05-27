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
    p.role = "teacher"
    p.name = "Tester"
    return p


def test_token_round_trip():
    settings = get_settings()
    p = _fake_participant()
    token = _make_token(p)
    decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"] == str(p.id)
    assert decoded["role"] == "teacher"
    assert decoded["name"] == "Tester"
    assert decoded["exp"] > int(datetime.now(timezone.utc).timestamp())


def test_token_invalid_signature_rejected():
    p = _fake_participant()
    token = _make_token(p)
    try:
        jwt.decode(token, "wrong-secret", algorithms=["HS256"])
    except jwt.InvalidSignatureError:
        return
    raise AssertionError("expected InvalidSignatureError")
