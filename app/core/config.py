from pathlib import Path
from typing import List, Optional

from pydantic import AnyUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "pdf_ai_engine"
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    database_url: AnyUrl = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")

    cors_origins: List[str] = Field(default_factory=lambda: ["*"])  # يسمح بالطلبات من أي مصدر بشكل افتراضي
    storage_backend: str = Field("local", env="STORAGE_BACKEND")
    local_storage_path: Path = Field(Path("storage"), env="LOCAL_STORAGE_PATH")

    max_upload_size_mb: int = Field(50, env="MAX_UPLOAD_SIZE_MB")
    google_credentials_path: Optional[Path] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    google_vision_max_calls_per_document: int = Field(10, env="GOOGLE_VISION_MAX_CALLS_PER_DOCUMENT")
    google_vision_max_calls_per_day: int = Field(1000, env="GOOGLE_VISION_MAX_CALLS_PER_DAY")
