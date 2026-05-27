"""Smoke test for ASR service in stub mode (no model load, no GPU)."""

import os

# Force stub mode BEFORE importing the app so the settings cache picks it up.
os.environ["ASR_STUB_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from src.main import app  # noqa: E402


def test_health_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"


def test_transcribe_stub_returns_fake_text():
    client = TestClient(app)
    # any non-empty bytes will do in stub mode
    files = {"file": ("dummy.wav", b"\x00\x01", "audio/wav")}
    resp = client.post("/transcribe", files=files)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["stub"] is True
    assert "stub" in payload["text"].lower()


def test_transcribe_rejects_empty():
    client = TestClient(app)
    files = {"file": ("empty.wav", b"", "audio/wav")}
    resp = client.post("/transcribe", files=files)
    assert resp.status_code == 400
