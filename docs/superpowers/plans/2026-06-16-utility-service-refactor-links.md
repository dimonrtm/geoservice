# План Реализации Рефакторинга Связей Utility Service

> **Для агентных исполнителей:** ОБЯЗАТЕЛЬНЫЙ ПОДНАВЫК: используйте `superpowers:subagent-driven-development` (рекомендуется) или `superpowers:executing-plans`, чтобы выполнять этот план по задачам. Шаги используют checkbox-синтаксис (`- [ ]`) для отслеживания.

**Цель:** Восстановить backend после рефакторинга директорий: приложение собирается как `utility_service`, `web_api` не зависит от `infrastructure`, тесты разложены по пакетам, Docker/CI работают с сервисом `utility_service`.

**Архитектура:** `utility_service.web_api` содержит только FastAPI/WebSocket controllers и импортирует зависимости/DTO из `utility_service.use_cases`. `utility_service.use_cases` содержит `deps.py`, application services, Pydantic schemas и может собирать runtime dependencies через `utility_service.infrastructure`. Docker build context становится `apps/backend`, entrypoint становится `utility_service.web_api.main:app`, Compose service/container называется `utility_service`.

**Технологии:** Python 3.12, FastAPI, SQLAlchemy async, Alembic, pytest, black, ruff, Docker Compose, GitHub Actions.

---

## Важное Правило Git

Не выполнять `git add` и `git commit` в ходе реализации, пока пользователь явно не попросит после своей проверки. Все checkpoint-шаги в этом плане означают: остановиться, показать статус и оставить изменения в working tree.

## Структура Файлов

- Изменить: `apps/backend/pyproject.toml` - discovery backend-тестов, настройки ruff/black.
- Создать или изменить: `apps/backend/Dockerfile` - образ для всего пакета `utility_service`.
- Оставить или удалить после миграции: `apps/backend/utility_service/web_api/Dockerfile` - старый узкий Dockerfile не должен использоваться Compose/CI.
- Изменить: `apps/backend/utility_service/web_api/alembic.ini` или перенести в `apps/backend/alembic.ini` - Alembic config должен указывать на migrations в infrastructure.
- Изменить: `apps/backend/utility_service/web_api/main.py` - абсолютные package imports и запуск как `utility_service.web_api.main:app`.
- Перенести/создать: `apps/backend/utility_service/use_cases/deps.py` - dependency-функции, которые импортируют controllers.
- Изменить: `apps/backend/utility_service/web_api/api/*.py` - controllers импортируют deps/schemas/services через `utility_service.use_cases`.
- Изменить: `apps/backend/utility_service/use_cases/**/*.py` - абсолютные imports и отсутствие imports из `web_api`.
- Изменить: `apps/backend/utility_service/infrastructure/**/*.py` - абсолютные imports и отсутствие imports из `web_api`.
- Изменить: `apps/backend/seeds/**/*.py` - imports обновлены под новые package paths.
- Перенести тесты:
  - `apps/backend/utility_service/web_api/tests`
  - `apps/backend/utility_service/use_cases/tests`
  - `apps/backend/utility_service/infrastructure/tests`
  - `apps/backend/seeds/tests`
  - `apps/backend/tests/integration_tests`
- Изменить: `infra/docker-compose.yml` - service `utility_service`, build context `../apps/backend`, command использует package entrypoint.
- Изменить: `infra/docker-compose.override.yml` - то же имя сервиса и build context.
- Изменить: `.github/workflows/ci.yml` - Docker build context, image tags, Compose service name, integration test paths.

## Задача 1: Добавить Тест Архитектурных Границ

**Файлы:**
- Создать: `apps/backend/tests/test_architecture_boundaries.py`

- [ ] **Шаг 1: Написать падающие boundary tests**

Создать `apps/backend/tests/test_architecture_boundaries.py`:

```python
from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = BACKEND_ROOT / "utility_service"


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _violations(root: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for path in _python_files(root):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(BACKEND_ROOT)} imports {module}")
    return violations


def test_web_api_does_not_import_infrastructure() -> None:
    assert _violations(
        PACKAGE_ROOT / "web_api",
        ("utility_service.infrastructure", "infrastructure"),
    ) == []


def test_use_cases_does_not_import_web_api() -> None:
    assert _violations(
        PACKAGE_ROOT / "use_cases",
        ("utility_service.web_api", "web_api", "api"),
    ) == []


def test_infrastructure_does_not_import_web_api() -> None:
    assert _violations(
        PACKAGE_ROOT / "infrastructure",
        ("utility_service.web_api", "web_api", "api"),
    ) == []
```

