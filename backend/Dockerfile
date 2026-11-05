FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml pdm.lock ./

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://pdm-project.org/install-pdm.py | python3 - -v 2.28.0 -p /usr/local \
    && rm -rf /var/lib/apt/lists/*
RUN pdm sync --prod

COPY . .

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8080

CMD ["pdm", "run", "uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8080"]