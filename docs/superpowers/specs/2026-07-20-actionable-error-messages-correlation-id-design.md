# Actionable Error Messages С Correlation ID

Дата: 2026-07-20
Статус: согласован для written spec
Расположение: `docs/superpowers/specs`

## Назначение

Существующий backend уже возвращает strict structured errors для
`AuthApiError`, `UtilityNetworkApiError` и `WorkOrderApiError` в форме
`{code, message, correlationId}`. Однако frontend обрабатывает эти ответы
неодинаково: login читает только часть body, а `workOrders` store схлопывает
workflow errors в generic-строки. Пользователь не получает контекстного
следующего действия и не видит пригодную для обращения в поддержку
диагностику.

Кроме того, текущий `correlationId` генерируется непосредственно в exception
handler. В приложении нет request-level middleware и structured error logs с
тем же идентификатором. Поэтому показанный пользователю код обращения пока
нельзя надёжно сопоставить с server-side событием.

Цель изменения — создать единый сквозной путь:

```text
HTTP request
    -> request correlation context
    -> structured response и structured log
    -> frontend parser
    -> context-specific UX policy
    -> actionable UI с раскрываемой диагностикой
```

## Цели

- Создать единый frontend parser для всех текущих structured REST responses и
  подключить его к существующим non-legacy UI без чтения raw `detail`,
  `error`, HTML или произвольного response body.
- Показывать понятную причину и безопасное следующее действие в существующих
  login/session и WorkOrder/Workspace UI.
- Показывать `code` и `correlationId` в закрытой по умолчанию диагностике.
- Сделать `correlationId` единым для request context, server log, response
  header и structured error body.
- Возвращать безопасный structured `500 INTERNAL_ERROR` для непредвиденных
  backend exceptions.
- Сохранить существующие request-sequence guards и изоляцию ошибок разных
  work orders.

## Границы Scope

Входит:

- request correlation middleware для всего HTTP API;
- response header `X-Correlation-ID` для успешных и ошибочных HTTP responses;
- CORS exposure этого header;
- structured logging обработанных API errors и непредвиденных exceptions;
- strict `INTERNAL_ERROR` response;
- frontend parser для structured, unstructured HTTP, network, timeout,
  cancellation и unknown failures;
- context-specific UX policies для login, session restoration,
  WorkOrder list, open и Workspace restore/load;
- reusable actionable error component;
- parser contract и backend coverage для `UtilityNetworkApiError`;
- component, store, parser, middleware, handler и logging tests.

Не входит:

- новый Utility Network screen, store или API consumer;
- интеграция actionable UI в legacy GIS editing и realtime surfaces;
- полная миграция FastAPI request validation errors и legacy GIS domain
  errors на strict structured body;
- WebSocket close reasons и realtime observability;
- полная observability-платформа, distributed tracing, log collector или
  dashboard;
- browser-generated correlation ID;
- изменение доменных error codes;
- автоматическое исправление повреждённого доменного контекста;
- unrelated refactoring frontend stores или backend API.

Legacy GIS и FastAPI validation responses после изменения получают
`X-Correlation-ID` header, но сохраняют текущий body. Frontend не показывает
их raw body и использует безопасный HTTP fallback.

## Выбранный Подход

Выбран центральный transport parser с отдельными контекстными UX policies.

Техническая нормализация не должна решать, какую кнопку показать. Один и тот
же HTTP status или error code может требовать разных действий при загрузке
списка, открытии work order и восстановлении workspace. Поэтому parser
возвращает только проверенные transport-данные, а policy конкретной операции
формирует пользовательское представление.

Отклонённые альтернативы:

- глобальный Axios error bus: теряет контекст операции, плохо работает с
  параллельными запросами и усложняет текущий auth `401` flow;
- локальный разбор response body на каждом экране: дублирует validation,
  fallback-тексты, diagnostic UI и тесты.

## Архитектура И Ответственность Слоёв

### Backend

Request correlation middleware отвечает только за жизненный цикл request ID:

- принимает допустимый `X-Correlation-ID` или создаёт UUID;
- сохраняет значение в `request.state.correlation_id`;
- добавляет тот же ID в каждый HTTP response.

Exception handlers отвечают за публичный error contract:

