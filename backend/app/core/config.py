from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment / .env.

    Never hardcode secrets here — ANTHROPIC_API_KEY must always come from
    the environment and must never be sent to the frontend.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"
    cors_origins: str = "http://localhost:5173"
    database_path: str = "./app/data/app.db"
    vector_db_url: str = "postgresql://ise2:ise2@localhost:5432/ise2_vectors"
    embedding_model: str = "all-MiniLM-L6-v2"
    context_dir: str = "../context"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
