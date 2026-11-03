# Online Store

Тестовое задание для стажировки: backend интернет-магазина на Django. На текущем этапе реализован health-check, запуск в Docker и автоматический тест endpoint.

## Стек

- Python 3.12
- Django
- Uvicorn (ASGI)
- PDM
- Docker и Docker Compose

## Требования

- Docker Engine с Docker Compose v2;
- Python 3.12 и PDM — только для локального запуска и тестов без Docker.

## Первоначальная настройка

В корне репозитория создайте локальный файл конфигурации:

```bash
cp .env.example .env
```

Откройте `.env` и замените значение `SECRET_KEY` на новый случайный ключ. Если PDM уже установлен, его можно сгенерировать из папки `backend`:

```bash
pdm run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Значения в `ALLOWED_HOSTS` перечисляются через запятую без пробелов.

## Запуск в Docker

Из корня репозитория соберите и запустите сервис:

```bash
docker compose up --build
```

Health-check доступен по адресу [http://localhost:8080/health](http://localhost:8080/health).

```bash
curl -i http://localhost:8080/health
```

Ожидаемый ответ:

```json
{"status": "ok"}
```

Для запуска в фоне добавьте флаг `-d`:

```bash
docker compose up --build -d
```

Остановка сервисов:

```bash
docker compose down
```

Тесты можно запустить из корня репозитория:

```bash
docker compose run --rm backend pdm run python manage.py test
```

## Локальный запуск

Команды выполняются из папки `backend`:

```bash
pdm sync
pdm run python manage.py runserver
pdm run python manage.py test
```

## Структура проекта

```text
.
├── .env.example             # шаблон локальной конфигурации
├── .gitignore
├── backend/
│   ├── app/                 # Django-приложение и тесты
│   ├── config/              # настройки Django и ASGI-точка входа
│   ├── Dockerfile
│   ├── manage.py
│   ├── pdm.lock
│   └── pyproject.toml
├── docker-compose.yml
└── README.md
```