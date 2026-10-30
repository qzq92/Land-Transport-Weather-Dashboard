"""FastAPI application factory and lifespan resource ownership."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import cast

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.cache import AsyncRedis, JsonCache
from backend.routes import router
from backend.services import (
    EnvironmentService,
    LocationService,
    TransitService,
    TransportService,
    WeatherService,
)
from backend.settings import Settings, get_settings
from backend.upstream import UpstreamClient, UpstreamError


@dataclass(frozen=True, slots=True)
class Services:
    """Lifespan-owned domain service registry."""

    locations: LocationService
    weather: WeatherService
    environment: EnvironmentService
    transport: TransportService
    transit: TransitService


def create_app(
    settings: Settings | None = None,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Build an application with resources scoped to its lifespan."""
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        timeout = httpx.Timeout(resolved_settings.http_timeout_seconds)
        limits = httpx.Limits(
            max_connections=resolved_settings.http_max_connections,
            max_keepalive_connections=(
                resolved_settings.http_max_keepalive_connections
            ),
        )
        http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            transport=http_transport,
            headers={"User-Agent": "lta-transport-dashboard-api/1.0"},
        )
        app.state.http_client = http_client
        app.state.redis = None
        app.state.redis_error = None

        redis_client: Redis | None = None
        if resolved_settings.redis_url:
            try:
                candidate = Redis.from_url(
                    resolved_settings.redis_url,
                    socket_connect_timeout=(
                        resolved_settings.redis_timeout_seconds
                    ),
                    socket_timeout=resolved_settings.redis_timeout_seconds,
                )
                await candidate.ping()
                redis_client = candidate
                app.state.redis = candidate
            except (RedisError, OSError, ValueError) as error:
                app.state.redis_error = str(error)
                if "candidate" in locals():
                    await candidate.aclose()

        cache = JsonCache(
            cast(AsyncRedis | None, redis_client),
            resolved_settings,
        )
        upstream = UpstreamClient(http_client)
        app.state.services = Services(
            locations=LocationService(upstream, cache, resolved_settings),
            weather=WeatherService(upstream, cache, resolved_settings),
            environment=EnvironmentService(upstream, cache, resolved_settings),
            transport=TransportService(upstream, cache, resolved_settings),
            transit=TransitService(upstream, cache, resolved_settings),
        )
        try:
            yield
        finally:
            await http_client.aclose()
            if redis_client is not None:
                await redis_client.aclose()

    app = FastAPI(
        title=resolved_settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url=f"{resolved_settings.api_prefix}/docs",
        openapi_url=f"{resolved_settings.api_prefix}/openapi.json",
        redoc_url=None,
    )
    app.state.settings = resolved_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )

    @app.exception_handler(UpstreamError)
    async def handle_upstream_error(
        _request: Request,
        error: UpstreamError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
        )

    app.include_router(router, prefix=resolved_settings.api_prefix)
    return app


app = create_app()
