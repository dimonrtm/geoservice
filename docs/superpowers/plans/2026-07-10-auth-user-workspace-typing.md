# План реализации типизации Auth User и Workspace Aggregate

> **Для agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить `Any`, обозначающий аутентифицированного пользователя, на независимый `AuthUserDTO`, а параметр workspace aggregate типизировать существующим `WorkspaceAggregateRow` без изменения API и runtime-семантики.

**Architecture:** `web_api` получает immutable DTO только из `use_cases`; преобразование ORM `User` в DTO выполняет mapper внутри `use_cases`, где зависимость от `infrastructure` разрешена. Workspace не получает дублирующий DTO: `WorkspaceService`, также находящийся в `use_cases`, принимает concrete infrastructure read model `WorkspaceAggregateRow`.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy 2, pytest, Ruff, standard-library `dataclasses` и `typing`.

## Global Constraints

- Written spec: `docs/superpowers/specs/2026-07-10-auth-user-workspace-typing-design.md`.
- Допустимое направление зависимостей: `web_api -> use_cases -> infrastructure`; прямые imports из `web_api` в `infrastructure` запрещены.
- Public HTTP API, JSON shape, JWT/session-cookie protocol, SQL и error codes не меняются.
- `AuthUserDTO.role` допускает только `Literal["editor", "reviewer"]` на уровне статического контракта.
- Динамические JSONB/GeoJSON `Any` и `WorkspaceService.association_type_value(association_type: Any)` остаются вне scope.
- Новый backend type-checker и новый CI job не добавляются.
- Все команды выполняются из `C:\Repositories\geoservice`; backend tests запускаются через существующий image `utility_service:dev` с bind mount `C:\Repositories\geoservice\apps\backend:/app`.

---

## Карта Файлов

### Новые файлы

- `apps/backend/utility_service/use_cases/dtos/__init__.py` — публичный use-case export `AuthRole` и `AuthUserDTO`.
- `apps/backend/utility_service/use_cases/dtos/auth_user.py` — immutable application DTO без infrastructure imports.
- `apps/backend/utility_service/use_cases/mappers/__init__.py` — публичный export mapper.
- `apps/backend/utility_service/use_cases/mappers/auth_user_mapper.py` — единственное преобразование ORM `User` в `AuthUserDTO`.
- `apps/backend/utility_service/use_cases/tests/test_auth_user_mapper.py` — контракт полей, ролей и immutability DTO.
- `apps/backend/utility_service/web_api/tests/__init__.py` — package marker для общих test helpers.
- `apps/backend/utility_service/web_api/tests/auth_user_factory.py` — единый factory `AuthUserDTO` для web API tests.
- `apps/backend/utility_service/web_api/tests/test_auth_typing_contract.py` — точные annotations auth dependencies/endpoints и запрет infrastructure imports из `web_api/api`.

### Изменяемые файлы

- `apps/backend/utility_service/use_cases/services/auth_service.py:9-47` — возврат `AuthUserDTO` вместо ORM `User`.
- `apps/backend/utility_service/use_cases/services/auth_session_service.py:3-113` — `AuthUserDTO` для issue/refresh flow.
- `apps/backend/utility_service/use_cases/schemas/auth/refreshed_auth_session_out.py:1-13` — точный тип поля `user`.
- `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py:3-106` — DTO на issue boundary и concrete ORM role при consume.
- `apps/backend/utility_service/use_cases/services/workspace_service.py:1-86` — `WorkspaceAggregateRow` вместо aggregate `Any`.
- `apps/backend/utility_service/web_api/api/auth.py:8-217` — DTO в auth dependencies и прямое чтение строковой роли.
- `apps/backend/utility_service/web_api/api/secure_router.py:1-24` — DTO и удаление `_role_value`.
- `apps/backend/utility_service/web_api/api/work_orders.py:1-82` — DTO в трёх editor dependencies.
- `apps/backend/utility_service/web_api/api/utility_network.py:1-28` — DTO для guard dependency.
- `apps/backend/utility_service/web_api/api/ws_layers.py:1-38` — DTO при выдаче websocket ticket.
- `apps/backend/utility_service/use_cases/tests/test_auth_service.py:1-97` — ожидание DTO из `AuthService`.
- `apps/backend/utility_service/use_cases/tests/test_auth_session_service.py:1-218` — DTO для issue и refresh results.
- `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py:1-280` — разделение issue DTO и ORM user для consume.
- `apps/backend/utility_service/use_cases/tests/test_workspace_service.py:1-177` — runtime-проверка aggregate annotation.
- `apps/backend/utility_service/web_api/tests/test_auth_api.py:1-273` — DTO в login/refresh fixtures.
- `apps/backend/utility_service/web_api/tests/test_auth_access.py:1-164` — DTO в auth dependencies и role guards.
- `apps/backend/utility_service/web_api/tests/test_work_orders_api.py:1-360` — DTO в `auth_context()`.
- `apps/backend/utility_service/web_api/tests/test_utility_network_api.py:1-150` — DTO в auth fixture.
- `apps/backend/utility_service/web_api/tests/test_layers_api.py:140-165` — DTO для legacy layer guard fixture.
- `apps/backend/utility_service/web_api/tests/test_ws_layers.py:1-370` — DTO для ticket endpoint auth fixtures.

