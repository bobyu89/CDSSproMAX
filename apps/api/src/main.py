"""FastAPI entry point for the TICDSS backend.

Wave 1 scope: skeleton with health endpoint, DB session, DUAT agent shells.
Real LLM calls land in Step 12 (see scripts/seed_db.py and routers/duat.py).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.routers import (
    admin,
    auth,
    cases,
    duat,
    grading,
    health,
    physio,
    sessions,
    transcripts,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    # NOTE: keep startup side effects minimal — DB and LLM clients are lazy.
    print(f"[ticdss-api] starting in {settings.app_env} on port {settings.api_port}")
    yield
    print("[ticdss-api] shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="DUAT five-agent OSCE assessment backend",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(cases.router)
    app.include_router(sessions.router)
    app.include_router(transcripts.router)
    app.include_router(duat.router)
    app.include_router(grading.router)
    app.include_router(admin.router)
    app.include_router(physio.router)
    return app


app = create_app()
