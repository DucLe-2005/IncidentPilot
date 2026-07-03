from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "IncidentPilot"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://incidentpilot:incidentpilot@localhost:5432/incidentpilot"
    )
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    slack_webhook_url: str | None = None
    llm_provider: str = "placeholder"
    llm_model: str = "placeholder"
    evidence_window_minutes: int = Field(default=15, ge=1, le=1440)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
