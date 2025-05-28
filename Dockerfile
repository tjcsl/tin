FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 PIPENV_VENV_IN_PROJECT=1

COPY Pipfile .
COPY Pipfile.lock .

RUN apt-get update -y && apt-get install -y --no-install-recommends curl firejail

RUN pip install pipenv && \
  pipenv install --dev

ENV PATH="/.venv/bin:$PATH"

WORKDIR /app