- берут ID только из request context;
- формируют `{code, message, correlationId}`;
- не создают собственный ID;
- не раскрывают внутренние exception details.

Минимальный logging helper отвечает за JSON event:

- не формирует HTTP response;
- не выбирает пользовательский текст;
- не читает request body, cookies или credentials;
- использует стандартный Python logger без новой runtime-зависимости.

### Frontend

`parseApiError()` отвечает только за техническую нормализацию `unknown`:

- знает Axios response shape и public structured error contract;
- не знает Vue, Pinia и пользовательские действия;
- не показывает raw unstructured body.

Контекстные policies:

- преобразуют нормализованную ошибку в `ErrorPresentation`;
- выбирают инструкцию и безопасное действие;
- не выполняют network request самостоятельно.

`ActionableError`:

- только отображает presentation;
- emits выбранное действие;
- не знает Axios, endpoints или stores.

Stores и owning components:

- сохраняют presentation в operation-specific state;
- связывают `action.id` с существующей store action;
- очищают ошибку при новой попытке или успешном ответе;
- сохраняют существующие concurrency guards.

Направление зависимостей:

```text
Axios/unknown error
        -> parseApiError
        -> context UX policy
        -> store/component state
        -> ActionableError
```

## Backend Correlation Design

### Входной Header

Имя header остаётся `X-Correlation-ID`.

Допустимое входное значение:

- длина от 1 до 128 символов;
- только ASCII letters, digits, `.`, `_`, `:`, `-`;
- проверяется выражением, эквивалентным
  `^[A-Za-z0-9._:-]{1,128}$`.

Пустое, слишком длинное или некорректное значение не отражается обратно.
Backend заменяет его новым UUID. Это исключает control characters, log
injection и неограниченный рост log field.

Frontend не генерирует correlation ID. Если response не получен из-за DNS,
CORS, offline или другого client-side transport failure, UI честно не
показывает код обращения. Gateway и внешние API clients могут передавать
допустимый ID.

### Request Context И Response

Middleware должен оборачивать HTTP pipeline так, чтобы correlation context был
доступен exception handlers и сохранялся для successful, handled-error и
unhandled-error responses.

Каждый HTTP response получает:

```text
X-Correlation-ID: <request correlation id>
```

`CORSMiddleware` должен expose этот header браузеру. Добавление browser-side
request header не требуется, потому что frontend использует server-owned ID.

Structured body для `AuthApiError`, `UtilityNetworkApiError`,
`WorkOrderApiError` и `INTERNAL_ERROR` содержит тот же ID:

```json
{
  "code": "WORK_ORDER_NOT_FOUND",
  "message": "Рабочая задача не найдена.",
  "correlationId": "0c15b33f-c655-4cf3-962d-9b4af2b1b9cf"
}
```

Body и header не должны расходиться. На frontend header считается каноническим
на случай неожиданного mismatch, потому что его устанавливает внешний
request middleware.

### INTERNAL_ERROR

Глобальный `Exception` handler:

- логирует непредвиденный exception со stack trace;
- возвращает status `500`;
- не включает exception class, message или stack trace в response;
- возвращает strict body:

```json
{
  "code": "INTERNAL_ERROR",
  "message": "Внутренняя ошибка сервиса",
  "correlationId": "0c15b33f-c655-4cf3-962d-9b4af2b1b9cf"
}
```

## Structured Error Logging

Для текущего scope достаточно JSON events через стандартный Python logger.
Новая logging library не добавляется.

Handled error event содержит:

- `event`: `api_error_handled`;
- `correlationId`;
- `code`;
- `status`;
- `method`;
- `route`.

Unhandled event использует `event: api_error_unhandled`,
`code: INTERNAL_ERROR` и те же request fields. Stack trace добавляется только
в server log.

Уровни:

- ожидаемые structured `4xx` — `INFO`;
- обработанные structured `5xx` — `ERROR`;
- непредвиденные exceptions — `ERROR` со stack trace.

`route` содержит route template, например
`/api/v1/work-orders/{work_order_id}/edit-versions`, а не конкретный UUID.
Если template недоступен, используется безопасный marker `<unmatched>`, а не
raw URL. Query string не логируется.