---

### Task 1: Добавить AuthUserDTO и ORM Mapper

**Files:**

- Create: `apps/backend/utility_service/use_cases/dtos/__init__.py`
- Create: `apps/backend/utility_service/use_cases/dtos/auth_user.py`
- Create: `apps/backend/utility_service/use_cases/mappers/__init__.py`
- Create: `apps/backend/utility_service/use_cases/mappers/auth_user_mapper.py`
- Test: `apps/backend/utility_service/use_cases/tests/test_auth_user_mapper.py`

**Interfaces:**

- Consumes: infrastructure `User` и `UserRole` из `utility_service.infrastructure.postgresql.models.user`.
- Produces: `AuthRole`, `AuthUserDTO`, `to_auth_user_dto(user: User) -> AuthUserDTO`.

- [ ] **Step 1: Написать failing mapper test**

Создать `apps/backend/utility_service/use_cases/tests/test_auth_user_mapper.py`:

```python
from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.user import User, UserRole


def load_auth_user_contract():
    try:
        from utility_service.use_cases.dtos import AuthUserDTO
        from utility_service.use_cases.mappers import to_auth_user_dto
    except ModuleNotFoundError as exc:
        pytest.fail(f"Auth user DTO modules must exist: {exc}")
    return AuthUserDTO, to_auth_user_dto


@pytest.mark.parametrize(
    ("user_role", "expected_role"),
    [
        (UserRole.EDITOR, "editor"),
        (UserRole.REVIEWER, "reviewer"),
    ],
)
def test_to_auth_user_dto_maps_identity_role_and_activity(
    user_role: UserRole,
    expected_role: str,
) -> None:
    AuthUserDTO, to_auth_user_dto = load_auth_user_contract()
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"{expected_role}@example.local",
        role=user_role,
        is_active=False,
    )

    result = to_auth_user_dto(user)

    assert result == AuthUserDTO(
        id=user_id,
        email=f"{expected_role}@example.local",
        role=expected_role,
        is_active=False,
    )


def test_auth_user_dto_is_immutable() -> None:
    AuthUserDTO, _to_auth_user_dto = load_auth_user_contract()
    result = AuthUserDTO(
        id=uuid4(),
        email="editor@example.local",
        role="editor",
        is_active=True,
    )

    with pytest.raises(FrozenInstanceError):
        result.email = "changed@example.local"
```

- [ ] **Step 2: Запустить test и подтвердить отсутствие DTO module**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_auth_user_mapper.py -q"
```

Expected: FAIL в test body с `Auth user DTO modules must exist`; collection завершается успешно, а RED вызван отсутствующей реализацией.

- [ ] **Step 3: Реализовать immutable DTO и public export**

Создать `apps/backend/utility_service/use_cases/dtos/auth_user.py`:

```python
from dataclasses import dataclass
from typing import Literal, TypeAlias
from uuid import UUID


AuthRole: TypeAlias = Literal["editor", "reviewer"]


@dataclass(frozen=True, slots=True)
class AuthUserDTO:
    id: UUID
    email: str
    role: AuthRole
    is_active: bool
```

Создать `apps/backend/utility_service/use_cases/dtos/__init__.py`:

```python
from utility_service.use_cases.dtos.auth_user import AuthRole, AuthUserDTO

__all__ = ["AuthRole", "AuthUserDTO"]
```

- [ ] **Step 4: Реализовать mapper без runtime-валидации роли**

Создать `apps/backend/utility_service/use_cases/mappers/auth_user_mapper.py`:

```python
from typing import cast

from utility_service.infrastructure.postgresql.models.user import User
from utility_service.use_cases.dtos import AuthRole, AuthUserDTO


def to_auth_user_dto(user: User) -> AuthUserDTO:
    return AuthUserDTO(
        id=user.id,
        email=user.email,
        role=cast(AuthRole, user.role.value),
        is_active=user.is_active,
    )
```

Создать `apps/backend/utility_service/use_cases/mappers/__init__.py`:

```python
from utility_service.use_cases.mappers.auth_user_mapper import to_auth_user_dto

