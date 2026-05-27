"""Object storage abstraction — MinIO / S3 backend for keyframes.

Design:
  - Single ``StorageClient`` interface so callers don't depend on aioboto3.
  - When ``STORAGE_BACKEND=none`` or aioboto3 isn't installed, falls back
    to a no-op client that returns empty paths. The vision router handles
    that gracefully — the PeObservation row is still written with
    ``keyframe_paths=[]`` and the scoring still happens.
  - Keys are namespaced by session_id / rubric_item_id / uuid so we never
    overwrite. Files have a TTL (configurable) via S3 object lifecycle —
    set up via MinIO admin or `mc ilm add` (out of scope here).
"""

from __future__ import annotations

import base64
import logging
import uuid
from abc import ABC, abstractmethod
from functools import lru_cache

from src.config import get_settings

logger = logging.getLogger(__name__)


class StorageClient(ABC):
    @abstractmethod
    async def put_keyframes(
        self,
        *,
        session_id: uuid.UUID,
        rubric_item_id: str,
        images_b64: list[str],
    ) -> list[str]:
        """Upload a list of base64-encoded JPEGs. Returns the URL list."""

    @abstractmethod
    async def healthcheck(self) -> dict[str, str | bool]:
        ...


class NoopStorage(StorageClient):
    """Used when STORAGE_BACKEND=none or aioboto3 unavailable."""

    async def put_keyframes(
        self,
        *,
        session_id: uuid.UUID,
        rubric_item_id: str,
        images_b64: list[str],
    ) -> list[str]:
        return []

    async def healthcheck(self) -> dict[str, str | bool]:
        return {"backend": "noop", "ok": True}


class S3Storage(StorageClient):
    """aioboto3-backed S3 / MinIO client."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.s3_access_key_id or not self.settings.s3_secret_access_key:
            raise RuntimeError("S3 credentials not configured")

    async def _client(self):
        import aioboto3  # type: ignore[import-untyped]

        session = aioboto3.Session()
        return session.client(
            "s3",
            endpoint_url=self.settings.s3_endpoint_url or None,
            region_name=self.settings.s3_region,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
        )

    @staticmethod
    def _decode(b64: str) -> tuple[bytes, str]:
        """Strip optional data-URL prefix, return (bytes, mime)."""
        mime = "image/jpeg"
        data = b64
        if data.startswith("data:") and "," in data:
            header, data = data.split(",", 1)
            try:
                mime = header.split(":", 1)[1].split(";", 1)[0] or "image/jpeg"
            except IndexError:
                pass
        return base64.b64decode(data), mime

    def _build_url(self, key: str) -> str:
        base = self.settings.s3_public_base_url.rstrip("/")
        if base:
            return f"{base}/{key}"
        # Fall back to endpoint-style URL (works for MinIO with `mc anonymous`)
        endpoint = (self.settings.s3_endpoint_url or "").rstrip("/")
        return f"{endpoint}/{self.settings.s3_bucket}/{key}"

    async def put_keyframes(
        self,
        *,
        session_id: uuid.UUID,
        rubric_item_id: str,
        images_b64: list[str],
    ) -> list[str]:
        if not images_b64:
            return []

        urls: list[str] = []
        bucket = self.settings.s3_bucket
        client_cm = await self._client()
        async with client_cm as s3:
            burst_id = uuid.uuid4().hex[:8]
            for idx, b64 in enumerate(images_b64):
                try:
                    data, mime = self._decode(b64)
                except Exception as exc:
                    logger.warning("keyframe %d decode failed: %s", idx, exc)
                    continue
                ext = "jpg" if "jpeg" in mime or "jpg" in mime else "png"
                key = (
                    f"sessions/{session_id}/"
                    f"{rubric_item_id}/{burst_id}/{idx:02d}.{ext}"
                )
                await s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=mime,
                )
                urls.append(self._build_url(key))
        return urls

    async def healthcheck(self) -> dict[str, str | bool]:
        try:
            client_cm = await self._client()
            async with client_cm as s3:
                await s3.head_bucket(Bucket=self.settings.s3_bucket)
            return {
                "backend": "s3",
                "endpoint": self.settings.s3_endpoint_url,
                "bucket": self.settings.s3_bucket,
                "ok": True,
            }
        except Exception as exc:  # pragma: no cover - infra-dependent
            return {"backend": "s3", "ok": False, "error": str(exc)}


@lru_cache
def get_storage_client() -> StorageClient:
    settings = get_settings()
    if settings.storage_backend.lower() != "s3":
        logger.info("STORAGE_BACKEND=%s — keyframes will not be persisted", settings.storage_backend)
        return NoopStorage()
    try:
        return S3Storage()
    except Exception as exc:
        logger.warning("S3Storage init failed (%s) — falling back to noop", exc)
        return NoopStorage()