Запрещено включать в эти events:

- request или response body;
- cookies;
- Authorization header;
- email, password, session token или access token;
- arbitrary incoming headers;
- raw public or internal exception message для handled `4xx`.

Каждая ошибка логируется один раз. Глобальный handler не должен дублировать
events, уже созданные typed handlers.

## Frontend Error Model

Нормализованная ошибка использует discriminated union:

```ts
type ParsedApiError =
  | {
      kind: "api";
      status: number;
      code: string;
      message: string;
      correlationId: string | null;
    }
  | {
      kind: "http";
      status: number;
      correlationId: string | null;
    }
  | {
      kind: "network" | "timeout" | "unknown";
      status: null;
      correlationId: null;
    }
  | {
      kind: "cancelled";
    };
```

`kind: "api"` означает валидную public structured error. `kind: "http"`
означает, что HTTP response получен, но body не соответствует public contract.
Такой fallback сохраняет status и exposed correlation header, но не raw body.

Пользовательское представление:

```ts
type ErrorPresentation = {
  summary: string;
  guidance: string | null;
  action: {
    id: "retry" | "refresh" | "reopen" | "sign-in";
    label: string;
  } | null;
  diagnostics: {
    code: string | null;
    correlationId: string | null;
  };
};
```

Policy может вернуть `null` для cancellation или ожидаемого initial
`AUTH_REQUIRED`, который не является пользовательской ошибкой.

## Parser Rules

Structured API error признаётся только когда:

- response status является числом;
- body является object record;
- `code` является непустой строкой;
- `message` является непустой строкой.

`correlationId` выбирается в порядке:

1. допустимый response header `X-Correlation-ID`;
2. допустимая строка `body.correlationId`;
3. `null`.

Для header и body используется одна проверка: 1–128 символов из набора
`[A-Za-z0-9._:-]`. Некорректное диагностическое значение игнорируется.

Если body и header расходятся, используется header. Parser не показывает
пользователю предупреждение о mismatch, но unit test фиксирует правило.

Raw `detail`, `details`, `error`, response text и HTML никогда не используются
как `summary`. Для `kind: "http"` policy формирует безопасный контекстный
fallback.

Transport categories:

- Axios cancellation — `cancelled` и отсутствие alert;
- timeout — `timeout`;
- request без response — `network`;
- response с невалидным body — `http`;
- не-Axios и нераспознанное значение — `unknown`.

## UX Policies

Общее правило:

- backend `message` объясняет причину только для валидной structured error;
- frontend добавляет конкретную инструкцию;
- frontend выбирает только безопасное действие;
- если рядом уже есть эквивалентная primary action, component не дублирует её.

### Login И Session

| Code/condition | Guidance | Action |
|---|---|---|
| `INVALID_CREDENTIALS` | Проверить электронную почту и пароль | Повторная отправка существующей login form |
| `USER_INACTIVE` | Обратиться к администратору | Нет безопасного повтора |
| Initial restore: `AUTH_REQUIRED` | Обычное отсутствие действующей сессии | Alert отсутствует |
| Runtime: `AUTH_REQUIRED` | Сессия завершена; требуется новый вход | `sign-in` |
| Restore network/timeout/`5xx` | Проверить соединение и повторить | `retry` |

### WorkOrder И Workspace

| Code/condition | Guidance | Action |
|---|---|---|
| List network/timeout/`5xx` | Проверить соединение и повторить | `retry` |
| `WORK_ORDER_NOT_FOUND` | Список назначений мог измениться | `refresh` |
| `WORK_ORDER_NOT_ASSIGNED` | Наряд больше не назначен текущему пользователю | `refresh` |
| `WORK_ORDER_STATE_CONFLICT` | Состояние наряда изменилось | `refresh` |
| `WORK_ORDER_CONTEXT_INVALID` | Повтор не устранит повреждённый контекст; передать код поддержке | Нет действия |
| `EDIT_VERSION_NOT_FOUND` при restore | Сохранённая версия больше недоступна | `reopen` |
| `EDIT_VERSION_STATE_CONFLICT` | Состояние рабочей версии изменилось | `refresh` |
| `WORKSPACE_CONTEXT_INVALID` | Workspace нельзя сформировать; передать код поддержке | Нет действия |
| `ROLE_NOT_ALLOWED` | Обратиться к администратору, если доступ должен быть предоставлен | Нет действия |
| Неизвестный structured `4xx` | Показать public backend reason без догадок о восстановлении | Обычно нет действия |
| Network/timeout/`5xx` | Контекстный безопасный fallback | Повтор текущей операции |

