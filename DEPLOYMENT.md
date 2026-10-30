# Deployment Guide

The supported deployment is the React, FastAPI, and Redis stack defined in
`compose.yaml`.

## Start the production stack

1. Install Docker Engine with the Compose plugin.
2. Copy `.env.example` to `.env`.
3. Set the Data.gov.sg, LTA DataMall, and OneMap credentials.
4. Build and start all services:

```bash
docker compose up --build -d
docker compose ps
```

The application is available on `WEB_PORT` (default `8080`). Nginx serves the
React build, proxies `/api/*` to FastAPI, and provides SPA fallback for
client-side routes. FastAPI and Redis are not published on host ports.

## Services

- `web`: unprivileged Nginx serving the static React build on port 8080.
- `api`: FastAPI/Uvicorn on the internal port 8000.
- `redis`: Redis 7 with AOF persistence in the `redis-data` named volume.

All containers use health checks, read-only root filesystems, temporary `/tmp`
mounts, restart policies, and `no-new-privileges`.

## Health and readiness

- `GET /healthz` verifies Nginx.
- `GET /api/v1/health/live` verifies the API process.
- `GET /api/v1/health/ready` verifies required dependencies.
- `docker compose ps` reports container health.

Redis remains a shared expiring cache, not the permanent source of record. To
stop without deleting cache data, run `docker compose down`. Only use
`docker compose down -v` when cache loss is intentional.

## Configuration and secrets

Provider credentials are API-only environment variables:

- `BACKEND_DATA_GOV_API_KEY`
- `BACKEND_LTA_API_KEY`
- `BACKEND_ONEMAP_EMAIL` and `BACKEND_ONEMAP_EMAIL_PASSWORD`, or
  `BACKEND_ONEMAP_API_KEY`

Key runtime settings include:

- `BACKEND_REDIS_URL`
- `BACKEND_REDIS_REQUIRED`
- `BACKEND_CORS_ORIGINS`
- `BACKEND_HTTP_TIMEOUT_SECONDS`
- `BACKEND_CACHE_TTL_SECONDS`
- `BACKEND_CACHE_STALE_SECONDS`
- `BACKEND_CACHE_TTL_JITTER_RATIO`
- `BACKEND_CACHE_LOCK_SECONDS`

Use a deployment secret manager rather than baking `.env` into an image.
Production traffic is same-origin. CORS accepts explicit development origins
only and never allows `*`.

## Verification

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose exec api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready')"
```

Run the repository test suites before promotion:

```bash
uv sync --all-groups
uv run pytest
docker run --rm -v "${PWD}/frontend:/app" -v /app/node_modules -w /app node:22.20-alpine sh -c "npm ci && npm run lint && npm test && npm run build"
```

## Monitoring and rollback

Monitor provider latency and errors, cache hit rate, stale responses, Redis
memory, and API response time. API cache metadata identifies hits, misses,
degraded Redis access, and stale fallback.

The web and API containers are stateless. Roll back by deploying the previous
image versions; the Redis cache can remain in place because keys are versioned.
