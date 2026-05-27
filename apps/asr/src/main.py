"""FastAPI app exposing Breeze-ASR-25 as POST /transcribe."""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.breeze import TranscriptionResult, get_asr
from src.config import get_settings


class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration_s: float
    model_id: str
    stub: bool


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TICDSS ASR",
        version="0.1.0",
        description=f"Breeze-ASR-25 wrapper ({settings.breeze_model_id})",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "model": settings.breeze_model_id,
            "stub_mode": str(settings.asr_stub_mode),
        }

    @app.post("/transcribe", response_model=TranscribeResponse)
    async def transcribe(file: UploadFile = File(...)) -> TranscribeResponse:
        audio = await file.read()
        if not audio:
            raise HTTPException(status_code=400, detail="empty audio")

        result: TranscriptionResult = get_asr().transcribe(audio)
        return TranscribeResponse(
            text=result.text,
            language=result.language,
            duration_s=result.duration_s,
            model_id=result.model_id,
            stub=result.stub,
        )

    return app


app = create_app()
