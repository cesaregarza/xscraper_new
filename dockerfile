###############################
#         Base Image          #
###############################
ARG BASE_IMAGE=python:3.11-slim

FROM $BASE_IMAGE AS base

WORKDIR /app

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1
ENV PATH="$PATH:$POETRY_HOME/bin"

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - 

RUN poetry config virtualenvs.create false

###############################
#    Install  Dependencies    #
###############################
FROM base AS dependencies

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-dev

###############################
#        Build Image          #
###############################
FROM dependencies AS build

ARG BUILD_VERSION
ARG TOKENS
ARG ENV_FILE
ARG SENTRY_DSN

RUN if [ -n "$ENV_FILE" ]; then cp $ENV_FILE .env; fi

COPY . /app/
RUN chmod +x /app/scripts/write_scraper_ini.sh && \
    /app/scripts/write_scraper_ini.sh $TOKENS

ENV SENTRY_DSN=$SENTRY_DSN

# Build the application
RUN poetry version $BUILD_VERSION && \
    poetry build && \
    poetry install && \
    poetry update