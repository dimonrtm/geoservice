# Типизация Auth User и Workspace Aggregate

Дата: 2026-07-10
Статус: утверждён пользователем для written spec
Расположение: `docs/superpowers/specs`

## Назначение

Убрать `Any` из двух известных внутренних контрактов backend:

1. объект аутентифицированного пользователя, проходящий через auth dependencies,
   auth/session services и защищённые endpoints;
2. параметр `WorkspaceService.workspace_from_aggregate()`, который фактически
   всегда получает `WorkspaceAggregateRow`.

Изменение должно сделать границы типов явными, не меняя HTTP API, JSON shape,
SQL, правила авторизации, error codes или пользовательское поведение.

## Архитектурное Ограничение

В текущей архитектуре допустима зависимость `use_cases` от `infrastructure`.
`web_api` не должен импортировать `infrastructure` напрямую. Поэтому ORM-модель
`User` нельзя использовать как аннотацию параметров в `web_api`.

Целевая направленность зависимостей:

```text
web_api -> use_cases -> infrastructure
```

Новый тип, доступный `web_api`, должен находиться в `use_cases` и не должен сам
импортировать infrastructure-модули. Преобразование infrastructure-модели в DTO
выполняется отдельным mapper внутри `use_cases`.

## Выбранный Подход

### Auth User

Добавить независимый application DTO:

```text
apps/backend/utility_service/use_cases/dtos/auth_user.py
```

```python
AuthRole = Literal["editor", "reviewer"]

@dataclass(frozen=True, slots=True)
class AuthUserDTO:
    id: UUID
    email: str
    role: AuthRole
    is_active: bool
```

DTO является внутренним immutable переносчиком данных. Он не является ORM-моделью
и не заменяет существующие API response schemas `AuthUserOut` и `AuthMeOut`.
Стандартный `dataclass` выбран вместо нового Pydantic model, потому что значения
уже проверены ORM-моделью и use-case логикой, а дополнительная runtime-валидация
на этой границе не нужна.

Добавить mapper в `use_cases`, например:

```text
apps/backend/utility_service/use_cases/mappers/auth_user_mapper.py
```

Mapper принимает infrastructure `User` и возвращает `AuthUserDTO`. Только mapper
и services, находящиеся в `use_cases`, знают о concrete ORM type. DTO-модуль и
`web_api` infrastructure не импортируют.

### Workspace Aggregate

Новый workspace DTO не добавляется. Repository уже возвращает точный тип
`WorkspaceAggregateRow | None`, поэтому `WorkspaceService` напрямую использует
существующий infrastructure read model:

```python
def workspace_from_aggregate(
    self,
    aggregate: WorkspaceAggregateRow,
) -> WorkspaceOut:
```

Такой импорт разрешён, потому что `WorkspaceService` находится в `use_cases`.
Структура `WorkspaceAggregateRow` и repository mapping не меняются.

`Any` внутри GeoJSON, feature properties и JSONB payload остаётся за пределами
этой задачи: эти значения действительно имеют динамическую JSON-форму. Также не
меняется отдельный `association_type: Any`, поскольку он не является типом
workspace aggregate целиком.

## Компоненты

### AuthService

`AuthService.authenticate_user()` продолжает получать ORM `User` из repository,
проверять пароль и `is_active`, но после успешной проверки преобразует модель и
возвращает `AuthUserDTO`.

`AuthService.get_user_by_id()` возвращает `AuthUserDTO | None`. Отсутствующий
пользователь обрабатывается до вызова mapper.

### AuthSessionService

`issue_session()` принимает `AuthUserDTO`, поскольку ему нужен только стабильный
use-case контракт пользователя.

`refresh_session()` продолжает читать ORM `User` через `UserRepository`, выполнять
существующие проверки активности и rotation, а перед возвратом преобразует
пользователя в `AuthUserDTO`. Поле `RefreshedAuthSessionOut.user` получает точный
тип `AuthUserDTO` вместо `Any`; ставшие ненужными импорт `Any` и настройка
`arbitrary_types_allowed=True` удаляются.

### Web API Auth Dependencies

`get_current_user()` возвращает `AuthUserDTO`. `require_editor()`,
`require_reviewer()` и `require_legacy_gis_editor()` принимают и возвращают тот же
тип. Поскольку `role` в DTO уже является строковым `AuthRole`, auth-specific
`_role_value(user: Any)` больше не нужен.

Параметры зависимостей во всех защищённых endpoints типизируются как
`AuthUserDTO`, включая:

- auth `/me`;
- secure ping endpoints;
- work-order list/open/workspace endpoints;
- utility-network endpoint;
- выдачу websocket ticket.

