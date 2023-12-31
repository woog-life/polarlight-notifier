FROM python:3.12-slim

RUN useradd --system --create-home --home-dir /app -s /bin/bash app
USER app
ENV PATH=$PATH:/app/.local/bin

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install pipx==1.3.3 --user --no-cache
RUN pipx install poetry==1.7.1

COPY [ "poetry.toml", "poetry.lock", "pyproject.toml", "./" ]

COPY src/polarlight_notifier ./src/polarlight_notifier

RUN poetry install --only main

ARG APP_VERSION
ENV BUILD_SHA=$APP_VERSION

ENTRYPOINT [ "poetry", "run", "python", "-m", "polarlight_notifier.bot" ]
