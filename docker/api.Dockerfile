FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app backend ./backend
COPY --chown=app:app conf ./conf
COPY --chown=app:app data/lta_camera_id_mapping.csv ./data/lta_camera_id_mapping.csv

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; prefix=os.getenv('BACKEND_API_PREFIX', '/api/v1'); urllib.request.urlopen(f'http://127.0.0.1:8000{prefix}/health/ready', timeout=3)"]

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
