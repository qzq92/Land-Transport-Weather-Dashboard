"""Shared API response and validation models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CacheState = Literal[
    "hit",
    "miss",
    "bypass",
    "degraded",
    "stale-if-error",
    "stale-while-locked",
]


class CacheMetadata(BaseModel):
    """Metadata describing how a response was produced."""

    model_config = ConfigDict(extra="forbid")

    state: CacheState
    key: str
    fetched_at: datetime
    age_seconds: float = Field(ge=0)
    stale: bool = False
    redis_degraded: bool = False


class ApiResponse(BaseModel):
    """Stable envelope used by all provider-backed endpoints."""

    model_config = ConfigDict(extra="forbid")

    data: Any
    meta: CacheMetadata


class HealthComponent(BaseModel):
    """Status of one dependency used by readiness checks."""

    status: Literal["up", "down", "disabled", "degraded"]
    detail: str | None = None


class HealthResponse(BaseModel):
    """Health probe response."""

    status: Literal["ok", "not_ready"]
    components: dict[str, HealthComponent] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Partial-success dashboard aggregate."""

    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any]
    errors: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime
