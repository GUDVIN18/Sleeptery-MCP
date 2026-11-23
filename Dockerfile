FROM ghcr.io/astral-sh/uv:0.10.11 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Зависимости для Git, psycopg2 и asyncpg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . /app

EXPOSE 8800
CMD ["python", "server.py"]