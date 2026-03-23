ARG PYTHON_VERSION=3.12
ARG PORT=8080

# --- Build stage ---
FROM python:${PYTHON_VERSION}-slim AS builder

ARG PORT

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT}

WORKDIR /app

# Copy uv from official image for better security and updates
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# --- Runtime stage ---
FROM python:${PYTHON_VERSION}-slim

ARG PORT

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT} \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -s /sbin/nologin appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

COPY --chown=appuser:appuser . .

RUN chmod -R 555 /app/fq_server && \
    chmod 555 /app/*.py && \
    chmod 444 /app/default.conf /app/pyproject.toml

USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, httpx; port = os.environ.get('PORT', '8080'); httpx.get(f'http://127.0.0.1:{port}/metrics/')" || exit 1

ENTRYPOINT ["sh", "-c"]
CMD exec uvicorn asgi:app --host 0.0.0.0 --port ${PORT}
