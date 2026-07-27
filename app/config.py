from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "AgentCare"
    app_env: str = "development"
    debug: bool = False

    database_url: str = "sqlite:///./agentcare.db"

    llm_provider: str = "groq"
    llm_model: str = "qwen/qwen3.6-27b"
    groq_api_key: str = ""

    secret_key: str = ""
    access_token_expire_minutes: int = 60

    upload_directory: str = "storage/documents"
    max_upload_size_mb: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()