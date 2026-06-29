# Унификация API Ошибок Auth И Workflow

Дата: 2026-06-29
Статус: согласован для written spec
Расположение: `docs/superpowers/specs`

## Назначение

`POST /api/v1/auth/login` и workflow endpoints для `WorkOrder`, `EditVersion` и
`Workspace` должны возвращать единый structured error body:

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "Неверная электронная почта или пароль",
  "correlationId": "test-correlation-id"
}
```

Сейчас часть API уже использует structured contract, но `AuthApiError`,
`WorkOrderApiError` и `UtilityNetworkApiError` добавляют поле `details`, а
неверный login credentials path выбрасывает FastAPI `HTTPException` с
`detail`. Это создает два разных контракта для близких пользовательских ошибок.

Цель изменения - сделать auth invalid login и workflow errors строгими и
предсказуемыми: только `code`, `message`, `correlationId`.

## Границы Scope

Входит:

- invalid credentials в `AuthService.authenticate_user()`;
- HTTP handlers для `AuthApiError`, `WorkOrderApiError` и `UtilityNetworkApiError`;
- frontend login UI, который читает текст ошибки из `message`;
- backend tests для auth service, auth API, structured handlers и workflow API;
- frontend tests для login error rendering.

Не входит:

- WebSocket close reasons;
- FastAPI request validation errors;
- `BusinessValidationException`, `LayerNotFoundException`,
  `FeatureNotFoundException`, `UnknownStorageTableError`;
- `VersionMismatchException` и специальный `VERSION_MISMATCH` response body;
- изменение пользовательских fallback-сообщений в `workOrders` store;
- новый глобальный frontend error bus или toast UI.

## Выбранный Подход

Выбран точечный подход: унифицировать уже существующее structured-семейство
auth, utility network и workflow errors без широкой миграции всех ошибок API.

Причины:

- задача явно касается invalid login и workflow errors;
- `WorkOrderApiError` уже несет `status_code`, `code`, `message`;
- `AuthApiError` уже используется для `AUTH_REQUIRED`, `USER_INACTIVE` и
  `ROLE_NOT_ALLOWED`;
- широкая миграция `Feature`, `Layer`, validation и version conflict ошибок
  затронет больше frontend paths и требует отдельного API-дизайна.

Альтернативы отклонены:

- общий базовый `ApiError` для всех доменных исключений сейчас дает больше
  касаний, чем пользы для текущего scope;
- полная унификация всех backend errors правильна как будущая работа, но
  увеличит риск регрессий в map/layers/edit flows.

## Backend Design

В `apps/backend/utility_service/web_api/api/exception_handlers.py` нужен
локальный helper, который собирает response body:

```python
def structured_error_response(request, status_code, code, message):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "correlationId": correlation_id,
        },
    )