`WORK_ORDER_ACTOR_NOT_FOUND` обрабатывается как account/session inconsistency:
пользователю предлагается новый вход, а не повтор workflow request.

### Utility Network

`FEEDER_NOT_FOUND` и `UTILITY_DATASET_INVALID` используются как structured
fixtures в parser contract tests и покрываются backend observability tests.
Существующего frontend consumer для endpoint нет, поэтому отдельная UX policy
и UI integration не создаются.

## Actionable Error Component

`ActionableError` показывает два уровня информации.

Основной уровень:

- `summary`;
- optional `guidance`;
- optional action button.

Диагностический уровень:

- закрытый по умолчанию `<details>` с label `Технические сведения`;
- `code` с пользовательским label `Код ошибки`;
- полный `correlationId` с label `Код обращения`;
- кнопка `Копировать код обращения` только при наличии correlation ID.

Компонент:

- использует `role="alert"` для error content;
- сообщает результат копирования через отдельный `aria-live="polite"` region;
- emits `action.id`, но не выполняет request;
- не скрывает полный ID при clipboard failure;
- позволяет выделить ID вручную;
- использует перенос длинного ID вместо визуального обрезания.

После успешного копирования показывается текст `Код обращения скопирован`.
Clipboard failure не заменяет исходную ошибку и не создаёт новый global alert.

## Интеграция С Текущим Frontend

### Auth Store И HTTP Interceptor

`sessionError: string | null` заменяется на
`sessionError: ErrorPresentation | null`.

Initial `restoreSession()`:

- `AUTH_REQUIRED` очищает local session и не создаёт alert;
- network/timeout/`5xx` создаёт retry presentation;
- `USER_INACTIVE` создаёт presentation без автоматического retry.

Runtime `401 AUTH_REQUIRED`:

- interceptor проверяет, существовала ли активная in-memory session до
  очистки;
- при активной session очищает auth и workOrders state, затем сохраняет
  presentation `Сессия завершена`;
- для уже anonymous пользователя не создаёт session alert;
- действие `sign-in` очищает session error и открывает обычный login screen.

Login form хранит собственную presentation, использует общий parser и login
policy. Кнопка `Войти` остаётся единственным повторным действием и не
дублируется внутри `ActionableError`.

### WorkOrders Store

State уточняется:

- `errorMessage` заменяется на `loadError: ErrorPresentation | null`;
- `openWorkspaceErrorByWorkOrderId` хранит
  `Record<string, ErrorPresentation | undefined>`.

`loadAssigned()`, `openSelectedWorkOrder()` и `restoreOpenedWorkspace()`:

- очищают соответствующую ошибку перед новой попыткой;
- normalise и present failure в catch;
- сохраняют существующие request sequence checks;
- не позволяют stale response вернуть старую ошибку;
- очищают ошибку после успеха.

Действия:

- `retry` повторяет ровно исходную операцию;
- `refresh` вызывает `loadAssigned()` и не открывает workspace автоматически;
- `reopen` сначала гарантирует очистку stale stored workspace marker, затем
  вызывает обычный open flow;
- context-invalid errors не меняют workspace и не запускают retry.

Keyed error другого work order не отображается после смены выбора и не
перезаписывает ошибку текущего work order. Полный reset очищает все error
slots.

### Components

`ActionableError` переиспользуется в:

- `LoginScreen`;
- session status state в `App`;
- list state в `EditorWorkOrdersView`;
- preview/open state в `WorkspaceDetailsPanel`.

Owning component связывает emitted action с store method. UI component не
импортирует stores.

## Error State Lifecycle

- Новая попытка очищает ошибку своей операции до request.
- Success оставляет error slot пустым.
- Cancellation не создаёт presentation.
- Ошибка устаревшего request игнорируется существующим sequence guard.
- Logout и user-id change выполняют полный workOrders reset.
- Ошибка открытия одного work order не блокирует выбор другого.
- Ошибка восстановления stale edit version удаляет persisted marker до
  предложения `Открыть заново`.
