"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings for API configuration."""

    app_env: str
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    cors_origins: list[str]
    seed_on_startup: bool


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_cors_origins(raw: str | None, app_env: str) -> list[str]:
    if raw and raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    if app_env.lower() == "production":
        return []
    return ["*"]


def get_settings() -> Settings:
    """Load settings from environment with local-development defaults."""
    app_env = os.getenv("APP_ENV", "development")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        if app_env.lower() == "production":
            raise RuntimeError("DATABASE_URL is required in production.")
        database_url = "postgresql://postgres:postgres@db:5432/board_game_tracker"

    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is required. Set JWT_SECRET_KEY in the environment."
        )

    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    cors_origins = _parse_cors_origins(os.getenv("CORS_ORIGINS"), app_env)
    seed_on_startup = _parse_bool(os.getenv("SEED_ON_STARTUP"), default=True)

    return Settings(
        app_env=app_env,
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        jwt_access_token_expire_minutes=jwt_access_token_expire_minutes,
        cors_origins=cors_origins,
        seed_on_startup=seed_on_startup,
    )
