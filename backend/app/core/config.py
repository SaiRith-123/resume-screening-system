"""Application settings loaded from environment variables (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV_FILE), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Intelligent Resume Screening System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # Security
    SECRET_KEY: str = "dev-insecure-change-me-000000000000000000"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "postgresql+psycopg://rss:rss_password@localhost:5432/resume_screening"

    # Async
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    USE_CELERY: bool = False

    # Rate limiting ("N/unit", unit: second|minute|hour)
    RATE_LIMIT_DEFAULT: str = "240/minute"
    RATE_LIMIT_AUTH: str = "20/minute"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # Uploads
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_UPLOAD_MB: int = 10
    STORAGE_BACKEND: str = "local"  # local | s3
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    EMBEDDING_BACKEND: str = "transformers"  # transformers | hash (explicit degraded mode)
    EMBEDDING_CACHE_DIR: str = ".cache/embeddings"

    # LLM
    LLM_PROVIDER: str = "null"  # openai | generic | local | null
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 45
    LLM_MAX_RETRIES: int = 3
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GENERIC_LLM_URL: str = ""
    GENERIC_LLM_API_KEY: str = ""
    LOCAL_LLM_URL: str = "http://localhost:11434/v1/chat/completions"
    LOCAL_LLM_MODEL: str = "llama3"

    # Firebase Admin verification uses application default credentials.
    FIREBASE_PROJECT_ID: str = ""

    @field_validator("SECRET_KEY")
    @classmethod
    def _warn_secret(cls, v: str) -> str:
        return v

    @model_validator(mode="after")
    def validate_production_storage(self):
        if self.is_production:
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("Production requires a remote PostgreSQL DATABASE_URL")
            if self.STORAGE_BACKEND.lower() != "s3" or not self.S3_BUCKET:
                raise ValueError("Production requires configured S3-compatible remote storage")
            if self.SECRET_KEY.startswith("dev-insecure"):
                raise ValueError("Production requires a non-default SECRET_KEY")
            if not self.FIREBASE_PROJECT_ID:
                raise ValueError("Production requires FIREBASE_PROJECT_ID")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