- [ ] **Шаг 2: Запустить boundary test и подтвердить текущее падение**

Выполнить из `apps/backend`:

```powershell
pytest tests/test_architecture_boundaries.py -q
```

Ожидаемо сейчас: FAIL, пока старые imports используют `api`, `db`, `repositories`, `models` или прямые infrastructure paths из `web_api`.

- [ ] **Шаг 3: Checkpoint**

Не выполнять staging и commit. Показать список падающих imports перед изменением package imports.

## Задача 2: Сделать Backend Package Импортируемым Из `apps/backend`

**Файлы:**
- Изменить: `apps/backend/utility_service/__init__.py`, если отсутствует.
- Создать: `apps/backend/utility_service/use_cases/__init__.py`, если отсутствует.
- Создать: `apps/backend/utility_service/infrastructure/__init__.py`, если отсутствует.
- Создать: `apps/backend/utility_service/infrastructure/postgresql/__init__.py`, если отсутствует.
- Изменить: `apps/backend/pyproject.toml`

- [ ] **Шаг 1: Убедиться, что package markers существуют**

Создать отсутствующие `__init__.py` files с таким содержимым:

```python
"""Utility service package."""
```

Для подпакетов использовать package-specific docstrings:

```python
"""Use case layer for utility_service."""
```

```python
"""Infrastructure layer for utility_service."""
```

```python
"""PostgreSQL infrastructure for utility_service."""
```

- [ ] **Шаг 2: Обновить pytest discovery**

В `apps/backend/pyproject.toml` задать pytest options так, чтобы находились package tests и integration tests:

```toml
[tool.pytest.ini_options]
testpaths = [
    "utility_service/web_api/tests",
    "utility_service/use_cases/tests",
    "utility_service/infrastructure/tests",
    "seeds/tests",
    "tests",
]
addopts = "-q"
```

- [ ] **Шаг 3: Запустить import smoke**

Выполнить из `apps/backend`:

```powershell
python -c "import utility_service; import utility_service.web_api.main; print('utility_service import ok')"
```

Ожидаемо после дальнейших import fixes: печатает `utility_service import ok`. Если сейчас падает из-за старых controller imports, перейти к Задаче 3.

## Задача 3: Перенести Dependency Wiring В `use_cases.deps`

**Файлы:**
- Создать: `apps/backend/utility_service/use_cases/deps.py`
- Изменить: `apps/backend/utility_service/web_api/api/deps.py` или удалить после того, как controllers перестанут его использовать.
- Изменить: `apps/backend/utility_service/web_api/api/auth.py`
- Изменить: `apps/backend/utility_service/web_api/api/layers.py`
- Изменить: `apps/backend/utility_service/web_api/api/utility_network.py`
- Изменить: `apps/backend/utility_service/web_api/api/ws_layers.py`
- Изменить: `apps/backend/utility_service/web_api/api/websocket_auth.py`
- Изменить: `apps/backend/utility_service/web_api/api/lifespan.py`

- [ ] **Шаг 1: Создать use_cases deps с concrete wiring**

Создать `apps/backend/utility_service/use_cases/deps.py` на основе текущей логики из `web_api/api/deps.py`, с абсолютными imports:

```python
from __future__ import annotations

from fastapi import Depends, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.utility_network_repository import (
    UtilityNetworkRepository,
)
from utility_service.infrastructure.postgresql.session import get_session
from utility_service.use_cases.services.auth_service import AuthService
from utility_service.use_cases.services.feature_realtime_publisher import FeatureRealtimePublisher
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.services.layer_service import LayerService
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.services.utility_network_service import UtilityNetworkService


def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_layer_repository(session: AsyncSession = Depends(get_session)) -> LayerRepository:
    return LayerRepository(session)


def get_utility_network_repository(
    session: AsyncSession = Depends(get_session),
) -> UtilityNetworkRepository:
    return UtilityNetworkRepository(session)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repository)


def get_websocket_connection_manager(request: Request) -> WebSocketConnectionManager:
    return request.app.state.websocket_connection_manager


def get_websocket_connection_manager_for_ws(websocket: WebSocket) -> WebSocketConnectionManager:
    return websocket.app.state.websocket_connection_manager


def get_feature_realtime_publisher(
    connection_manager: WebSocketConnectionManager = Depends(get_websocket_connection_manager),
) -> FeatureRealtimePublisher:
    return FeatureRealtimePublisher(connection_manager)


def get_feature_service(
    layer_repository: LayerRepository = Depends(get_layer_repository),
    publisher: FeatureRealtimePublisher = Depends(get_feature_realtime_publisher),
) -> FeatureService:
    return FeatureService(layer_repository, publisher)


def get_layer_service(
    layer_repository: LayerRepository = Depends(get_layer_repository),
) -> LayerService:
    return LayerService(layer_repository)


def get_utility_network_service(
    repository: UtilityNetworkRepository = Depends(get_utility_network_repository),
) -> UtilityNetworkService:
    return UtilityNetworkService(repository)
```

