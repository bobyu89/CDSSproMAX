"""Health check endpoint — used by docker, deployment, and Step 3 smoke test."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
        version="0.1.0",
    )