Эти модули импортируют DTO только из `use_cases`.

### WebSocketTicketService

`issue_ticket()` принимает `AuthUserDTO` и использует строковое поле `role`.

`consume_ticket()` может продолжать работать с concrete ORM `User`, потому что
метод находится в `use_cases`. После проверки он, как и сейчас, строит
`WebSocketUserContext`; отдельный `AuthUserDTO` в этом ответвлении не нужен.
Helper `_role_value(user: Any)` удаляется: `issue_ticket()` читает строковую роль
из `AuthUserDTO.role`, а `consume_ticket()` читает `User.role.value` из ORM enum.

### WorkspaceService

`workspace_from_aggregate()` получает `WorkspaceAggregateRow`. Логика построения
`WorkspaceOut`, фильтрация, нормализация значений enum и обработка повреждённого
контекста остаются прежними.

## Data Flow

### Login

```text
UserRepository -> ORM User -> AuthService validation
    -> AuthUserDTO -> AuthSessionService.issue_session
    -> web_api -> AuthUserOut
```

### Current User

```text
JWT -> AuthService.get_user_by_id -> ORM User
    -> AuthUserDTO -> get_current_user/role dependency -> endpoint
```

### Session Refresh

```text
session token -> AuthSessionRepository -> UserRepository -> ORM User
    -> activity/rotation checks -> AuthUserDTO
    -> RefreshedAuthSessionOut -> web_api
```

### Workspace

```text
WorkOrderRepository -> WorkspaceAggregateRow
    -> WorkspaceService.workspace_from_aggregate
    -> WorkspaceOut
```

## Error Handling

Существующие ошибки и их семантика не меняются:

- `401 AUTH_REQUIRED` для отсутствующей или недействительной сессии;
- `403 USER_INACTIVE` для отключённой учётной записи;
- `403 ROLE_NOT_ALLOWED` для неподходящей роли;
- текущие work-order ошибки доступа;
- `422 WORKSPACE_CONTEXT_INVALID` для повреждённого workspace context.

Mapper вызывается только для существующего ORM `User`. Он не вводит новую
runtime-валидацию роли: значение переносится из существующего `UserRole`, который
ограничен DB/ORM enum. Поэтому новая ветвь HTTP-ошибки не появляется.

## Testing

Обязательные проверки:

- unit-тест mapper для ролей `Editor` и `Reviewer`, включая перенос `id`, `email`
  и `is_active`;
- обновление auth service и auth session service тестов под `AuthUserDTO`;
- обновление auth API/access тестов, включая login, refresh, `/me` и role guards;
- обновление websocket ticket тестов для точного типа пользователя;
- существующие workspace service, workspace schemas и repository aggregate тесты;
- `ruff check` для backend;
- полный релевантный backend test suite.

Дополнительные статические проверки исходного кода:

1. В `web_api` нет прямых импортов `utility_service.infrastructure`.
2. Ни одна сигнатура, представляющая auth user, не использует `Any`.
3. `WorkspaceService.workspace_from_aggregate()` принимает
   `WorkspaceAggregateRow`, а не `Any`.
4. Динамические JSON/GeoJSON `Any` не удаляются механически.

Новый backend type-checker (`mypy` или `pyright`) и новый CI job не добавляются.

## Out Of Scope

- изменение public API или response JSON;
- изменение JWT/session cookie протокола;
- изменение ролей `Editor`/`Reviewer`;
- изменение SQL workspace aggregate query или repository rows;
- полная типизация JSONB, GeoJSON properties и geometry payload;
- замена всех `Any` в backend;
- настройка `mypy`, `pyright` или отдельного typecheck CI gate;
- реорганизация общей архитектуры repositories и services.

## Последствия

Auth boundary перестаёт передавать ORM-модель в `web_api`: web слой получает
маленький стабильный DTO без `password_hash`, `created_at` и других persistence
деталей. Изменение ORM-модели пользователя меньше влияет на endpoints.

Workspace boundary остаётся простой: существующий read model используется без
дублирующего DTO и дополнительного mapping. Все изменения ограничены типами и
внутренним преобразованием auth user; внешний контракт приложения сохраняется.

## Проверка Spec

Spec фиксирует один ограниченный refactor и не требует изменения API, SQL или CI.
Auth и workspace решения намеренно различаются: DTO нужен там, где объект пересекает
границу `use_cases -> web_api`; concrete row достаточен там, где объект остаётся
внутри `use_cases`. Неопределённых требований, незаполненных мест и скрытого расширения
scope в документе нет.
