"""Application settings, loaded from environment / .env file at repo root."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # === App ===
    app_name: str = "TICDSS API"
    app_env: str = Field(default="development")
    api_port: int = 8001

    # === Database ===
    database_url: str = Field(
        default="postgresql+asyncpg://ticdss:change_me_locally@localhost:5433/ticdss"
    )

    # === LLM ===
    anthropic_api_key: str = ""
    google_api_key: str = ""
    s_agent_model: str = "claude-opus-4-7"
    e_agent_model: str = "gemini-3.5-flash"
    a_agent_model: str = "gemini-3.5-flash"
    v_agent_model: str = "gemini-3.5-flash"

    # === ASR ===
    asr_service_url: str = "http://localhost:8002"
    breeze_model_id: str = "MediaTek-Research/Breeze-ASR-25"

    # === Langfuse ===
    langfuse_host: str = "http://localhost:3001"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # === RAG ===
    embedding_model: str = "BAAI/bge-base-zh-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"

    # === Audit ===
    audit_log_dir: Path = REPO_ROOT / "audit_logs"

    # === Object storage (MinIO / S3) ===
    storage_backend: str = "none"  # 's3' | 'none'
    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = "ticdss-keyframes"
    s3_public_base_url: str = ""

    # === Auth ===
    jwt_secret: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 12


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.audit_log_dir.mkdir(parents=True, exist_ok=True)
    return settings
