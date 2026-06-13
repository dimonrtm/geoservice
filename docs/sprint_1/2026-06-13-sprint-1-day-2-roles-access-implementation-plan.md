# План Реализации Ролей И Доступа Дня 2 Спринта 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить legacy-модель `Viewer`/`Editor` на строгие роли `Editor`/`Reviewer`, проверять актуального активного пользователя через БД, создать трех стабильных demo users и не показывать reviewer editor workspace.

**Architecture:** Backend сохраняет одну enum-роль в `users`, а все HTTP guards получают актуальный `User` через async dependency и не доверяют роли из JWT как source of truth. Миграция удаляет известные legacy demo accounts и `Viewer`, меняет CHECK constraint и добавляет `is_active`; frontend использует общий role helper и отдельный reviewer placeholder. `WorkOrder` assignment guard, reviewer queue, approve/reject и `post` остаются точками интеграции следующих дней.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL/PostGIS, Pydantic 2, pytest, Vue 3, Pinia, TypeScript, Vitest, Docker Compose.

---

## Предусловие Исполнения

- Работать в текущей ветке и текущей рабочей копии.
- Не создавать worktree или отдельную ветку.
- Все операции Git должны быть только read-only: `git diff`, `git diff --cached`
  и `git status --short`.
- Не менять и не снимать уже существующие staged-изменения пользователя.
- Не удалять и не ослаблять jobs или проверки в `.github/workflows/ci.yml`.
- Сохранить работоспособность существующих backend/frontend Docker targets,
  `infra/docker-compose.yml`, `infra/docker-compose.override.yml`,
  `infra/ci-up.cmd` и `infra/dev-up.cmd`.
- Отдельного CD workflow в репозитории сейчас нет. Deployment-контракт этой
  задачи — существующие Docker image builds и локальные Compose-сценарии
  `backend`, `dev` и `prod`; пустой `infra/docker-compose.full.yml` не является
  активным сценарием развертывания.

## Граница Scope

Этот план реализует только День 2:

- роли `editor | reviewer`;
- DB-backed HTTP authentication и `require_editor`/`require_reviewer`;
- active-user guard и структурированные auth errors;
- доступ обеих ролей к read-only realtime;
- стабильный seed трех demo users;
- frontend role contract и reviewer placeholder;
- удаление legacy `Viewer` из активного кода и документации запуска.

Не реализуются:

- `WorkOrder`, assignment guard и `WORK_ORDER_NOT_ASSIGNED`;
- reviewer queue;
- approve/reject и `post`;
- audit storage;
- production user administration.

Day 2 design заменяет решение Дня 1 о generic `Viewer`, но не переносит в этот
день сущности следующих vertical backlog items.

## Карта Файлов

**Backend-модель и миграция**

- Modify: `apps/backend/app/models/user.py`
- Create: `apps/backend/app/alembic/versions/b82a5f2d91c3_editor_reviewer_roles.py`
- Create: `apps/backend/app/tests/test_user_role_model.py`

**Backend auth и ошибки**

- Create: `apps/backend/app/domain/exceptions/auth_api_error.py`
- Modify: `apps/backend/app/api/exception_handlers.py`
- Modify: `apps/backend/app/api/auth.py`
- Modify: `apps/backend/app/api/layers.py`
- Modify: `apps/backend/app/api/secure_router.py`
- Modify: `apps/backend/app/services/auth_service.py`
- Modify: `apps/backend/app/schemas/auth_user_out.py`
- Modify: `apps/backend/app/schemas/dev_login_in.py`
- Create: `apps/backend/app/tests/test_auth_access.py`
- Modify: `apps/backend/app/tests/test_auth_service.py`

**Demo seed**

- Modify: `apps/backend/app/repositories/user_repository.py`
- Modify: `apps/backend/app/services/demo_user_seed_service.py`
- Modify: `apps/backend/app/tests/test_demo_user_seed_service.py`

**Realtime**

- Modify: `apps/backend/app/api/websocket_auth.py`
- Modify: `apps/backend/app/tests/test_websocket_auth.py`
- Modify: `apps/backend/app/tests/test_websocket_auth_roles.py`
- Modify: `apps/backend/app/tests/test_ws_layers.py`
- Modify: `apps/backend/app/tests/test_realtime_connection_manager.py`

**Frontend**

- Modify: `apps/frontend/src/api/auth.ts`
- Create: `apps/frontend/src/domain/authRole.ts`
- Create: `apps/frontend/src/domain/authRole.test.ts`
- Create: `apps/frontend/src/components/ReviewerHome.vue`
- Modify: `apps/frontend/src/App.vue`
- Modify: `apps/frontend/src/stores/auth.test.ts`