- Необработанный clipboard failure не влияет на operation state.

## Testing

### Backend

Middleware tests проверяют:

- генерацию UUID без входного header;
- сохранение допустимого incoming ID;
- замену пустого, длинного и некорректного ID;
- одинаковый header для success, handled error и unhandled error;
- CORS exposure `X-Correlation-ID`.

Exception handler tests проверяют:

- strict body для существующих typed errors;
- равенство body и header ID;
- безопасный `500 INTERNAL_ERROR`;
- отсутствие exception text и stack trace в response;
- сохранение текущих `code`, `message` и statuses.

Logging tests через captured logs проверяют:

- parseable JSON event;
- обязательные fields;
- `INFO` для handled `4xx`;
- `ERROR` для handled и unhandled `5xx`;
- stack trace только для unhandled exception;
- route template вместо query string и concrete IDs;
- отсутствие Authorization, cookies, request body и test secret markers.

### Frontend Parser И Policies

Parser tests проверяют:

- valid structured body;
- header priority и body fallback;
- header/body mismatch;
- malformed и legacy body без raw text exposure;
- `http` fallback с status и correlation header;
- network, timeout, cancellation и unknown errors.

Policy table tests проверяют каждый перечисленный code/action, initial silent
`AUTH_REQUIRED`, runtime `AUTH_REQUIRED`, unknown `4xx` и retryable
network/`5xx` paths.

### Frontend Components И Stores

Component tests проверяют:

- summary, guidance и optional action;
- закрытый по умолчанию diagnostic details;
- отображение code и полного correlation ID;
- emitted action;
- successful copy, clipboard failure и `aria-live` confirmation;
- `role="alert"` и отсутствие duplicate primary action.

Store/interceptor tests проверяют:

- initial `AUTH_REQUIRED` без session error;
- runtime `AUTH_REQUIRED` с sign-in presentation;
- retry restoration для network/`5xx`;
- structured login error;
- list/open/restore presentations;
- keyed error isolation;
- очистку при retry и success;
- stale marker cleanup до reopen;
- сохранение request-sequence behavior.

### Regression Gates

Backend:

```powershell
pytest utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py utility_service/web_api/tests/test_utility_network_api.py
ruff check utility_service
```

Frontend:

```powershell
npm run test -- --run
npm run typecheck
npm run build
```

Implementation plan должен уточнить наиболее узкий red/green test order и при
необходимости выделить новые focused test files для parser, policies,
middleware и logging.

## Критерии Готовности

- Каждый текущий structured REST error использует один correlation ID в
  request context, structured log, response header и body.
- Все существующие login/session и WorkOrder/Workspace error surfaces
  показывают причину, безопасное действие и раскрываемую диагностику.
- Неструктурированные HTTP responses не раскрывают raw backend body.
- Unexpected backend exception возвращает безопасный `INTERNAL_ERROR` и имеет
  searchable server log с тем же ID.
- Frontend не создаёт correlation ID при отсутствии server response.
- Initial anonymous session restoration не выглядит как ошибка.
- Existing auth reset, workspace persistence и request-sequence tests не
  регрессируют.
- Utility Network contract и logging покрыты без создания нового UI.
- Legacy GIS, WebSocket и полная миграция validation errors остаются за
  пределами изменения.

## Последствия

Положительные:

- support получает воспроизводимый код обращения;
- пользователь получает конкретное следующее действие вместо generic error;
- parsing, UX policy и rendering тестируются независимо;
- дальнейшие structured REST consumers могут переиспользовать тот же путь.

Компромиссы:

- frontend получает несколько новых небольших типов и policy functions;
- часть старых API responses остаётся только safe fallback;
- server-owned correlation ID отсутствует при client-side failure без HTTP
  response;
- полноценная observability всё ещё требует отдельной задачи.

## Дальнейший Процесс

После пользовательской проверки этой written spec следующий шаг — создать
детальный implementation plan через `superpowers:writing-plans`. До отдельного
одобрения implementation plan production-код не изменяется.
