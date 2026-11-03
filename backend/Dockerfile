FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml pdm.lock ./

RUN pip install pdm --no-cache-dir
RUN pdm sync --prod

COPY . .

EXPOSE 8080

CMD ["pdm", "run", "uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8080"]