**Документация**

- Modify: `README.md`
- Modify: `docs/sprint_1/README.md`
- Update through `/ingest repository-change`: `Code_wiki/dev_setup/local_development.md`
- Update through `/ingest repository-change`: `Code_wiki/сборка/ci_and_quality.md`
- Update through `/ingest repository-change`: `Code_wiki/deployment/docker_compose.md`

### Задача 0: Зафиксировать Deployment Baseline До Изменений

**Files:**

- Verify unchanged: `.github/workflows/ci.yml`
- Verify unchanged: `apps/backend/app/Dockerfile`
- Verify unchanged: `apps/frontend/Dockerfile`
- Verify unchanged: `infra/docker-compose.yml`
- Verify unchanged: `infra/docker-compose.override.yml`
- Verify unchanged: `infra/ci-up.cmd`
- Verify unchanged: `infra/dev-up.cmd`

- [ ] **Шаг 1: Проверить синтаксис действующих Compose-конфигураций**

Из `infra`:

```powershell
docker compose -f docker-compose.yml config --quiet
docker compose config --quiet
docker compose --profile dev config --quiet
docker compose --profile prod config --quiet
```

Ожидается: все команды завершаются с кодом `0`.

- [ ] **Шаг 2: Создать legacy volume для проверки обновления**

Из `infra`:

```powershell
docker compose -f docker-compose.yml down -v
docker compose -f docker-compose.yml up -d --build postgis backend
docker compose -f docker-compose.yml exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
docker compose -f docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT email, role FROM users ORDER BY email;"
docker compose -f docker-compose.yml stop backend
```

Ожидается: backend healthy; в legacy volume присутствуют
`editor@example.com` и `viewer@example.com`; `postgis` и volume остаются для
upgrade smoke следующих задач.

- [ ] **Шаг 3: Зафиксировать исходные Git и CI поверхности**

```powershell
git status --short
git diff --cached --stat
```

Ожидается: команды только читают состояние; существующий staging не меняется.

### Задача 1: Заменить Хранимую Модель Ролей

**Files:**

- Create: `apps/backend/app/tests/test_user_role_model.py`
- Modify: `apps/backend/app/models/user.py`
- Create: `apps/backend/app/alembic/versions/b82a5f2d91c3_editor_reviewer_roles.py`

- [ ] **Шаг 1: Написать падающий тест модели ролей**

```python
from models.user import User, UserRole


def test_user_role_contains_only_editor_and_reviewer() -> None:
    assert {role.value for role in UserRole} == {"editor", "reviewer"}


def test_user_is_active_by_default() -> None:
    assert User.__table__.c.is_active.default.arg is True
```

- [ ] **Шаг 2: Запустить целевой тест и подтвердить падение**

Запустить из `apps/backend/app`:

```powershell
pytest tests/test_user_role_model.py -q
```

Ожидается: FAIL, потому что `UserRole.REVIEWER` и `User.is_active` отсутствуют.

- [ ] **Шаг 3: Реализовать строгую модель**

Изменить `UserRole` и добавить `is_active` в `models/user.py`:

```python
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func


class UserRole(str, enum.Enum):
    EDITOR = "editor"
    REVIEWER = "reviewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            length=16,
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

- [ ] **Шаг 4: Добавить миграцию**

Создать `b82a5f2d91c3_editor_reviewer_roles.py`:

```python
"""replace viewer with reviewer

Downgrade removes reviewer demo accounts because the legacy role set cannot
represent them safely.

Revision ID: b82a5f2d91c3
Revises: c6cef6320f1d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b82a5f2d91c3"
down_revision: Union[str, Sequence[str], None] = "c6cef6320f1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM users
            WHERE role = 'viewer'
               OR email IN ('editor@example.com', 'viewer@example.com')
            """
        )
    )
    op.drop_constraint("user_role", "users", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('editor', 'reviewer')",
    )
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM users WHERE role = 'reviewer'"))
    op.drop_constraint("user_role", "users", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('viewer', 'editor')",
    )
    op.drop_column("users", "is_active")
