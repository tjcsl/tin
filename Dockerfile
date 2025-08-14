FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 C_FORCE_ROOT=1

COPY pyproject.toml .
COPY uv.lock .

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT="/venv"

RUN apt-get update -y && apt-get install -y --no-install-recommends curl firejail

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --frozen

WORKDIR /app