Если constructor names отличаются, скопировать точные constructor calls из текущего `web_api/api/deps.py` и сохранить те же public function names.

- [ ] **Шаг 2: Перевести controllers на imports deps из use_cases**

В каждом `apps/backend/utility_service/web_api/api/*.py` заменить:

```python
from api.deps import get_auth_service
```

на:

```python
from utility_service.use_cases.deps import get_auth_service
```

Для multi-imports использовать явные imports:

```python
from utility_service.use_cases.deps import (
    get_auth_service,
    get_layer_service,
    get_utility_network_service,
    get_websocket_connection_manager_for_ws,
)
```

- [ ] **Шаг 3: Оставить web_api deps только как временную compatibility-прослойку или удалить**

Предпочтительное final state: удалить `apps/backend/utility_service/web_api/api/deps.py` после переноса всех imports.

Если tests временно все еще импортируют его, заменить содержимое compatibility shim только до переноса тестов:

```python
from utility_service.use_cases.deps import *  # noqa: F403
```

Финальная проверка должна показать отсутствие production import из `utility_service.web_api.api.deps`.

- [ ] **Шаг 4: Запустить boundary test**

Выполнить из `apps/backend`:

```powershell
pytest tests/test_architecture_boundaries.py -q
```

Ожидаемо: `test_web_api_does_not_import_infrastructure` проходит или сообщает только remaining direct infrastructure imports, которые нужно исправить в Задаче 4.

## Задача 4: Переписать Imports На Абсолютные `utility_service.*` Paths

**Файлы:**
- Изменить: `apps/backend/utility_service/**/*.py`
- Изменить: `apps/backend/seeds/**/*.py`

- [ ] **Шаг 1: Заменить web_api internal imports**

Пример:

```python
from api.auth import require_editor
```

становится:

```python
from utility_service.web_api.api.auth import require_editor
```

```python
from api.lifespan import lifespan
```

становится:

```python
from utility_service.web_api.api.lifespan import lifespan
```

Внутри одного package `web_api.api` можно использовать package-relative imports, если так понятнее:

```python
from .auth import require_editor
from .websocket_auth import authenticate_websocket_token
```

- [ ] **Шаг 2: Заменить use_cases imports**

Пример:

```python
from schemas.feature_out import FeatureOut
from services.realtime_connection_manager import WebSocketConnectionManager
from domain.exceptions.auth_api_error import AuthApiError
```

становится:

```python
from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
```

Использовать фактические текущие schema paths под `utility_service/use_cases/schemas`.

- [ ] **Шаг 3: Заменить infrastructure imports**

Пример:

```python
from models.user import User
from repositories.layer_repository import LayerRepository
from db.session import SessionFactory
```

становится:

```python
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.infrastructure.postgresql.session import SessionFactory
```

- [ ] **Шаг 4: Заменить domain_services imports**

Если `domain_services` остается отдельным package, imports должны быть явными:

```python
from utility_service.domain_services.bbox import parse_bbox
from utility_service.domain_services.feature_registry import get_layer_feature_model
```

Если `domain_services` переносится в `use_cases.domain`, обновить все references единообразно и запустить все use case tests.

- [ ] **Шаг 5: Заменить seed imports**

Пример:

```python
from models.user import UserRole
from core.passwords import hash_password
```

становится:

```python
from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.utils.passwords import hash_password
```

- [ ] **Шаг 6: Найти старые import roots**

Выполнить из корня репозитория:

```powershell
rg -n "from (api|core|db|domain|models|repositories|schemas|services)\b|import (api|core|db|domain|models|repositories|schemas|services)\b" apps/backend
```