```

`downgrade` намеренно удаляет reviewer demo accounts; это ограничение должно
быть явно указано в docstring миграции.

- [ ] **Шаг 5: Запустить тесты модели и migration smoke**

```powershell
pytest tests/test_user_role_model.py -q
```

Ожидается: `2 passed`.

Из корня репозитория:

```powershell
docker compose -f infra/docker-compose.yml --profile migrate up --build --abort-on-container-exit migrate
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users' AND column_name='is_active';"
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='users'::regclass AND conname='user_role';"
```

Ожидается: `is_active | boolean`; constraint содержит `editor` и `reviewer`,
но не содержит `viewer`.

- [ ] **Шаг 6: Проверить локальный diff без изменения staging**

```powershell
git diff -- apps/backend/app/models/user.py apps/backend/app/alembic/versions/b82a5f2d91c3_editor_reviewer_roles.py apps/backend/app/tests/test_user_role_model.py
git status --short
```

Ожидается: diff содержит только изменения модели, миграции и тестов задачи;
Git index не изменён.

### Задача 2: Добавить DB-Backed HTTP Authentication И Role Guards

**Files:**

- Create: `apps/backend/app/domain/exceptions/auth_api_error.py`
- Modify: `apps/backend/app/api/exception_handlers.py`
- Modify: `apps/backend/app/api/auth.py`
- Modify: `apps/backend/app/api/layers.py`
- Modify: `apps/backend/app/api/secure_router.py`
- Modify: `apps/backend/app/services/auth_service.py`
- Modify: `apps/backend/app/schemas/auth_user_out.py`
- Modify: `apps/backend/app/schemas/dev_login_in.py`
- Create: `apps/backend/app/tests/test_auth_access.py`
- Modify: `apps/backend/app/tests/test_auth_service.py`

- [ ] **Шаг 1: Написать падающие тесты dependency и service**

Создать `tests/test_auth_access.py`:

```python
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from api.auth import create_access_token, get_current_user, require_editor, require_reviewer
from api.deps import get_auth_service
from api.exception_handlers import install_exception_handlers
from api.secure_router import secure_router
from domain.exceptions.auth_api_error import AuthApiError
from models.user import UserRole


def credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_uses_current_database_role() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    current_user = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        is_active=True,
    )
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = current_user

    result = asyncio.run(get_current_user(credentials(token), auth_service))

    assert result is current_user


def test_get_current_user_rejects_legacy_viewer_token() -> None:
    token = create_access_token(str(uuid4()), "viewer")

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(get_current_user(credentials(token), AsyncMock()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "AUTH_REQUIRED"


def test_get_current_user_rejects_inactive_user() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        role=SimpleNamespace(value="editor"),
        is_active=False,
    )

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(get_current_user(credentials(token), auth_service))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"


def test_role_guards_are_mutually_exclusive() -> None:
    editor = SimpleNamespace(role=UserRole.EDITOR)
    reviewer = SimpleNamespace(role=UserRole.REVIEWER)

    assert require_editor(editor) is editor
    assert require_reviewer(reviewer) is reviewer

    with pytest.raises(AuthApiError):
        require_editor(reviewer)
    with pytest.raises(AuthApiError):
        require_reviewer(editor)


def test_reviewer_gets_structured_403_from_editor_endpoint() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "reviewer")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(secure_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    response = TestClient(app).post(
        "/api/v1/secure/ping",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    assert response.json()["message"] == (
        "Операция доступна только пользователю с ролью Editor."
    )
```

Add to `test_auth_service.py`:

```python
def test_authenticate_user_rejects_inactive_user() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        password_hash=hash_password("marina-reviewer-password"),
        is_active=False,
    )
    repository = AsyncMock()
    repository.get_by_email.return_value = user
    service = AuthService(session=None, user_repository=repository)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(
            service.authenticate_user(
                "marina.reviewer@example.local",
                "marina-reviewer-password",
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"
```

- [ ] **Шаг 2: Запустить целевые тесты и подтвердить падение**

```powershell
pytest tests/test_auth_access.py tests/test_auth_service.py -q
```

Ожидается: FAIL, потому что `AuthApiError`, `require_reviewer`, active-user
checks и DB-backed `get_current_user` отсутствуют.

- [ ] **Шаг 3: Добавить структурированную auth exception**

Создать `domain/exceptions/auth_api_error.py`:

```python
class AuthApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
```

Register it in `api/exception_handlers.py`:

```python
from uuid import uuid4

from domain.exceptions.auth_api_error import AuthApiError


@app.exception_handler(AuthApiError)
async def auth_api_error(request: Request, error: AuthApiError):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": error.code,
            "message": error.message,
            "correlationId": correlation_id,
            "details": {},
        },
    )
```

Place the handler inside `install_exception_handlers`.

- [ ] **Шаг 4: Сделать `get_current_user` асинхронным и DB-backed**

In `api/auth.py`, import `User`, `UserRole`, `AuthApiError`, and change the
dependencies:

```python
SUPPORTED_AUTH_ROLES = {role.value for role in UserRole}


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if cred is None or not cred.credentials:
        raise AuthApiError(401, "AUTH_REQUIRED", "Требуется вход в систему.")

    try:
        payload = decode_token(cred.credentials)
    except HTTPException as exc:
        raise AuthApiError(
            401,
            "AUTH_REQUIRED",
            "Сессия недействительна.",
        ) from exc

    token_role = payload.get("role")
    if "sub" not in payload or token_role not in SUPPORTED_AUTH_ROLES:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError as exc:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.") from exc

    current_user = await auth_service.get_user_by_id(user_id)
    if current_user is None:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")
    if not current_user.is_active:
        raise AuthApiError(403, "USER_INACTIVE", "Учетная запись отключена.")
    return current_user


def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.EDITOR:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Editor.",
        )
    return user


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.REVIEWER:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Reviewer.",
        )
    return user
