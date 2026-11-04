# Online Store

Тестовое задание для стажировки: REST API интернет-магазина на Django.

На текущем этапе реализованы health-check, JWT-аутентификация, OpenAPI-документация, PostgreSQL и запуск через Docker Compose.

## Стек

- Python 3.12
- Django и Django REST Framework
- PostgreSQL 16
- JWT (`djangorestframework-simplejwt`)
- OpenAPI/Swagger (`drf-spectacular`)
- PDM
- Docker и Docker Compose

## Требования

- Docker Engine с Docker Compose v2.

Все команды ниже выполняются из корня репозитория. Локальные Python, PDM и PostgreSQL не требуются.

## Первоначальная настройка

Создайте локальный файл конфигурации:

```bash
cp .env.example .env
```

В `.env` замените значения-заглушки `SECRET_KEY` и `POSTGRES_PASSWORD` на случайные секреты. Например, ключ Django можно сгенерировать через Docker:

```bash
docker run --rm python:3.12-alpine python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Файл `.env` содержит секреты и исключён из Git. Значения в `ALLOWED_HOSTS` перечисляются через запятую без пробелов.

## Запуск

Соберите и запустите сервисы:

```bash
docker compose up --build
```

Compose запускает PostgreSQL, ждёт его готовности, затем backend автоматически применяет миграции и запускает Uvicorn.

Для фонового режима используйте:

```bash
docker compose up --build -d
```

Доступные адреса:

- Health-check: [http://localhost:8080/health](http://localhost:8080/health)
- Swagger UI: [http://localhost:8080/api/docs/](http://localhost:8080/api/docs/)
- OpenAPI-схема: [http://localhost:8080/api/schema/](http://localhost:8080/api/schema/)

Проверка health-check:

```bash
curl -i http://localhost:8080/health
```

Остановка сервисов без удаления данных PostgreSQL:

```bash
docker compose down
```

## Тесты

Сначала запустите сервисы в фоне, затем выполните тесты внутри backend-контейнера:

```bash
docker compose up -d --build
docker compose exec backend pdm run python manage.py test
```

Django создаёт отдельную временную тестовую базу PostgreSQL и удаляет её после выполнения.

## API

| Метод | URL | Описание |
| --- | --- | --- |
| `GET` | `/health` | Проверка работоспособности сервиса |
| `POST` | `/api/auth/register/` | Регистрация пользователя |
| `POST` | `/api/auth/login/` | Получение access и refresh JWT |
| `POST` | `/api/auth/refresh/` | Обновление access JWT |
| `GET` | `/api/auth/me/` | Профиль текущего пользователя |

Полная интерактивная документация доступна в Swagger UI.

## Структура проекта

```text
.
├── .env.example             # безопасный шаблон переменных окружения
├── .gitignore
├── backend/
│   ├── app/                 # пользовательская модель, JWT и тесты
│   ├── config/              # настройки Django и главный роутер
│   ├── Dockerfile
│   ├── entrypoint.sh        # автоматическое применение миграций
│   ├── manage.py
│   ├── pdm.lock
│   └── pyproject.toml
├── docker-compose.yml       # backend и PostgreSQL
└── README.md
```