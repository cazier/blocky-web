FROM python:slim AS base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


FROM base as python_builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.1.12

RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./
RUN poetry lock && poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin


FROM node:slim as npm_builder

WORKDIR /app

COPY package.json package-lock.json webpack.config.js ./
COPY src/static ./src/static
COPY src/templates ./src/templates

RUN npm install && npm run build


FROM base AS app

COPY src ./src
COPY docker-entrypoint.sh ./

COPY --from=python_builder /venv /venv
COPY --from=npm_builder /app/src/static/dist /app/src/static/dist

WORKDIR /config
EXPOSE 80

CMD [ "/app/docker-entrypoint.sh" ]