```

- [ ] **Шаг 5: Обновить consumers и response schemas**

In `secure_router.py`, use model fields:

```python
@secure_router.get("/ping")
async def ping(user: User = Depends(get_current_user)) -> dict:
    return {"status": "ok", "user_id": str(user.id), "role": user.role.value}
```

Применить такое же изменение к `ping_write`.

In `layers.py`, remove the redundant `user.get("role")` branch from
`get_layer_features_from_bbox`; the router-level `get_current_user` dependency
already authorizes both active roles.

Изменить `AuthUserOut.role`:

```python
role: Literal["editor", "reviewer"]
```

Задать строгий default в `DevLoginIn`:

```python
class DevLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    role: UserRole = UserRole.EDITOR
```

Remove the permissive validator that silently converted unknown roles to
`Viewer`.

- [ ] **Шаг 6: Отклонять inactive login в `AuthService`**

После проверки пароля:

```python
if not user.is_active:
    raise AuthApiError(
        status_code=status.HTTP_403_FORBIDDEN,
        code="USER_INACTIVE",
        message="Учетная запись отключена.",
    )
```

Добавить `is_active=True` в существующие auth-service fixtures и заменить
legacy viewer examples на reviewer examples.

- [ ] **Шаг 7: Запустить целевые и все backend tests**

```powershell
pytest tests/test_auth_access.py tests/test_auth_service.py tests/test_exception_handlers.py -q
pytest -q
```

Ожидается: целевые тесты и полный backend suite проходят.

- [ ] **Шаг 8: Проверить локальный diff без изменения staging**

```powershell
git diff -- apps/backend/app/domain/exceptions/auth_api_error.py apps/backend/app/api/exception_handlers.py apps/backend/app/api/auth.py apps/backend/app/api/layers.py apps/backend/app/api/secure_router.py apps/backend/app/services/auth_service.py apps/backend/app/schemas/auth_user_out.py apps/backend/app/schemas/dev_login_in.py apps/backend/app/tests/test_auth_access.py apps/backend/app/tests/test_auth_service.py
git status --short
```

Ожидается: diff содержит только auth-контракт, guards, обработку ошибок и их
тесты; Git index не изменён.

### Задача 3: Создать Трех Стабильных Demo Users

**Files:**

- Modify: `apps/backend/app/repositories/user_repository.py`
- Modify: `apps/backend/app/services/demo_user_seed_service.py`
- Modify: `apps/backend/app/tests/test_demo_user_seed_service.py`
- Reuse unchanged entrypoint: `apps/backend/app/seed_demo_users.py`
- Reuse unchanged startup integration: `infra/docker-compose.yml`

Не создавать новый seed script, CLI или отдельный механизм загрузки demo users.
Расширить существующую цепочку
`seed_demo_users.py -> run_demo_user_seed() -> DemoUserSeedService`.

- [ ] **Шаг 1: Заменить seed tests контрактом трех пользователей**

Тест должен проверять эти точные specs:

```python
EXPECTED_DEMO_USERS = {
    "alexey.editor@example.local": UserRole.EDITOR,
    "bolat.editor@example.local": UserRole.EDITOR,
    "marina.reviewer@example.local": UserRole.REVIEWER,
}


def test_demo_user_specs_define_three_stable_users() -> None:
    assert {spec.email: spec.role for spec in DEMO_USER_SPECS} == EXPECTED_DEMO_USERS
    assert len({spec.id for spec in DEMO_USER_SPECS}) == 3
