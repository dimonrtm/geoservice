# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -U pip

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

FROM base AS deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

FROM deps AS dev
RUN pip install --no-cache-dir ruff black pytest
COPY . /app
EXPOSE 8000

FROM deps AS prod
COPY . /app
EXPOSE 8000