Ожидаемо: нет production matches. Test matches допустимы только если их явно обновляют в Задаче 5.

## Задача 5: Перенести Unit И Integration Tests

**Файлы:**
- Перенести: `apps/backend/tests/test_auth_access.py` -> `apps/backend/utility_service/web_api/tests/test_auth_access.py`
- Перенести: `apps/backend/tests/test_exception_handlers.py` -> `apps/backend/utility_service/web_api/tests/test_exception_handlers.py`
- Перенести: `apps/backend/tests/test_utility_network_api.py` -> `apps/backend/utility_service/web_api/tests/test_utility_network_api.py`
- Перенести: `apps/backend/tests/test_websocket_auth.py` -> `apps/backend/utility_service/web_api/tests/test_websocket_auth.py`
- Перенести: `apps/backend/tests/test_websocket_auth_roles.py` -> `apps/backend/utility_service/web_api/tests/test_websocket_auth_roles.py`
- Перенести: `apps/backend/tests/test_ws_layers.py` -> `apps/backend/utility_service/web_api/tests/test_ws_layers.py`
- Перенести service/schema/domain unit tests в `apps/backend/utility_service/use_cases/tests`.
- Перенести model/repository metadata unit tests в `apps/backend/utility_service/infrastructure/tests`.
- Перенести DB/migration/API integration tests в `apps/backend/tests/integration_tests`.
- Перенести seed unit tests в `apps/backend/seeds/tests`.
- Изменить/создать package-level `conftest.py` files.

- [ ] **Шаг 1: Перенести shared conftest в backend tests support**

Создать `apps/backend/tests/conftest.py` с безопасными env defaults и package path:

```python
import os
from pathlib import Path
import sys


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
)
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
```

Если pytest не загружает этот файл для package tests, добавить идентичный minimal `conftest.py` в каждый package `tests` directory.

- [ ] **Шаг 2: Перенести web_api unit tests**

Перенести tests для controllers, auth dependency behavior, exception handlers, websocket auth и websocket endpoints в:

```text
apps/backend/utility_service/web_api/tests
```

Обновить imports:

```python
from utility_service.web_api.api.auth import create_access_token
from utility_service.use_cases.deps import get_auth_service
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.infrastructure.postgresql.models.user import UserRole
```

- [ ] **Шаг 3: Перенести use_cases unit tests**

Перенести service/schema tests в:

```text
apps/backend/utility_service/use_cases/tests
```

Обновить imports:

```python
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.schemas.feature.create_feature_in import CreateFeatureIn
from utility_service.use_cases.domain.exceptions.version_mismatch_exception import (
    VersionMismatchException,
)
```

- [ ] **Шаг 4: Перенести infrastructure unit tests**

Перенести model metadata и repository tests без внешнего DB requirement в:

```text
apps/backend/utility_service/infrastructure/tests
```

Обновить imports:

```python
from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)
```

- [ ] **Шаг 5: Перенести integration tests**

Перенести DB-dependent tests в:

```text
apps/backend/tests/integration_tests
```

Минимальный набор:

```text
test_network_model_integration.py
test_network_model_migration.py
test_seed_utility_dataset_integration.py
test_utility_network_repository_integration.py
```

Перенести `network_db_support.py` в:

```text
apps/backend/tests/integration_tests/network_db_support.py
```

Обновить imports:

```python
from tests.integration_tests.network_db_support import run_in_rollback_transaction
```

- [ ] **Шаг 6: Перенести seed unit tests**

Перенести seed unit/spec tests в:

```text
apps/backend/seeds/tests
```

Обновить imports:

```python
from seeds.services.seed_demo_user_service import run_seed_demo_users
from seeds.specs.seed_utility_dataset_specs import SEED_UTILITY_DATASET_SPEC
```

- [ ] **Шаг 7: Запустить unit-focused pytest**

Выполнить из `apps/backend`:

```powershell
pytest utility_service/web_api/tests utility_service/use_cases/tests utility_service/infrastructure/tests seeds/tests tests/test_architecture_boundaries.py -q
```

Ожидаемо: все non-DB unit и architecture tests проходят.

## Задача 6: Исправить Alembic Location И Migration Imports