```

Обновить create/update/idempotence tests на три вызова/пользователя и добавить:

```python
def test_seed_restores_reviewer_role_and_password() -> None:
    session = FakeSession()
    marina = SimpleNamespace(
        id=DEMO_USER_SPECS[2].id,
        email="marina.reviewer@example.local",
        role=UserRole.EDITOR,
        password_hash=None,
    )
    repository = AsyncMock()
    repository.get_by_email.side_effect = [
        SimpleNamespace(
            id=DEMO_USER_SPECS[0].id,
            email=DEMO_USER_SPECS[0].email,
            role=DEMO_USER_SPECS[0].role,
            password_hash=hash_password(DEMO_USER_SPECS[0].password),
        ),
        SimpleNamespace(
            id=DEMO_USER_SPECS[1].id,
            email=DEMO_USER_SPECS[1].email,
            role=DEMO_USER_SPECS[1].role,
            password_hash=hash_password(DEMO_USER_SPECS[1].password),
        ),
        marina,
    ]

    users = asyncio.run(DemoUserSeedService(session, repository).ensure_demo_users())

    assert users[-1] is marina
    assert marina.role is UserRole.REVIEWER
    assert verify_password("marina-reviewer-password", marina.password_hash)
```

- [ ] **Шаг 2: Запустить seed tests и подтвердить падение**

```powershell
pytest tests/test_demo_user_seed_service.py -q
```

Ожидается: FAIL, потому что текущий seed определяет двух generic users и не
имеет стабильных IDs.

- [ ] **Шаг 3: Добавить стабильные IDs и credentials**

Extend `DemoUserSpec`:

```python
from uuid import UUID


@dataclass(frozen=True)
class DemoUserSpec:
    id: UUID
    email: str
    password: str
    role: UserRole
```

Use:

```python
DEMO_USER_SPECS = (
    DemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000001"),
        email="alexey.editor@example.local",
        password="alexey-editor-password",
        role=UserRole.EDITOR,
    ),
    DemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000002"),
        email="bolat.editor@example.local",
        password="bolat-editor-password",
        role=UserRole.EDITOR,
    ),
    DemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000003"),
        email="marina.reviewer@example.local",
        password="marina-reviewer-password",
        role=UserRole.REVIEWER,
    ),
)
```

- [ ] **Шаг 4: Разрешить repository создавать пользователя с явным ID**

Изменить сигнатуру repository:

```python
async def create_user(
    self,
    email: str,
    role: UserRole,
    password_hash: str | None = None,
    user_id: UUID | None = None,
) -> User:
    values = {
        "email": email,
        "role": role,
        "password_hash": password_hash,
    }
    if user_id is not None:
        values["id"] = user_id

    stmt = insert(User).values(**values).returning(User)
    result = await self.session.execute(stmt)
    return result.scalar_one()
```

Pass `user_id=spec.id` from `DemoUserSeedService` when creating a missing user.
Do not rewrite an existing primary key during idempotent repair.

- [ ] **Шаг 5: Запустить backend tests и обновить сохранённый deployment**

```powershell
pytest tests/test_demo_user_seed_service.py -q
pytest -q
```

Из `infra`:

```powershell
docker compose -f docker-compose.yml up -d --build backend
docker compose -f docker-compose.yml exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
docker compose -f docker-compose.yml exec -T backend python seed_demo_users.py
docker compose -f docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT id, email, role, is_active FROM users ORDER BY email;"
```

Ожидается: все тесты проходят; существующий deployment обновляется поверх
legacy volume; `seed_demo_users.py` использует обновлённый
`DemoUserSeedService`; в БД ровно три целевых demo users без legacy `Viewer`.

- [ ] **Шаг 6: Проверить локальный diff без изменения staging**

```powershell
git diff -- apps/backend/app/repositories/user_repository.py apps/backend/app/services/demo_user_seed_service.py apps/backend/app/tests/test_demo_user_seed_service.py
git status --short
```

Ожидается: новый seed-механизм не создан; изменены только существующие
repository, service и tests; Git index не изменён.

### Задача 4: Разрешить Realtime-Чтение Для Editor И Reviewer

**Files:**

- Modify: `apps/backend/app/api/websocket_auth.py`
- Modify: `apps/backend/app/tests/test_websocket_auth.py`
- Modify: `apps/backend/app/tests/test_websocket_auth_roles.py`
- Modify: `apps/backend/app/tests/test_ws_layers.py`
- Modify: `apps/backend/app/tests/test_realtime_connection_manager.py`

- [ ] **Шаг 1: Перевести tests на новый набор ролей**

Заменить authorized parametrization на:

```python
@pytest.mark.parametrize("role", ["editor", "reviewer"])
```

Add an inactive-user test:

```python
def test_authenticate_websocket_token_rejects_inactive_user() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "reviewer")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        is_active=False,
    )

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token(token, auth_service))

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Учетная запись отключена."
```

Добавить `is_active=True` во все fixtures активных пользователей. Сохранить
один явный тест legacy-токена `viewer` с ожидаемым policy violation.

- [ ] **Шаг 2: Запустить realtime tests и подтвердить падение**

```powershell
pytest tests/test_websocket_auth.py tests/test_websocket_auth_roles.py tests/test_ws_layers.py tests/test_realtime_connection_manager.py -q
```

Ожидается: FAIL, потому что reviewer не авторизован, а inactive users не
проверяются.

- [ ] **Шаг 3: Реализовать realtime role policy**

In `api/websocket_auth.py`:

```python
ALLOWED_REALTIME_ROLES = {"editor", "reviewer"}
```

После загрузки пользователя:

```python
if not current_user.is_active:
    raise _websocket_auth_error("Учетная запись отключена.")

