FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml pdm.lock ./

RUN pip install pdm --no-cache-dir
RUN pdm sync --prod

COPY . .

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8080

CMD ["pdm", "run", "uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8080"]