__all__ = ["to_auth_user_dto"]
```

- [ ] **Step 5: Запустить mapper tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_auth_user_mapper.py -q"
```

Expected: `2 passed`.

---

### Task 2: Перевести AuthService и AuthSessionService на DTO

**Files:**

- Modify: `apps/backend/utility_service/use_cases/services/auth_service.py:9-47`
- Modify: `apps/backend/utility_service/use_cases/services/auth_session_service.py:3-113`
- Modify: `apps/backend/utility_service/use_cases/schemas/auth/refreshed_auth_session_out.py:1-13`
- Test: `apps/backend/utility_service/use_cases/tests/test_auth_service.py:1-97`
- Test: `apps/backend/utility_service/use_cases/tests/test_auth_session_service.py:1-218`

**Interfaces:**

- Consumes: `AuthUserDTO` и `to_auth_user_dto()` из Task 1.
- Produces: `AuthService.authenticate_user(email: str, password: str) -> AuthUserDTO`, `AuthService.get_user_by_id(user_id: UUID) -> AuthUserDTO | None`, `AuthSessionService.issue_session(user: AuthUserDTO)`, `RefreshedAuthSessionOut.user: AuthUserDTO`.

- [ ] **Step 1: Изменить AuthService tests так, чтобы они требовали DTO**

Добавить import:

```python
from utility_service.use_cases.dtos import AuthUserDTO
```

Заменить два success-теста следующими контрактами; проверки транзакции и repository calls сохранить:

```python
def test_authenticate_user_returns_dto_for_valid_credentials() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        password_hash=hash_password("editor-password"),
        is_active=True,
    )
    repository = AsyncMock()
    repository.get_by_email.return_value = user
    service, _session = build_service(repository)

    result = asyncio.run(service.authenticate_user("editor@example.com", "editor-password"))

    assert result == AuthUserDTO(
        id=user.id,
        email=user.email,
        role="editor",
        is_active=True,
    )
    repository.get_by_email.assert_awaited_once_with("editor@example.com")


def test_get_user_by_id_returns_dto_after_closing_read_transaction() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        password_hash=hash_password("editor-password"),
        is_active=True,
    )
    repository = AsyncMock()
    repository.get_by_id.return_value = user
    session = FakeReadSession()
    service = AuthService(session=session, user_repository=repository)

    result = asyncio.run(service.get_user_by_id(user.id))

    assert result == AuthUserDTO(
        id=user.id,
        email=user.email,
        role="editor",
        is_active=True,
    )
    assert session.begin_calls == 1
    assert session.in_transaction is False
    repository.get_by_id.assert_awaited_once_with(user.id)
```

В `test_authenticate_user_closes_read_transaction_before_session_reuse()` заменить `assert result is user` на:

```python
assert result == AuthUserDTO(
    id=user.id,
    email=user.email,
    role="editor",
    is_active=True,
)
```

- [ ] **Step 2: Изменить session tests так, чтобы issue и refresh требовали DTO**

Добавить imports:

```python
from typing import get_type_hints

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.use_cases.dtos import AuthUserDTO
```

Изменить ORM-like fixture и добавить DTO factory:

```python
def make_user(*, is_active: bool = True):
    return SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=UserRole.EDITOR,
        is_active=is_active,
    )


def auth_user_dto(user) -> AuthUserDTO:
    return AuthUserDTO(
        id=user.id,
        email=user.email,
        role="editor",
        is_active=user.is_active,
    )
```

Добавить точные type contracts:

```python
def test_auth_session_service_uses_auth_user_dto_contract() -> None:
    assert get_type_hints(AuthSessionService.issue_session)["user"] is AuthUserDTO
    assert RefreshedAuthSessionOut.model_fields["user"].annotation is AuthUserDTO
```

В `test_issue_session_creates_hash_and_12_hour_expiry()` передавать `auth_user_dto(user)` вместо ORM fixture. В двух refresh success-тестах заменить identity assertions:

```python
assert result.user == auth_user_dto(user)
```

и:

```python
assert result.user == auth_user_dto(rotated_user)
```

- [ ] **Step 3: Запустить изменённые tests и подтвердить старые return types**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_auth_service.py utility_service/use_cases/tests/test_auth_session_service.py -q"
```

Expected: FAIL — `AuthService` возвращает ORM object, `issue_session` аннотирован `Any`, а `RefreshedAuthSessionOut.user` имеет annotation `Any`.

- [ ] **Step 4: Изменить AuthService return boundary**

В `auth_service.py` импортировать DTO и mapper, удалить прямой импорт `User`, затем использовать следующие методы:

```python
from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.mappers import to_auth_user_dto


