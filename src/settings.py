import os

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    OPENAI_API_KEY: SecretStr
    TELEGRAM_BOT_TOKEN: SecretStr
    OPENAI_BASE_URL: str | None = Field(default=None)
    MODEL_NAME: str = "openai/gpt-4o-mini"

    LANGFUSE_HOST: str = Field(default="http://localhost:3000")
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: SecretStr
    USE_SIMULATED_LLM: bool = Field(
        default_factory=lambda: "PYTEST_CURRENT_TEST" in os.environ
    )

    # App Defaults
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"


settings = Settings()  # type: ignore
