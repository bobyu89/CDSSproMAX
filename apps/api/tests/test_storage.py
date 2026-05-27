"""Storage client — Noop fallback + S3 URL construction."""

import base64
import uuid

import pytest

from src.services.storage import NoopStorage, S3Storage, get_storage_client


pytestmark = pytest.mark.asyncio


async def test_noop_returns_empty_paths():
    s = NoopStorage()
    paths = await s.put_keyframes(
        session_id=uuid.uuid4(),
        rubric_item_id="pe.lung.auscultation",
        images_b64=["data:image/jpeg;base64,/9j/4A=="],
    )
    assert paths == []


async def test_noop_healthcheck():
    h = await NoopStorage().healthcheck()
    assert h["ok"] is True
    assert h["backend"] == "noop"


def test_s3_decode_strips_data_url():
    raw_data = b"hello world"
    b64 = base64.b64encode(raw_data).decode()
    decoded, mime = S3Storage._decode(f"data:image/png;base64,{b64}")
    assert decoded == raw_data
    assert mime == "image/png"


def test_s3_decode_raw_base64():
    raw_data = b"abc"
    b64 = base64.b64encode(raw_data).decode()
    decoded, mime = S3Storage._decode(b64)
    assert decoded == raw_data
    assert mime == "image/jpeg"  # default


def test_s3_url_construction_with_public_base(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "y")
    monkeypatch.setenv("S3_PUBLIC_BASE_URL", "https://cdn.example/keyframes")
    from src.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    storage = S3Storage()
    url = storage._build_url("sessions/abc/pe.x/burst/00.jpg")
    assert url == "https://cdn.example/keyframes/sessions/abc/pe.x/burst/00.jpg"


def test_s3_url_construction_endpoint_fallback(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "y")
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://localhost:9000")
    monkeypatch.setenv("S3_PUBLIC_BASE_URL", "")
    monkeypatch.setenv("S3_BUCKET", "kf")
    from src.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    storage = S3Storage()
    url = storage._build_url("sessions/abc/pe.x/burst/00.jpg")
    assert url == "http://localhost:9000/kf/sessions/abc/pe.x/burst/00.jpg"


async def test_get_storage_client_falls_back_to_noop_without_creds(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "")
    from src.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    get_storage_client.cache_clear()  # type: ignore[attr-defined]
    s = get_storage_client()
    assert isinstance(s, NoopStorage)


async def test_get_storage_client_noop_when_backend_none(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "none")
    from src.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    get_storage_client.cache_clear()  # type: ignore[attr-defined]
    s = get_storage_client()
    assert isinstance(s, NoopStorage)