if current_user.role.value not in ALLOWED_REALTIME_ROLES:
    raise _websocket_auth_error(
        "Подписка на realtime недоступна для этой роли."
    )
```

Актуальная роль из БД остается authoritative; `WebSocketUserContext` нельзя
строить из роли JWT.

- [ ] **Шаг 4: Запустить realtime и backend suites**

```powershell
pytest tests/test_websocket_auth.py tests/test_websocket_auth_roles.py tests/test_ws_layers.py tests/test_realtime_connection_manager.py -q
pytest -q
```

Ожидается: все тесты проходят.

- [ ] **Шаг 5: Проверить локальный diff без изменения staging**

```powershell
git diff -- apps/backend/app/api/websocket_auth.py apps/backend/app/tests/test_websocket_auth.py apps/backend/app/tests/test_websocket_auth_roles.py apps/backend/app/tests/test_ws_layers.py apps/backend/app/tests/test_realtime_connection_manager.py
git status --short
```

Ожидается: diff ограничен realtime-auth и тестами; Git index не изменён.

### Задача 5: Обновить Frontend-Контракт Ролей

**Files:**

- Modify: `apps/frontend/src/api/auth.ts`
- Create: `apps/frontend/src/domain/authRole.ts`
- Create: `apps/frontend/src/domain/authRole.test.ts`
- Create: `apps/frontend/src/components/ReviewerHome.vue`
- Modify: `apps/frontend/src/App.vue`
- Modify: `apps/frontend/src/stores/auth.test.ts`

- [ ] **Шаг 1: Написать падающие тесты role helper**

Создать `domain/authRole.test.ts`:

```typescript
import { describe, expect, it } from "vitest";

import { getRoleLabel, isEditorRole } from "@/domain/authRole";

describe("auth role", () => {
  it("returns Russian labels for both workflow roles", () => {
    expect(getRoleLabel("editor")).toBe("Редактор");
    expect(getRoleLabel("reviewer")).toBe("Рецензент");
  });

  it("allows editor workspace only for Editor", () => {
    expect(isEditorRole("editor")).toBe(true);
    expect(isEditorRole("reviewer")).toBe(false);
  });
});
```

Изменить restore-session test в `stores/auth.test.ts`, чтобы он возвращал:

```typescript
user: {
  id: "user-2",
  email: "marina.reviewer@example.local",
  role: "reviewer",
}
```

- [ ] **Шаг 2: Запустить frontend tests и подтвердить падение**

Запустить из `apps/frontend`:

```powershell
npm test -- src/domain/authRole.test.ts src/stores/auth.test.ts
```

Ожидается: FAIL, потому что helper отсутствует, а `AuthRole` отклоняет
`reviewer`.

- [ ] **Шаг 3: Реализовать role type и helper**

In `api/auth.ts`:

```typescript
export type AuthRole = "editor" | "reviewer";
```

Создать `domain/authRole.ts`:

```typescript
import type { AuthRole } from "@/api/auth";

const ROLE_LABELS: Record<AuthRole, string> = {
  editor: "Редактор",
  reviewer: "Рецензент",
};

export function getRoleLabel(role: AuthRole): string {
  return ROLE_LABELS[role];
}

export function isEditorRole(role: AuthRole): boolean {
  return role === "editor";
}
```

- [ ] **Шаг 4: Добавить reviewer placeholder**

Создать `components/ReviewerHome.vue`:

```vue
<template>
  <section class="reviewerHome">
    <h1>Проверка изменений</h1>
    <p>
      Роль Reviewer активна. Очередь версий для проверки будет добавлена в
      следующем спринте.
    </p>
  </section>
