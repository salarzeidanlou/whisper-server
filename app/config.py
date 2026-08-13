from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://whisper:whisper@localhost:5432/whisper"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = Field(default=7, ge=1, le=365)

    # Rate limiting
    LOGIN_RATE_LIMIT: int = Field(default=5, ge=1)  # max attempts
    LOGIN_RATE_WINDOW: int = Field(default=300, ge=1)  # seconds (5 min)

    # CORS
    CORS_ORIGINS: str = ""  # comma-separated origins, e.g. "https://app.example.com"

    # Environment
    ENVIRONMENT: str = ""  # "development" or "production"

    # WebSocket auth ticket TTL
    WS_TICKET_TTL: int = Field(default=30, ge=1, le=300)  # seconds

    # Trusted proxy IPs that are allowed to set X-Forwarded-For
    # Comma-separated, e.g. "127.0.0.1,10.0.0.0/8"
    TRUSTED_PROXIES: str = ""

    # coturn TURN server (self-hosted)
    COTURN_SECRET: str = ""
    COTURN_REALM: str = "turn.example.com"

    model_config = {"env_file": ".env", "extra": "ignore"}


_UNSAFE_SECRET_MARKERS = ("change-me", "changeme", "replace-me")


def _is_unsafe_secret(secret: str) -> bool:
    normalized = secret.strip().lower()
    return (
        len(secret.encode("utf-8")) < 32
        or normalized in {"secret", "test"}
        or any(marker in normalized for marker in _UNSAFE_SECRET_MARKERS)
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if _is_unsafe_secret(settings.JWT_SECRET_KEY):
        raise RuntimeError(
            "JWT_SECRET_KEY must be at least 32 bytes and must not use a "
            "placeholder value"
        )
    return settings
