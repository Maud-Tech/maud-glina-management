FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY . .
RUN uv sync --no-dev

EXPOSE 8000