async def authenticate_user(self, email: str, password: str) -> AuthUserDTO:
    async with self.session.begin():
        user = await self.user_repository.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=INVALID_CREDENTIALS_CODE,
            message=INVALID_CREDENTIALS_MESSAGE,
        )
    if not user.is_active:
        raise AuthApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_INACTIVE",
            message="Учетная запись отключена.",
        )
    return to_auth_user_dto(user)


async def get_user_by_id(self, user_id: UUID) -> AuthUserDTO | None:
    async with self.session.begin():
        user = await self.user_repository.get_by_id(user_id)
    if user is None:
        return None
    return to_auth_user_dto(user)
```

- [ ] **Step 5: Изменить session service и refreshed schema**

В `auth_session_service.py` удалить `from typing import Any`, импортировать DTO и mapper, затем изменить границы:

```python
from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.mappers import to_auth_user_dto


async def issue_session(self, user: AuthUserDTO) -> IssuedAuthSessionOut:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=self.ttl_hours)

    async with self.session.begin():
        await self.session_repository.create_session(
            session_token_hash=hash_auth_session_token(token),
            user_id=user.id,
            expires_at=expires_at,
        )

    return IssuedAuthSessionOut(token=token, expires_at=expires_at)
```

В конце `refresh_session()` преобразовать выбранного после rotation ORM user:

```python
return RefreshedAuthSessionOut(
    token=new_token,
    expires_at=expires_at,
    user=to_auth_user_dto(user),
)
```

Полностью заменить `refreshed_auth_session_out.py`:

```python
from pydantic import ConfigDict

from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.schemas.auth.issued_auth_session_out import (
    IssuedAuthSessionOut,
)


class RefreshedAuthSessionOut(IssuedAuthSessionOut):
    model_config = ConfigDict(extra="forbid")

    user: AuthUserDTO
```

- [ ] **Step 6: Запустить auth service/session tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_auth_user_mapper.py utility_service/use_cases/tests/test_auth_service.py utility_service/use_cases/tests/test_auth_session_service.py -q"
```

Expected: PASS; transaction-order assertions и существующие `401/403` assertions остаются зелёными.

---

### Task 3: Типизировать WebSocketTicketService

**Files:**

- Modify: `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py:3-106`
- Test: `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py:1-280`

**Interfaces:**

- Consumes: `AuthRole`, `AuthUserDTO` из Task 1; ORM `User` остаётся repository result внутри `consume_ticket()`.
- Produces: `issue_ticket(user: AuthUserDTO, layer_id: UUID) -> WebSocketTicketOut`; helper `_role_value(user: Any)` удалён.

- [ ] **Step 1: Разделить DTO actor и ORM repository user в tests**

Добавить imports:

```python
from typing import cast, get_type_hints

from utility_service.use_cases.dtos import AuthRole, AuthUserDTO
```

Заменить единственный `make_user()` двумя helpers:

```python
def make_orm_user(role: str = "editor", is_active: bool = True):
    return SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=SimpleNamespace(value=role),
        is_active=is_active,
    )


def make_auth_user(user) -> AuthUserDTO:
    return AuthUserDTO(
        id=user.id,
        email=user.email,
        role=cast(AuthRole, user.role.value),
        is_active=user.is_active,
    )
```

Добавить annotation contract:

```python
def test_issue_ticket_accepts_auth_user_dto() -> None:
    assert get_type_hints(WebSocketTicketService.issue_ticket)["user"] is AuthUserDTO
```

Во всех issue paths создавать ORM-like user через `make_orm_user`, передавать его в `build_service()` и вызывать:

```python
result = asyncio.run(service.issue_ticket(make_auth_user(orm_user), layer.id))
```

Для consume paths repository продолжает возвращать `orm_user`. В inactive-after-issue test изменять только ORM object после выдачи ticket:

```python
issued = asyncio.run(service.issue_ticket(make_auth_user(orm_user), layer.id))
orm_user.is_active = False
```

Сохранить проверки reviewer/viewer denial, создавая DTO через `make_auth_user()`; `cast()` не меняет runtime role value.

- [ ] **Step 2: Запустить websocket service test и подтвердить `Any` annotation**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_websocket_ticket_service.py -q"
```

Expected: FAIL в `test_issue_ticket_accepts_auth_user_dto`, потому что текущая annotation равна `Any`.

- [ ] **Step 3: Реализовать разные role representations для issue и consume**

В `websocket_ticket_service.py` удалить import `Any` и `_role_value()`, импортировать DTO:

```python
from utility_service.use_cases.dtos import AuthUserDTO
```

Изменить issue signature и role guard:

```python
async def issue_ticket(self, user: AuthUserDTO, layer_id: UUID) -> WebSocketTicketOut:
    if user.role not in ALLOWED_REALTIME_ROLES:
        raise AuthApiError(
            status.HTTP_403_FORBIDDEN,
            "ROLE_NOT_ALLOWED",
            "Подписка на realtime недоступна для этой роли.",
        )
    if not user.is_active:
        raise AuthApiError(
            status.HTTP_403_FORBIDDEN,
            "USER_INACTIVE",
            "Учетная запись отключена.",
        )