**Файлы:**
- Изменить: `apps/backend/alembic.ini` или `apps/backend/utility_service/web_api/alembic.ini`
- Изменить: `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py`
- При необходимости изменить: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/*.py`

- [ ] **Шаг 1: Положить Alembic config в backend build root**

Предпочтительно создать `apps/backend/alembic.ini`, чтобы Docker command мог выполнять `alembic upgrade head` из `/app`.

Установить:

```ini
[alembic]
script_location = %(here)s/utility_service/infrastructure/postgresql/alembic
prepend_sys_path = .
```

Сохранить существующие logging sections из старого `alembic.ini`.

- [ ] **Шаг 2: Обновить Alembic env imports**

В `apps/backend/utility_service/infrastructure/postgresql/alembic/env.py` заменить model imports на абсолютные package paths:

```python
from utility_service.infrastructure.postgresql.models.base import Base  # noqa: E402
from utility_service.infrastructure.postgresql.models.feature_line import FeatureLine  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.feature_multiline import FeatureMultiLine  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.feature_multipoint import FeatureMultiPoint  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.feature_multipolygon import FeatureMultiPolygon  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.feature_point import FeaturePoint  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.feature_polygon import FeaturePolygon  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.layer import Layer  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.user import User  # noqa: E402, F401
from utility_service.infrastructure.postgresql.models.utility_network import (  # noqa: E402, F401
    AOI,
    AssociationType,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
)
```

- [ ] **Шаг 3: Запустить Alembic smoke**

Выполнить из `apps/backend`:

```powershell
alembic heads
```

Ожидаемо: печатает текущую head revision, включая `d3a01f4e9c21` или текущую head после refactor.

## Задача 7: Обновить Docker Build Для Всего `utility_service`

**Файлы:**
- Создать/изменить: `apps/backend/Dockerfile`
- Изменить: `infra/docker-compose.yml`
- Изменить: `infra/docker-compose.override.yml`

- [ ] **Шаг 1: Создать backend-level Dockerfile**

Создать `apps/backend/Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -U pip

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

FROM base AS deps
COPY utility_service/web_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

FROM deps AS dev
RUN pip install --no-cache-dir ruff black pytest
COPY . /app
EXPOSE 8000

FROM deps AS prod
COPY . /app
EXPOSE 8000
```

- [ ] **Шаг 2: Переименовать Compose service в `utility_service`**

В `infra/docker-compose.yml` заменить service `backend:` на `utility_service:` и установить:

```yaml
  utility_service:
    container_name: utility_service
    build:
      context: ../apps/backend/
      dockerfile: Dockerfile
      target: dev
```

Обновить command:

```yaml
    command:
      [
        "bash",
        "-lc",
        "set -euo pipefail; alembic upgrade head; python -m seeds.runners.seed_demo_users; python -m seeds.runners.seed_utility_dataset; uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000"
      ]
```

Обновить dependent services:

```yaml
    depends_on:
      utility_service:
        condition: service_healthy
```

- [ ] **Шаг 3: Обновить override Compose**

Применить такое же service rename, build context, command и port exposure в `infra/docker-compose.override.yml`.

- [ ] **Шаг 4: Проверить compose config**

Выполнить из `infra`:

```powershell
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml -f docker-compose.override.yml config
```

Ожидаемо: service list содержит `utility_service`, а не `backend`.

## Задача 8: Обновить CI На `utility_service`

**Файлы:**
- Изменить: `.github/workflows/ci.yml`

- [ ] **Шаг 1: Обновить Docker build contexts и image tags**

Заменить:

```yaml
context: ./apps/backend/app
tags: geoservice-backend:dev
```

на:

```yaml
context: ./apps/backend
tags: utility_service:dev
```

Заменить prod tag:

```yaml
tags: utility_service:prod
```

Обновить все `docker run` commands:

```yaml
run: docker run --rm --entrypoint bash utility_service:dev -lc "pytest"
```

- [ ] **Шаг 2: Обновить smoke service names**

Заменить:

```bash
docker compose -f docker-compose.yml up -d --build postgis backend
CID="$(docker compose -f docker-compose.yml ps -q backend)"
docker compose -f docker-compose.yml logs backend --tail=200
docker compose -f docker-compose.yml exec -T backend ...
```

на:

```bash
docker compose -f docker-compose.yml up -d --build postgis utility_service
CID="$(docker compose -f docker-compose.yml ps -q utility_service)"
docker compose -f docker-compose.yml logs utility_service --tail=200
docker compose -f docker-compose.yml exec -T utility_service ...
```

- [ ] **Шаг 3: Обновить integration test paths**

Заменить:

```bash
pytest tests/test_network_model_integration.py -q
```

на:

```bash
pytest tests/integration_tests/test_network_model_integration.py -q
```

То же самое сделать для:

```text
test_network_model_migration.py
test_seed_utility_dataset_integration.py
test_utility_network_repository_integration.py
```

- [ ] **Шаг 4: Найти stale names в CI**

Выполнить:

```powershell
rg -n "apps/backend/app|geoservice-backend|\\bbackend\\b|tests/test_network_model|tests/test_seed_utility_dataset_integration|tests/test_utility_network_repository_integration" .github/workflows/ci.yml infra
```

Ожидаемо: нет stale `apps/backend/app` или `geoservice-backend`. Оставшиеся слова `backend` допустимы только в job names или human labels, если это не references на service/container.

## Задача 9: Запустить Verification Gates

**Файлы:**
- Плановых edits нет, только verification.

- [ ] **Шаг 1: Backend unit и architecture tests**

Выполнить из `apps/backend`:

```powershell
pytest utility_service/web_api/tests utility_service/use_cases/tests utility_service/infrastructure/tests seeds/tests tests/test_architecture_boundaries.py -q
```

Ожидаемо: PASS.

- [ ] **Шаг 2: Backend full pytest без DB opt-in**

Выполнить из `apps/backend`:

```powershell
pytest -q
```

Ожидаемо: PASS, DB integration tests skipped, если `RUN_DB_TESTS=1` не задан.

- [ ] **Шаг 3: Format и lint**

Выполнить из `apps/backend`:

```powershell
black --check .
ruff check .
```

Ожидаемо: обе команды PASS.

- [ ] **Шаг 4: Docker dev/prod build**

Выполнить из корня репозитория:

```powershell
docker build --target dev -t utility_service:dev apps/backend
docker build --target prod -t utility_service:prod apps/backend
```

Ожидаемо: обе сборки завершаются успешно.

- [ ] **Шаг 5: Compose smoke**

Выполнить из `infra`:

```powershell
docker compose -f docker-compose.yml up -d --build postgis utility_service
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec -T utility_service python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
docker compose -f docker-compose.yml down -v
```

Ожидаемо: `utility_service` становится healthy и `/health` печатает `health ok`.

- [ ] **Шаг 6: Frontend unchanged gates**

Выполнить из `apps/frontend`:

```powershell
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Ожидаемо: поведение такое же, как до refactor.

## Задача 10: Обновить Knowledge Docs Только Если Нужно

**Файлы:**
- Возможно изменить: `Code_wiki/архитектура/backend.md`
- Возможно изменить: `Code_wiki/deployment/docker_compose.md`
- Возможно изменить: `Code_wiki/сборка/ci_and_quality.md`
- Возможно изменить: `Code_wiki/правила_и_стиль/testing_strategy.md`

- [ ] **Шаг 1: Решить, нужен ли repository-change ingest**

После implementation и verification ответить:

```text
Создает ли этот refactor durable technical knowledge, которое еще не зафиксировано в code, CI config, Docker config или design/plan?
```

Ожидаемо: да, если Code_wiki все еще говорит `apps/backend/app`, service `backend` или old test layout.

- [ ] **Шаг 2: Если да, выполнить repository-change ingest**

Использовать `.agents/skills/source-command-ingest/SKILL.md` mode `/ingest repository-change`.

Ожидаемо: меняется только `Code_wiki` documentation; code/config/test edits во время ingest не выполняются.

- [ ] **Шаг 3: Если нет, пропустить ingest**

Сообщить:

```text
Repository-change ingest skipped: durable technical knowledge is already captured by code/config/design docs.
```

## Самопроверка

- Покрытие spec: package boundaries покрыты Задачами 1, 3, 4; Docker/Compose/CI - Задачами 7, 8; test layout - Задачей 5; Alembic - Задачей 6; verification - Задачей 9.
- Проверка полноты: незавершенных шагов нет.
- Согласованность типов и путей: runtime entrypoint везде `utility_service.web_api.main:app`; Compose service/container name везде `utility_service`; разрешенный dependency flow везде `web_api -> use_cases -> infrastructure`.
- Git rule: план намеренно не содержит steps с `git add`/`git commit`, потому что repository memory требует явную просьбу пользователя после проверки.
