FROM python:3.13-slim

# uv берём из официального образа, отдельно от Python
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# 1. Сначала зависимости: этот слой кэшируется, пока не изменятся pyproject.toml и uv.lock
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Потом код: меняется часто, пересобирается только он
COPY app ./app
COPY migrations ./migrations

# Версия образа попадает в рантайм и отдаётся на /version
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# --host 0.0.0.0, иначе из контейнера сервис не виден снаружи
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