```

Оставшуюся ticket creation transaction не менять. В `consume_ticket()` использовать concrete ORM enum:

```python
user = await self.user_repository.get_by_id(user_id)
if (
    user is None
    or not user.is_active
    or user.role.value not in ALLOWED_REALTIME_ROLES
):
    raise WebSocketTicketError(INVALID_WEBSOCKET_TICKET_MESSAGE)

return WebSocketUserContext(
    user_id=user.id,
    email=user.email,
    role=user.role.value,
)
```

- [ ] **Step 4: Запустить websocket service tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_websocket_ticket_service.py -q"
```

Expected: PASS, включая one-time consume, wrong layer, expired ticket, reviewer и inactive user cases.

---

### Task 4: Провести AuthUserDTO Через Web API

**Files:**

- Create: `apps/backend/utility_service/web_api/tests/test_auth_typing_contract.py`
- Create: `apps/backend/utility_service/web_api/tests/__init__.py`
- Create: `apps/backend/utility_service/web_api/tests/auth_user_factory.py`
- Modify: `apps/backend/utility_service/web_api/api/auth.py:8-217`
- Modify: `apps/backend/utility_service/web_api/api/secure_router.py:1-24`
- Modify: `apps/backend/utility_service/web_api/api/work_orders.py:1-82`
- Modify: `apps/backend/utility_service/web_api/api/utility_network.py:1-28`
- Modify: `apps/backend/utility_service/web_api/api/ws_layers.py:1-38`
- Test: `apps/backend/utility_service/web_api/tests/test_auth_api.py:1-273`
- Test: `apps/backend/utility_service/web_api/tests/test_auth_access.py:1-164`
- Test: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py:1-360`
- Test: `apps/backend/utility_service/web_api/tests/test_utility_network_api.py:1-150`
- Test: `apps/backend/utility_service/web_api/tests/test_layers_api.py:140-165`
- Test: `apps/backend/utility_service/web_api/tests/test_ws_layers.py:1-370`

**Interfaces:**

- Consumes: `AuthUserDTO` returned by `AuthService` and accepted by `WebSocketTicketService`.
- Produces: все auth dependencies/endpoint parameters используют `AuthUserDTO`; `web_api/api` не импортирует `infrastructure`.

- [ ] **Step 1: Написать failing annotation и layer-boundary tests**

Создать `apps/backend/utility_service/web_api/tests/test_auth_typing_contract.py`:

```python
from pathlib import Path
from typing import get_type_hints

import pytest

from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.web_api.api.auth import (
    get_current_user,
    me,
    require_editor,
    require_legacy_gis_editor,
    require_reviewer,
)
from utility_service.web_api.api.secure_router import ping, ping_write
from utility_service.web_api.api.utility_network import get_feeder
from utility_service.web_api.api.work_orders import (
    get_workspace,
    list_assigned_to_me,
    open_edit_version,
)
from utility_service.web_api.api.ws_layers import issue_layer_websocket_ticket


@pytest.mark.parametrize(
    ("function", "parameter"),
    [
        (require_editor, "user"),
        (require_legacy_gis_editor, "user"),
        (require_reviewer, "user"),
        (me, "user"),
        (ping, "user"),
        (ping_write, "user"),
        (list_assigned_to_me, "user"),
        (open_edit_version, "user"),
        (get_workspace, "user"),
        (get_feeder, "_"),
        (issue_layer_websocket_ticket, "user"),
    ],
)
def test_web_api_auth_parameters_use_auth_user_dto(function, parameter: str) -> None:
    assert get_type_hints(function)[parameter] is AuthUserDTO


def test_auth_dependencies_return_auth_user_dto() -> None:
    assert get_type_hints(get_current_user)["return"] is AuthUserDTO
    assert get_type_hints(require_editor)["return"] is AuthUserDTO
    assert get_type_hints(require_legacy_gis_editor)["return"] is AuthUserDTO
    assert get_type_hints(require_reviewer)["return"] is AuthUserDTO


