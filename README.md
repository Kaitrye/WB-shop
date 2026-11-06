# Online Store

Тестовое задание для стажировки: REST API интернет-магазина на Django.

На текущем этапе реализованы health-check, JWT-аутентификация, каталог товаров с административным управлением, корзина, OpenAPI-документация, PostgreSQL и запуск через Docker Compose.

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
docker compose up --build -d --wait
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
docker compose up --build -d --wait
docker compose exec backend pdm run python manage.py test
```

Django создаёт отдельную временную тестовую базу PostgreSQL и удаляет её после выполнения.

## CI

Workflow GitHub Actions запускается при каждом `push` и pull request: собирает Docker-образ, поднимает сервисы, выполняет тесты и проверяет OpenAPI-схему.

## API

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| `GET` | `/health` | все | Проверка работоспособности сервиса |
| `POST` | `/api/auth/register/` | все | Регистрация пользователя |
| `POST` | `/api/auth/login/` | все | Получение access и refresh JWT |
| `POST` | `/api/auth/refresh/` | все | Обновление access JWT |
| `GET` | `/api/auth/me/` | авторизованный пользователь | Профиль текущего пользователя |
| `GET` | `/api/products/` | все | Список активных товаров |
| `POST` | `/api/products/` | администратор | Создание товара |
| `GET` | `/api/products/{id}/` | все | Получение активного товара |
| `PUT` | `/api/products/{id}/` | администратор | Полное обновление товара |
| `PATCH` | `/api/products/{id}/` | администратор | Частичное обновление товара |
| `DELETE` | `/api/products/{id}/` | администратор | Мягкое удаление товара |
| `GET` | `/api/cart/` | авторизованный пользователь | Получение своей корзины |
| `POST` | `/api/cart/items/` | авторизованный пользователь | Добавление товара в корзину |
| `PATCH` | `/api/cart/items/{id}/` | владелец корзины | Установка количества позиции |
| `DELETE` | `/api/cart/items/{id}/` | владелец корзины | Удаление позиции из корзины |

Товар содержит название, описание, цену, остаток и признак активности. Удаление меняет `is_active` на `false`: запись остаётся в базе данных, но товар перестаёт быть доступен через публичный API.

Администратор — пользователь с `is_staff=True`.

При первом обращении к корзине она создаётся автоматически. Повторный `POST` для того же товара увеличивает количество позиции. Нельзя добавить или установить количество выше остатка товара; корзина не резервирует остатки до оформления заказа.

Полная интерактивная документация доступна в Swagger UI.

## Структура проекта

```text
.
├── .env.example             # безопасный шаблон переменных окружения
├── .gitignore
├── backend/
│   ├── users/               # пользовательская модель, JWT и тесты
│   ├── products/            # каталог товаров, API и тесты
│   ├── cart/                # корзина, API и тесты
│   ├── config/              # настройки Django и главный роутер
│   ├── Dockerfile
│   ├── entrypoint.sh        # автоматическое применение миграций
│   ├── manage.py
│   ├── pdm.lock
│   └── pyproject.toml
├── docker-compose.yml       # backend и PostgreSQL
└── README.md
```