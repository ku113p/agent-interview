from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/interview_db"
    )  # type: ignore
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")  # type: ignore

    OPENAI_API_KEY: SecretStr = Field(default=SecretStr("sk-placeholder"))

    # App Defaults
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"


settings = Settings()
