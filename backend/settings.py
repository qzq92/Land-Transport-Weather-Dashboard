"""Runtime configuration for the API service."""

from functools import lru_cache
from typing import Annotated

from pydantic import (
    BeforeValidator,
    Field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_origins(value: object) -> object:
    """Accept either JSON arrays or comma-separated origins from the environment."""
    if isinstance(value, str) and not value.lstrip().startswith("["):
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    return value


OriginList = Annotated[list[str], NoDecode, BeforeValidator(_split_origins)]


class Settings(BaseSettings):
    """Validated settings loaded from environment variables and an optional .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BACKEND_",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "LTA Transport Dashboard API"
    api_prefix: str = "/api/v1"
    cors_origins: OriginList = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    http_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    http_max_connections: int = Field(default=100, ge=1, le=1000)
    http_max_keepalive_connections: int = Field(default=20, ge=1, le=200)

    redis_url: str | None = None
    redis_required: bool = False
    redis_timeout_seconds: float = Field(default=1.0, gt=0, le=10)
    cache_version: str = Field(default="v1", pattern=r"^[a-zA-Z0-9_.-]+$")
    cache_ttl_seconds: int = Field(default=120, ge=1, le=86400)
    cache_stale_seconds: int = Field(default=3600, ge=1, le=604800)
    cache_ttl_jitter_ratio: float = Field(default=0.1, ge=0, le=0.5)
    cache_lock_seconds: int = Field(default=15, ge=1, le=120)
    cache_lock_wait_seconds: float = Field(default=1.0, ge=0, le=10)

    data_gov_api_key: str | None = None
    lta_api_key: str | None = None
    onemap_api_key: str | None = None
    onemap_email: str | None = None
    onemap_email_password: str | None = None

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        normalized = "/" + value.strip("/")
        if normalized == "/":
            raise ValueError("api_prefix cannot be the root path")
        return normalized

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: list[str]) -> list[str]:
        if not origins:
            raise ValueError("at least one CORS origin is required")
        normalized: list[str] = []
        for origin in origins:
            candidate = origin.rstrip("/")
            if candidate == "*" or not candidate.startswith(("http://", "https://")):
                raise ValueError("CORS origins must be explicit http(s) origins")
            normalized.append(candidate)
        if len(set(normalized)) != len(normalized):
            raise ValueError("CORS origins must be unique")
        return normalized

    @model_validator(mode="after")
    def validate_redis_requirement(self) -> "Settings":
        if self.redis_required and not self.redis_url:
            raise ValueError("redis_url is required when redis_required is true")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide immutable settings object."""
    return Settings()
