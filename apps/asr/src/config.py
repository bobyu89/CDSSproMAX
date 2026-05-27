"""ASR service settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    asr_port: int = 8002
    breeze_model_id: str = "MediaTek-Research/Breeze-ASR-25"
    # 'cuda', 'cpu', or 'auto' (auto picks cuda if available)
    asr_device: str = "auto"
    asr_cache_dir: Path = REPO_ROOT / "asr-cache"
    # If True, do not load the model at startup — return a deterministic
    # stub from /transcribe. Useful for CI and frontend integration tests
    # on machines without a GPU.
    asr_stub_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.asr_cache_dir.mkdir(parents=True, exist_ok=True)
    return settings