def test_web_api_source_does_not_import_infrastructure() -> None:
    api_dir = Path(__file__).resolve().parents[1] / "api"
    offenders = [
        path.name
        for path in api_dir.glob("*.py")
        if "utility_service.infrastructure" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
```

- [ ] **Step 2: Запустить contract test и подтвердить endpoint `Any`**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/web_api/tests/test_auth_typing_contract.py -q"
```

Expected: annotation parametrizations FAIL, потому что production functions ещё используют `Any`; infrastructure import test PASS.

- [ ] **Step 3: Типизировать auth dependencies и удалить `_role_value`**

В `auth.py` удалить import `Any`, импортировать `AuthUserDTO` и изменить signatures:

```python
from utility_service.use_cases.dtos import AuthUserDTO


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthUserDTO:
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

    if "sub" not in payload or payload.get("role") not in SUPPORTED_AUTH_ROLES:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError as exc:
        raise AuthApiError(
            401,
            "AUTH_REQUIRED",
            "Сессия недействительна.",
        ) from exc

    current_user = await auth_service.get_user_by_id(user_id)
    if current_user is None:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")
    if not current_user.is_active:
        raise AuthApiError(403, "USER_INACTIVE", "Учетная запись отключена.")
    return current_user


def require_editor(
    user: AuthUserDTO = Depends(get_current_user),
) -> AuthUserDTO:
    if user.role != EDITOR_ROLE:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Editor.",
        )
    return user


def require_legacy_gis_editor(
    user: AuthUserDTO = Depends(get_current_user),
) -> AuthUserDTO:
    if not settings.legacy_gis_api_enabled:
        raise AuthApiError(
            status.HTTP_403_FORBIDDEN,
            LEGACY_GIS_API_DISABLED_CODE,
            LEGACY_GIS_API_DISABLED_MESSAGE,
        )
    return require_editor(user)


def require_reviewer(
    user: AuthUserDTO = Depends(get_current_user),
) -> AuthUserDTO:
    if user.role != REVIEWER_ROLE:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Reviewer.",
        )
    return user
```

В `login()`, `refresh_session()` и `me()` заменить каждый вызов `_role_value(user)` прямым `user.role`. Итоговые изменённые blocks должны выглядеть так:

```python
# login()
token = create_access_token(str(user.id), user.role)
return AuthSuccessOut(
    access_token=token,
    token_type="bearer",
    user=AuthUserOut(
        id=str(user.id),
        email=user.email,
        role=user.role,
    ),
)


# refresh_session()
user = session.user
token = create_access_token(str(user.id), user.role)
return AuthSuccessOut(
    access_token=token,
    token_type="bearer",
    user=AuthUserOut(
        id=str(user.id),
        email=user.email,
        role=user.role,
    ),
)


# /me
async def me(user: AuthUserDTO = Depends(get_current_user)) -> AuthMeOut:
    return AuthMeOut(
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=user.role,
        )
    )
```

Удалить функцию `_role_value()` полностью.

- [ ] **Step 4: Типизировать остальные protected endpoints**

В каждом модуле импортировать:

```python
from utility_service.use_cases.dtos import AuthUserDTO
```

Применить следующие полные endpoint definitions; decorators и неизменяемые imports/schemas вокруг них сохранить:

```python
# secure_router.py
async def ping(user: AuthUserDTO = Depends(get_current_user)) -> dict:
    return {"status": "ok", "user_id": str(user.id), "role": user.role}


async def ping_write(user: AuthUserDTO = Depends(require_editor)) -> dict:
    return {
        "status": "ok",
        "write": True,
        "user_id": str(user.id),
        "role": user.role,
    }


# work_orders.py
async def list_assigned_to_me(
    user: AuthUserDTO = Depends(require_editor),
    work_order_service: WorkOrderService = Depends(get_work_order_service),
) -> AssignedWorkOrdersOut:
    return await work_order_service.list_assigned_to_editor(user.id)


async def open_edit_version(
    work_order_id: UUID,
    response: Response,
    user: AuthUserDTO = Depends(require_editor),
    edit_version_service: EditVersionService = Depends(get_edit_version_service),
) -> OpenEditVersionOut:
    result = await edit_version_service.open_for_work_order(work_order_id, user.id)
    if not result.created:
        response.status_code = status.HTTP_200_OK

    edit_version = result.edit_version
    status_value = getattr(edit_version.status, "value", edit_version.status)
    return OpenEditVersionOut(
        created=result.created,
        edit_version=EditVersionOut(
            id=edit_version.id,
            work_order_id=edit_version.work_order_id,
            owner_user_id=edit_version.owner_user_id,
            status=status_value,
            base_network_revision=edit_version.base_network_revision,
            created_at=edit_version.created_at,
            last_opened_at=edit_version.last_opened_at,
        ),
    )


async def get_workspace(
    work_order_id: UUID,
    edit_version_id: UUID,
    user: AuthUserDTO = Depends(require_editor),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceOut:
    return await workspace_service.get_workspace(
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
        actor_id=user.id,
    )

# utility_network.py
async def get_feeder(
    feederId: UUID,
    _: AuthUserDTO = Depends(require_editor),
    service: UtilityNetworkService = Depends(get_utility_network_service),
) -> UtilityFeederOut:
    feeder_id = feederId
    return await service.get_feeder(feeder_id)

# ws_layers.py
async def issue_layer_websocket_ticket(
    layer_id: UUID,
    user: AuthUserDTO = Depends(require_legacy_gis_editor),
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
) -> WebSocketTicketOut:
    return await ticket_service.issue_ticket(user, layer_id)
```

Удалить ставшие ненужными imports `Any`; в `secure_router.py` также удалить import `_role_value`.

- [ ] **Step 5: Перевести web API test fixtures на DTO**

Создать пустой `apps/backend/utility_service/web_api/tests/__init__.py` и общий `apps/backend/utility_service/web_api/tests/auth_user_factory.py`:

```python
from uuid import UUID, uuid4

from utility_service.use_cases.dtos import AuthRole, AuthUserDTO


def auth_user(
    role: AuthRole = "editor",
    *,
    user_id: UUID | None = None,
    is_active: bool = True,
) -> AuthUserDTO:
    resolved_user_id = user_id or uuid4()
    return AuthUserDTO(
        id=resolved_user_id,
        email=f"{role}@example.local",
        role=role,
        is_active=is_active,
    )
```

Во всех шести test modules импортировать один factory:

```python
from utility_service.web_api.tests.auth_user_factory import auth_user
```

Использовать его в локальных contexts:

```python
# test_auth_api.py
def build_auth_user(role: AuthRole = "editor") -> AuthUserDTO:
    return auth_user(role)


# test_work_orders_api.py
def auth_context(role: AuthRole, *, is_active: bool = True):
    user_id = uuid4()
    token = create_access_token(str(user_id), role)
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = auth_user(
        role,
        user_id=user_id,
        is_active=is_active,
    )
    return auth_service, token, user_id


# test_utility_network_api.py
def auth_context(
    role: AuthRole,
    *,
    is_active: bool = True,
) -> tuple[AsyncMock, str]:
    user_id = uuid4()
    token = create_access_token(str(user_id), role)
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = auth_user(
        role,
        user_id=user_id,
        is_active=is_active,
    )
    return auth_service, token


# test_layers_api.py
user = auth_user(role, user_id=USER_ID)


# test_auth_access.py и test_ws_layers.py
editor = auth_user("editor")
reviewer = auth_user("reviewer")
```

Заменить все nested role fixtures вызовами этих helpers. В `test_auth_access.py` переименовать `test_secure_ping_uses_database_user_model` в `test_secure_ping_uses_auth_user_dto`; ожидаемый response JSON оставить прежним. `SimpleNamespace` imports сохранять только в файлах, где он ещё используется для layer/edit-version/service fakes.

- [ ] **Step 6: Запустить contract и web API regression tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/web_api/tests/test_auth_typing_contract.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py utility_service/web_api/tests/test_utility_network_api.py utility_service/web_api/tests/test_layers_api.py utility_service/web_api/tests/test_ws_layers.py -q"
```

Expected: PASS; login/refresh JSON, cookie flags, `401/403/404`, legacy feature flag и websocket ticket behavior не изменились.

---

### Task 5: Типизировать Workspace Aggregate и Выполнить Полную Проверку

**Files:**

- Modify: `apps/backend/utility_service/use_cases/services/workspace_service.py:1-86`
- Test: `apps/backend/utility_service/use_cases/tests/test_workspace_service.py:1-177`

**Interfaces:**

- Consumes: существующий `WorkspaceAggregateRow` из `utility_service.infrastructure.postgresql.repository_rows.workspace`.
- Produces: `WorkspaceService.workspace_from_aggregate(aggregate: WorkspaceAggregateRow) -> WorkspaceOut`; JSON/GeoJSON `Any` остаются неизменными.

- [ ] **Step 1: Добавить failing annotation contract**

В `test_workspace_service.py` добавить imports:

```python
from typing import get_type_hints

from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
)
```

Добавить test перед behavior tests:

```python
def test_workspace_from_aggregate_uses_repository_row_contract() -> None:
    annotation = get_type_hints(WorkspaceService.workspace_from_aggregate)["aggregate"]

    assert annotation is WorkspaceAggregateRow
