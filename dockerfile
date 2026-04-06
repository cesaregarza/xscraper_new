###############################
#         Base Image          #
###############################
ARG BASE_IMAGE=python:3.11-slim

FROM $BASE_IMAGE AS base

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/app/.venv/bin:$PATH"

###############################
#    Install  Dependencies    #
###############################
FROM base AS dependencies

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

###############################
#        Build Image          #
###############################
FROM dependencies AS build

ARG BUILD_VERSION
ARG TOKENS
ARG SCRAPER_SHARED_CONFIG_B64
ARG ENV_FILE
ARG SENTRY_DSN

RUN if [ -n "$ENV_FILE" ]; then cp $ENV_FILE .env; fi

COPY . /app/
RUN chmod +x /app/scripts/write_scraper_ini.sh && \
    SCRAPER_SHARED_CONFIG_B64="$SCRAPER_SHARED_CONFIG_B64" \
    /app/scripts/write_scraper_ini.sh "$TOKENS"

ENV SENTRY_DSN=$SENTRY_DSN

# Update version in pyproject.toml and install the project into the image
RUN sed -i "s/^version = \".*\"/version = \"${BUILD_VERSION}\"/" pyproject.toml && \
    uv sync --frozen && \
    uv build
