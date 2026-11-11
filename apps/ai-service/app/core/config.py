from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_service_name: str = "DevFlow AI"
    ai_service_version: str = "0.1.0"
    ai_service_port: int = 8000

    openai_api_key: str = ""
    openai_model: str = ""
    embedding_model: str = "text-embedding-3-small"

    # PostgreSQL configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_username: str = ""
    db_password: str = ""
    db_database: str = ""


settings = Settings()