</template>

<style scoped>
.reviewerHome {
  max-width: 720px;
  margin: 48px auto;
  padding: 24px;
  color: #0f172a;
}
</style>
```

In `App.vue`:

```typescript
import ReviewerHome from "./components/ReviewerHome.vue";
import { getRoleLabel, isEditorRole } from "@/domain/authRole";

const userLabel = computed(() => {
  if (!auth.user) {
    return "";
  }
  return `${auth.user.email} (${getRoleLabel(auth.user.role)})`;
});

const showEditorWorkspace = computed(
  () => auth.user !== null && isEditorRole(auth.user.role),
);
```

Заменить безусловный вывод карты:

```vue
<MapPageView v-if="showEditorWorkspace" class="mapSlot" />
<ReviewerHome v-else />
```

- [ ] **Шаг 5: Запустить frontend quality gates**

```powershell
npm test
npm run typecheck
npm run lint
npm run format:check
npm run build
```

Ожидается: все команды проходят.

- [ ] **Шаг 6: Проверить локальный diff без изменения staging**

```powershell
git diff -- apps/frontend/src/api/auth.ts apps/frontend/src/domain/authRole.ts apps/frontend/src/domain/authRole.test.ts apps/frontend/src/components/ReviewerHome.vue apps/frontend/src/App.vue apps/frontend/src/stores/auth.test.ts
git status --short
```

Ожидается: diff ограничен frontend role contract и reviewer placeholder; Git
index не изменён.

### Задача 6: Обновить Demo-Документацию И Выполнить End-To-End Проверку

**Files:**

- Modify: `README.md`
- Modify: `docs/sprint_1/README.md`
- Update through `/ingest repository-change`: `Code_wiki/dev_setup/local_development.md`
- Update through `/ingest repository-change`: `Code_wiki/сборка/ci_and_quality.md`
- Update through `/ingest repository-change`: `Code_wiki/deployment/docker_compose.md`

- [ ] **Шаг 1: Обновить demo credentials в `README.md`**

Заменить generic users на:

```text
alexey.editor@example.local / alexey-editor-password
bolat.editor@example.local / bolat-editor-password
marina.reviewer@example.local / marina-reviewer-password
```

Document:

- `Editor` sees the existing map/editor foundation;
- `Reviewer` sees the reviewer placeholder;
- old `viewer@example.com` credentials are intentionally removed;
- restarting backend reruns the idempotent seed.

- [ ] **Шаг 2: Добавить план в индекс Спринта 1**

Add to `docs/sprint_1/README.md`:

```markdown
- [План реализации ролей и доступа Дня 2](2026-06-13-sprint-1-day-2-roles-access-implementation-plan.md)
```

- [ ] **Шаг 3: Повторить backend jobs из текущего CI**

Из корня репозитория:

```powershell
docker build --target dev -t geoservice-backend:dev apps/backend/app
docker run --rm --entrypoint bash geoservice-backend:dev -lc "black --check ."
docker run --rm --entrypoint bash geoservice-backend:dev -lc "ruff check ."
docker run --rm --entrypoint bash geoservice-backend:dev -lc "pytest"
docker build --target prod -t geoservice-backend:prod apps/backend/app
```

Ожидается: эквиваленты jobs `backend_format`, `backend_lint`, `backend_test` и
`backend_build_prod` из `.github/workflows/ci.yml` проходят без изменения
workflow.

- [ ] **Шаг 4: Повторить frontend jobs из текущего CI**

Из `apps/frontend`:

```powershell
npm ci
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Из корня репозитория:

```powershell
docker build --target prod -t geoservice-frontend:prod apps/frontend
```

Ожидается: эквиваленты jobs `frontend_format_check`, `frontend_lint`,
`frontend_typecheck`, `frontend_test` и `frontend_build` проходят; production
nginx image также собирается.

- [ ] **Шаг 5: Проверить все действующие Compose-конфигурации**

Из `infra`:

```powershell
docker compose -f docker-compose.yml config --quiet
docker compose config --quiet
docker compose --profile dev config --quiet
docker compose --profile prod config --quiet
```

Ожидается: base, base+override, dev profile и prod profile валидны.

- [ ] **Шаг 6: Повторить Compose smoke из текущего CI**

Из `infra`:

```powershell
docker compose -f docker-compose.yml down -v
docker compose -f docker-compose.yml up -d --build postgis backend
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
```

Ожидается: эквивалент job `smoke_test` проходит, backend становится healthy.

Проверить logins внутри container, где base Compose предоставляет API:

