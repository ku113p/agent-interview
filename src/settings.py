import os

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.infra.security.source import SecretsSettingsSource


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.prod"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
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

    # Security
    SECRETS_BACKEND: str = "env"

    # App Defaults
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Context Management
    CONVERSATION_WINDOW_SIZE: int = 6
    SUMMARY_THRESHOLD: int = 10

    # Database Pooling
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            SecretsSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()  # type: ignore
