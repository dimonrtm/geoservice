# Дизайн Восстановления Связей Utility Service

Дата: 2026-06-16
Статус: approved

## Цель

После рефакторинга директорий восстановить рабочие связи между backend-файлами так,
чтобы приложение собиралось и запускалось как пакет `utility_service`, а границы
между пакетами были явными.

## Границы Пакетов

`utility_service.web_api` содержит только HTTP/WebSocket входы:

- FastAPI controllers/routers;
- exception handlers;
- websocket endpoints;
- тонкие imports `Depends`-функций из `utility_service.use_cases.deps`;
- imports Pydantic DTO из `utility_service.use_cases.schemas`.

`utility_service.web_api` не импортирует `utility_service.infrastructure`.

`utility_service.use_cases` содержит application слой:

- `deps.py` с функциями dependency wiring для controllers;
- application services;
- Pydantic schemas/DTO;
- domain exceptions и прикладные правила;
- допустимую зависимость на `utility_service.infrastructure`, если dependency-функции
  собирают concrete SQLAlchemy session/repositories/services.

`utility_service.use_cases` не импортирует `utility_service.web_api`.

`utility_service.infrastructure` содержит технические реализации:

- SQLAlchemy session;
- repositories;
- models;
- Alembic migrations;
- DB-specific helpers.

`utility_service.infrastructure` не импортирует `utility_service.web_api`.

## Поток Зависимостей

Разрешенный поток зависимостей:

```text
web_api -> use_cases -> infrastructure
```

Запрещенные связи:

```text
web_api -> infrastructure
use_cases -> web_api
infrastructure -> web_api
```

Контроллеры в `web_api` остаются тонкими. Они получают зависимости так:

```python
from fastapi import Depends
from utility_service.use_cases.deps import get_layer_service
from utility_service.use_cases.schemas.layer import LayerListOut
```

Вся сборка runtime-зависимостей, которая раньше была в `web_api/api/deps.py`,
переносится в `utility_service.use_cases.deps`.

## Сборка И Запуск

Docker и CI должны строить backend из `apps/backend`, чтобы внутрь образа попадал
пакет `utility_service` целиком, а не только подпакет `web_api`.

Docker Compose runtime service/container должен называться `utility_service`, а не
`backend`. CI smoke и локальные Compose-команды должны обращаться к этому сервису
по имени `utility_service`.

Точка входа runtime:

```text
utility_service.web_api.main:app
```

Alembic должен использовать migration directory:

```text
utility_service/infrastructure/postgresql/alembic
```

Compose-команды сохраняют текущий порядок запуска:

```text
alembic upgrade head
python -m seeds.runners.seed_demo_users
python -m seeds.runners.seed_utility_dataset
uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000
```

CI должен сохранить существующие gates: backend format, lint, unit tests, prod image
build, compose smoke, frontend format/lint/typecheck/tests/build.

## Тесты

Unit tests раскладываются по пакетам:

- `apps/backend/utility_service/web_api/tests`;
- `apps/backend/utility_service/use_cases/tests`;
- `apps/backend/utility_service/infrastructure/tests`;
- при необходимости отдельные unit tests для `apps/backend/seeds/tests`.

Integration tests переносятся в:

```text
apps/backend/tests/integration_tests
```

Backend `pytest` должен находить и пакетные unit tests, и integration tests. CI smoke
для DB-dependent проверок должен ссылаться на новые пути integration tests.

## Проверка

Минимальная проверка реализации:

- `black --check .` из backend build context;
- `ruff check .` из backend build context;
- `pytest` из backend build context;
- Docker build dev/prod backend image;
- Compose smoke `postgis + backend`;
- frontend CI-команды без изменения поведения.

## Вне Области Работ

Этот дизайн не требует:

- превращать каждый слой в отдельный installable package;
- переносить FastAPI controllers из `web_api`;
- менять бизнес-поведение API;
- переписывать frontend.