```

- [ ] **Step 2: Запустить workspace test и подтвердить aggregate `Any`**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_workspace_service.py -q"
```

Expected: FAIL только в новом contract test: annotation равна `Any`.

- [ ] **Step 3: Заменить только aggregate annotation**

В `workspace_service.py` добавить import:

```python
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
)
```

Изменить signature без изменения тела:

```python
def workspace_from_aggregate(
    self,
    aggregate: WorkspaceAggregateRow,
) -> WorkspaceOut:
```

Сохранить `from typing import Any`, потому что он всё ещё используется в `feature_properties()` и `association_type_value()` для динамических payload.

- [ ] **Step 4: Запустить workspace tests**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest utility_service/use_cases/tests/test_workspace_service.py utility_service/use_cases/tests/test_workspace_schemas.py utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py -q"
```

Expected: PASS; существующие `403/404/409/422` и workspace response shape не меняются.

- [ ] **Step 5: Проверить отсутствие целевых `Any` и нарушение слоя**

Run from `C:\Repositories\geoservice\apps\backend`:

```powershell
rg -n "\bAny\b" utility_service/web_api/api/auth.py utility_service/web_api/api/secure_router.py utility_service/web_api/api/work_orders.py utility_service/web_api/api/utility_network.py utility_service/web_api/api/ws_layers.py utility_service/use_cases/services/auth_session_service.py utility_service/use_cases/services/websocket_ticket_service.py utility_service/use_cases/schemas/auth/refreshed_auth_session_out.py
rg -n "utility_service\.infrastructure" utility_service/web_api/api
rg -n "workspace_from_aggregate\(self, aggregate: Any" utility_service/use_cases/services/workspace_service.py
```

Expected: все три команды завершаются без совпадений. Не применять этот поиск ко всем JSON/GeoJSON modules.

- [ ] **Step 6: Запустить полный backend test suite**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "pytest -q"
```