```

Handlers для `AuthApiError`, `UtilityNetworkApiError` и `WorkOrderApiError`
используют этот helper. Поле `details` удаляется из всех трех ответов.

`AuthService.authenticate_user()` перестает выбрасывать `HTTPException` для
unknown email, wrong password и `password_hash is None`. Вместо этого сервис
выбрасывает:

```python
AuthApiError(
    status_code=401,
    code="INVALID_CREDENTIALS",
    message="Неверная электронная почта или пароль",
)
```

`USER_INACTIVE`, `AUTH_REQUIRED` и `ROLE_NOT_ALLOWED` сохраняют свои коды,
статусы и сообщения. Меняется только shape HTTP response.

`WorkOrderApiError` и `UtilityNetworkApiError` классы менять не нужно: их
текущих полей достаточно.

## Frontend Design

`apps/frontend/src/components/LoginScreen.vue` должен читать structured body.
Если `status === 401` и `error.response.data.message` является строкой, UI
показывает это сообщение. В остальных случаях остается текущий generic fallback:
`Сейчас не удалось выполнить вход. Попробуйте ещё раз.`

Чтение `error.response.data.detail` удаляется из login UI, потому что invalid
login больше не возвращает FastAPI `detail`.

`apps/frontend/src/api/http.ts` в этом scope не меняется. Текущий interceptor
по-прежнему вызывает `auth.logout()` на любом `401`. Для login failure это не
мешает показать ошибку после rejected request, а изменение interceptor behavior
затронуло бы более широкий auth/session flow.

`apps/frontend/src/stores/workOrders.ts` в этом scope не начинает показывать raw
backend `message`. Для загрузки нарядов и открытия workspace сохраняются
существующие стабильные пользовательские fallback-сообщения.

## Error Handling

`correlationId` формируется единообразно:

- если запрос содержит `X-Correlation-ID`, response возвращает это значение;
- если заголовка нет, backend генерирует новый UUID;
- frontend не обязан генерировать correlation id в этой задаче.

Public error codes в scope:

- `INVALID_CREDENTIALS` для неверной электронной почты, неверного пароля или
  отсутствующего password hash;
- существующие auth codes: `AUTH_REQUIRED`, `USER_INACTIVE`, `ROLE_NOT_ALLOWED`;
- существующие workflow codes: `WORK_ORDER_NOT_FOUND`,
  `WORK_ORDER_CONTEXT_INVALID`, `WORK_ORDER_STATE_CONFLICT`,
  `EDIT_VERSION_NOT_FOUND`, `EDIT_VERSION_STATE_CONFLICT`,
  `WORKSPACE_CONTEXT_INVALID`;
- существующие utility network codes остаются в том же strict shape, например
  `FEEDER_NOT_FOUND` и `UTILITY_DATASET_INVALID`.

`INVALID_CREDENTIALS` намеренно не раскрывает, был ли найден email. Это
сохраняет текущую безопасную семантику invalid login.

## Testing

Backend tests:

- `apps/backend/utility_service/use_cases/tests/test_auth_service.py`:
  unknown email, wrong password и `password_hash is None` ожидают
  `AuthApiError` с `status_code == 401` и `code == "INVALID_CREDENTIALS"`;
- auth API test для `POST /api/v1/auth/login` проверяет strict response body
  `{code, message, correlationId}` и отсутствие `detail`/`details`;
- `apps/backend/utility_service/web_api/tests/test_exception_handlers.py`
  проверяет, что structured handlers возвращают только три поля;
- `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`
  закрепляет strict body для `WorkOrderApiError` на workflow endpoints;
- существующие tests для `ROLE_NOT_ALLOWED`, `AUTH_REQUIRED` и
  `USER_INACTIVE` обновляются под отсутствие `details`, где они проверяют body.

Frontend tests:

- login component test покрывает `401` response с `message` и проверяет, что
  текст отображается пользователю;
- fallback test покрывает `401` или другую ошибку без строкового `message` и
  сохраняет generic login error.

Regression gates:

```powershell
pytest utility_service/use_cases/tests/test_auth_service.py utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py
npm run test -- --run src/components/LoginScreen.test.ts src/stores/auth.test.ts src/stores/workOrders.test.ts
npm run typecheck
```

Если `LoginScreen.test.ts` еще не существует, implementation plan должен
добавить минимальный component test рядом с `LoginScreen.vue`.

## Последствия

API clients получают один контракт для invalid login и workflow errors. Старые
проверки на `detail` и `details` должны быть удалены в затронутых tests и UI.

Документация `Code_wiki/архитектура/api_and_realtime.md` сейчас говорит, что
structured errors содержат `details`. После реализации это знание устареет.
Если implementation меняет код, нужно рассмотреть `/ingest repository-change`
только если изменение не будет уже достаточно сохранено в code/tests/spec.

## Проверка Spec

Документ не содержит заглушек или открытых требований. Scope ограничен auth
invalid login и structured workflow family. Широкая унификация всех backend
errors явно вынесена за пределы текущего изменения.
