ARG PYTHON_VERSION=3.12
ARG PORT=8300

# --- Build stage ---
FROM python:${PYTHON_VERSION}-slim AS builder

ARG PORT

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT}

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# --- Runtime stage ---
FROM python:${PYTHON_VERSION}-slim

ARG PORT

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT} \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system flowdacity && \
    useradd --system --gid flowdacity --uid 1000 --create-home --shell /usr/sbin/nologin flowdacity

COPY --from=builder --chown=flowdacity:flowdacity /app/.venv /app/.venv
COPY --from=builder --chown=flowdacity:flowdacity /app /app

RUN chmod -R a-w /app && \
    chmod -R u+rwX /app

USER flowdacity

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, httpx; port = os.environ.get('PORT', '8300'); r = httpx.get(f'http://127.0.0.1:{port}/metrics/'); raise SystemExit(0 if r.status_code < 400 else 1)"

CMD ["sh", "-c", "exec uvicorn asgi:app --host 0.0.0.0 --port ${PORT}"]