"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fpl_totw"

    # FPL API
    fpl_base_url: str = "https://fantasy.premierleague.com/api"

    # Application
    debug: bool = False
    cors_origins: list[str] = ["*"]

    # Model settings
    model_version: str = "v1.0.0"
    min_training_gws: int = 5  # Minimum GWs needed before making predictions

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