Expected: exit code `0`; все доступные tests PASS, integration tests без включённой внешней БД могут остаться SKIPPED согласно существующим markers.

- [ ] **Step 7: Запустить formatting и lint gates**

Run:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "black --check . && ruff check ."
```

Expected: `All done!` от Black и `All checks passed!` от Ruff. Если Black перечисляет изменённые файлы, выполнить следующую точную formatting command, повторить tests из Step 6 и затем повторить этот gate:

```powershell
docker run --rm -v C:\Repositories\geoservice\apps\backend:/app -w /app --entrypoint bash utility_service:dev -lc "black utility_service/use_cases/dtos utility_service/use_cases/mappers utility_service/use_cases/services/auth_service.py utility_service/use_cases/services/auth_session_service.py utility_service/use_cases/services/websocket_ticket_service.py utility_service/use_cases/services/workspace_service.py utility_service/use_cases/schemas/auth/refreshed_auth_session_out.py utility_service/use_cases/tests/test_auth_user_mapper.py utility_service/use_cases/tests/test_auth_service.py utility_service/use_cases/tests/test_auth_session_service.py utility_service/use_cases/tests/test_websocket_ticket_service.py utility_service/use_cases/tests/test_workspace_service.py utility_service/web_api/api/auth.py utility_service/web_api/api/secure_router.py utility_service/web_api/api/work_orders.py utility_service/web_api/api/utility_network.py utility_service/web_api/api/ws_layers.py utility_service/web_api/tests/test_auth_typing_contract.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py utility_service/web_api/tests/test_utility_network_api.py utility_service/web_api/tests/test_layers_api.py utility_service/web_api/tests/test_ws_layers.py"
```

- [ ] **Step 8: Проверить итоговый diff**

Run:

```powershell
git diff --check
git status --short
git diff -- apps/backend/utility_service/use_cases/services/workspace_service.py apps/backend/utility_service/use_cases/tests/test_workspace_service.py
```

Expected: `git diff --check` не выводит ошибок; diff Task 5 содержит только import, точную annotation и contract test.

---

## Definition Of Done

- `AuthUserDTO` — frozen/slots dataclass в `use_cases`, не импортирующий infrastructure.
- Единственный ORM-to-DTO mapper находится в `use_cases/mappers`.
- ORM `User` не пересекает границу `use_cases -> web_api`.
- Все auth-user signatures вместо `Any` используют `AuthUserDTO` или concrete ORM `User` внутри `use_cases` consume path.
- `RefreshedAuthSessionOut.user` имеет annotation `AuthUserDTO`.
- `WorkspaceService.workspace_from_aggregate()` принимает `WorkspaceAggregateRow`.
- Direct imports `web_api -> infrastructure` отсутствуют и защищены test.
- Public API, cookie/JWT behavior, roles, structured errors, workspace JSON и SQL не изменены.
- Focused tests, полный backend suite, Black и Ruff завершаются с exit code `0`.