```powershell
docker compose -f docker-compose.yml exec -T backend python -c "import json, urllib.request; users=[('alexey.editor@example.local','alexey-editor-password'),('bolat.editor@example.local','bolat-editor-password'),('marina.reviewer@example.local','marina-reviewer-password')]; print([json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=json.dumps({'email': email, 'password': password}).encode(), headers={'Content-Type':'application/json'})).read())['user']['role'] for email, password in users])"
```

Ожидается: `['editor', 'editor', 'reviewer']`.

Проверить удалённые credentials:

```powershell
docker compose -f docker-compose.yml exec -T backend python -c "import json, urllib.error, urllib.request; request=urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=json.dumps({'email':'viewer@example.com','password':'viewer-password'}).encode(), headers={'Content-Type':'application/json'}); exec(\"try:\\n urllib.request.urlopen(request)\\n raise SystemExit('expected 401')\\nexcept urllib.error.HTTPError as error:\\n assert error.code == 401\\n print('legacy login rejected')\")"
```

Ожидается: HTTP `401`.

- [ ] **Шаг 7: Проверить локальные dev и prod deployment profiles**

Из `infra`:

```powershell
docker compose -f docker-compose.yml down -v
docker compose --profile dev up -d --build
docker compose --profile dev ps
curl.exe -fsS http://localhost:8000/health
curl.exe -fsS http://localhost:5173/
docker compose --profile dev down

docker compose --profile prod up -d --build
docker compose --profile prod ps
curl.exe -fsS http://localhost:8000/health
curl.exe -fsS http://localhost:8080/
```

Ожидается: существующий dev deployment поднимает healthy backend и Vite
frontend; существующий prod deployment поднимает healthy backend и nginx
frontend. `infra/dev-up.cmd` и `infra/ci-up.cmd` продолжают использовать
совместимые Compose-команды.

- [ ] **Шаг 8: Перезапустить backend и проверить идемпотентность seed**

```powershell
docker compose --profile prod restart backend
docker compose --profile prod exec -T backend python seed_demo_users.py
docker compose --profile prod exec -T postgis sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT email, role, is_active FROM users ORDER BY email;"'
```

Ожидается: ровно три целевых demo users, корректные роли, все active,
повторный seed не создаёт дубликаты.

- [ ] **Шаг 9: Выполнить обязательный repository-change ingest**

Invoke `/ingest repository-change` through
`.agents/skills/source-command-ingest/SKILL.md`. It must update only knowledge
documentation, including the actual role model and demo credentials in
`Code_wiki/dev_setup/local_development.md`, подтвержденные CI gates в
`Code_wiki/сборка/ci_and_quality.md`, deployment smoke в
`Code_wiki/deployment/docker_compose.md`, then run wiki lint. Не создавать
session task-log: реализация восстанавливается из code, tests и обновлённых
`Code_wiki` нод.

- [ ] **Шаг 10: Выполнить финальные проверки репозитория**

```powershell
python scripts/check-memory-needed.py --check
git diff --check
git status --short
```

Ожидается: memory check проходит, whitespace errors отсутствуют, изменены
только ожидаемые файлы. Известные lint findings по frontmatter `RAW_inputs`
могут остаться задокументированными в `FU-2026-06-01-004`.

- [ ] **Шаг 11: Проверить итоговый diff без изменения staging**

```powershell
git diff
git diff --cached
git status --short
```

Ожидается: unstaged diff содержит реализацию и документацию задачи, ранее
существовавшие staged-изменения пользователя не изменены; Git index и история
остались без изменений.

## Проверка Покрытия Design

- Strict `editor | reviewer` enum: Task 1.
- One mutually exclusive role per user: Task 1.
- Legacy `Viewer` removal: Tasks 1-4 and Task 6 smoke.
- DB-backed active-user HTTP auth: Task 2.
- `require_editor` and `require_reviewer`: Task 2.
- Structured `AUTH_REQUIRED`, `USER_INACTIVE`, `ROLE_NOT_ALLOWED`: Task 2.
- Three stable demo users: Task 3.
- Realtime read access for both roles: Task 4.
- Frontend role names and reviewer isolation: Task 5.
- WorkOrder assignment and `WORK_ORDER_NOT_ASSIGNED`: explicitly deferred to
  S1-05 because `WorkOrder` does not exist on Day 2.
- Reviewer queue, approve/reject and `post`: explicitly deferred to later
  Release 1 sprints.
- Audit persistence: explicitly deferred; no audit table exists on Day 2.
- Existing CI jobs, backend/frontend image builds and Compose deployment
  profiles: Task 0 baseline and Task 6 regression gates.
