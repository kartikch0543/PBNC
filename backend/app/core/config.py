import os
from typing import List, Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Document Intelligence & Question Extraction Service"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "dev_secret_key_please_override_in_production_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "document_intelligence"
    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    @computed_field
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    def sync_database_url(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    @computed_field
    def redis_connection_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    @computed_field
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # AI / Vision
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Worker
    WORKER_MAX_CONCURRENT_JOBS: int = 5


settings = Settings()
