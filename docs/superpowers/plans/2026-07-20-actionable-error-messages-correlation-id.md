# Actionable Error Messages With Correlation ID Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить сквозной server-owned `correlationId`, безопасные structured error logs и единый actionable error UX для существующих login/session и WorkOrder/Workspace REST flows.

**Architecture:** Чистый ASGI middleware создаёт request correlation context, typed handlers возвращают и логируют один strict contract, а внешний `CORSMiddleware` сохраняет CORS headers даже для `INTERNAL_ERROR`. Frontend сначала нормализует transport error в `ParsedApiError`, затем context policy формирует `ErrorPresentation`, а reusable Vue component только отображает сообщение, действие и диагностику.

**Tech Stack:** Python 3.12, FastAPI 0.115.6, Starlette, standard-library `logging`/`json`, pytest/httpx; Vue 3.5, TypeScript 5.9, Axios 1.13, Pinia 3, Vitest 3.2, Vue Test Utils, jsdom.

## Global Constraints

- Источник дизайна: `docs/superpowers/specs/2026-07-20-actionable-error-messages-correlation-id-design.md`.
- Human-readable UI и application log messages пишутся на русском; API paths, JSON keys, error `code`, event identifiers, types и identifiers остаются на английском.
- Публичный structured body содержит только `{code, message, correlationId}`.
- Incoming correlation ID допустим только по `^[A-Za-z0-9._:-]{1,128}$`; иначе backend создаёт UUID.
- Frontend не создаёт correlation ID и не показывает raw `detail`, `details`, `error`, HTML или произвольный response body.
- Не добавлять runtime dependencies: backend использует standard-library logging, frontend — уже установленный Axios/Vue stack.
- Initial `AUTH_REQUIRED` при `restoreSession()` остаётся тихим; runtime `AUTH_REQUIRED` переводит пользователя в actionable sign-in state.
- Не создавать Utility Network UI и не расширять scope на legacy GIS, WebSocket или полную миграцию validation errors.
- Сохранить существующие request-sequence guards, user-scoped reset и workspace persistence semantics.
- В этом репозитории агентам запрещены `git add`, `git commit` и `git push`. Все изменения остаются unstaged; каждый task заканчивается read-only review checkpoint вместо commit.
- Реализацию вести TDD: сначала focused failing test, затем минимальный production code, затем focused и regression tests.

## File Structure

Backend:

- Create `apps/backend/utility_service/web_api/middleware/__init__.py` — package boundary.
- Create `apps/backend/utility_service/web_api/middleware/correlation_id.py` — validation, request state и response header.
- Create `apps/backend/utility_service/web_api/observability/__init__.py` — package boundary.
- Create `apps/backend/utility_service/web_api/observability/api_error_logging.py` — JSON events без HTTP response logic.
- Create `apps/backend/utility_service/web_api/tests/test_correlation_id_middleware.py` — middleware/CORS contract.
- Modify `apps/backend/utility_service/web_api/api/exception_handlers.py` — typed logging и safe `INTERNAL_ERROR`.
- Modify `apps/backend/utility_service/web_api/main.py` — middleware order и outer CORS wrapper.
- Modify `apps/backend/utility_service/web_api/tests/test_exception_handlers.py` — strict body/header/log regression coverage.

Frontend shared error path:

- Create `apps/frontend/src/contracts/api-error.ts` — discriminated unions and shared identifiers.
- Create `apps/frontend/src/api/parseApiError.ts` and `parseApiError.test.ts` — transport normalization.
- Create `apps/frontend/src/errors/apiErrorPresentations.ts` and `.test.ts` — context policies.
- Create `apps/frontend/src/components/ActionableError.vue` and `.test.ts` — reusable accessible UI.

Frontend integration:

- Modify `apps/frontend/src/stores/auth.ts` and `.test.ts` — structured session state.
- Modify `apps/frontend/src/api/http.ts` and `.test.ts` — runtime unauthorized handoff.
- Modify `apps/frontend/src/components/LoginScreen.vue` and `.test.ts` — login policy/UI.
- Modify `apps/frontend/src/App.vue` and `.test.ts` — session recovery/sign-in UI.
- Modify `apps/frontend/src/stores/workOrders.ts` and `.test.ts` — operation-specific presentations and retries.
- Modify `apps/frontend/src/components/EditorWorkOrdersView.vue` and `.test.ts` — list/workspace action routing.
- Modify `apps/frontend/src/components/WorkspaceDetailsPanel.vue` and `.test.ts` — contextual error replacement for the normal open action.

---

### Task 1: Request Correlation Middleware And CORS Boundary

**Files:**

- Create: `apps/backend/utility_service/web_api/middleware/__init__.py`
- Create: `apps/backend/utility_service/web_api/middleware/correlation_id.py`
- Create: `apps/backend/utility_service/web_api/tests/test_correlation_id_middleware.py`
- Modify: `apps/backend/utility_service/web_api/main.py`

**Interfaces:**

- Consumes: Starlette ASGI `scope`, incoming `X-Correlation-ID`.
- Produces: `CORRELATION_ID_HEADER`, `CorrelationIdMiddleware`, `is_valid_correlation_id(value: object) -> bool`, `get_correlation_id(request: Request) -> str`.
- Later tasks rely on `request.state.correlation_id` and the exported header constant.

- [ ] **Step 1: Add focused failing tests for validation and response propagation**

Create `test_correlation_id_middleware.py`:

```python
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from utility_service.web_api.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
    is_valid_correlation_id,
)


def create_test_app():
    api = FastAPI()
    api.add_middleware(CorrelationIdMiddleware)

    @api.get("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    return CORSMiddleware(
        app=api,
        allow_origins=["http://frontend.local"],
        allow_methods=["GET"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=[CORRELATION_ID_HEADER],
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("request-123", True),
        ("a.b_c:d-1", True),
        ("", False),
        ("contains space", False),
        ("x" * 129, False),
        (None, False),
    ],
)
def test_correlation_id_validation(value: object, expected: bool) -> None:
    assert is_valid_correlation_id(value) is expected


def test_missing_header_generates_uuid() -> None:
    response = TestClient(create_test_app()).get("/ok")

    assert response.status_code == 200
    UUID(response.headers[CORRELATION_ID_HEADER])


def test_valid_header_is_preserved() -> None:
    response = TestClient(create_test_app()).get(
        "/ok",
        headers={CORRELATION_ID_HEADER: "client-request-123"},
    )

    assert response.headers[CORRELATION_ID_HEADER] == "client-request-123"


def test_invalid_header_is_replaced() -> None:
    response = TestClient(create_test_app()).get(
        "/ok",
        headers={CORRELATION_ID_HEADER: "contains space"},
    )

    generated = response.headers[CORRELATION_ID_HEADER]
    UUID(generated)
    assert generated != "contains space"


def test_cors_exposes_correlation_header() -> None:
    response = TestClient(create_test_app()).get(
        "/ok",
        headers={"Origin": "http://frontend.local"},
    )

    assert response.headers["access-control-allow-origin"] == "http://frontend.local"
    assert CORRELATION_ID_HEADER in response.headers["access-control-expose-headers"]
```

- [ ] **Step 2: Run the new test and verify the missing module failure**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_correlation_id_middleware.py -q
```

Expected: collection fails with `ModuleNotFoundError` for
`utility_service.web_api.middleware`.

- [ ] **Step 3: Implement the pure ASGI middleware**

Create an empty `middleware/__init__.py`, then create
`middleware/correlation_id.py`:

```python
from __future__ import annotations

import re
from uuid import uuid4

from fastapi import Request
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


CORRELATION_ID_HEADER = "X-Correlation-ID"
CORRELATION_ID_STATE_KEY = "correlation_id"
_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def is_valid_correlation_id(value: object) -> bool:
    return isinstance(value, str) and _CORRELATION_ID_PATTERN.fullmatch(value) is not None


def get_correlation_id(request: Request) -> str:
    correlation_id = getattr(request.state, CORRELATION_ID_STATE_KEY, None)
    if not is_valid_correlation_id(correlation_id):
        raise RuntimeError("CorrelationIdMiddleware не установил request correlation ID")
    return correlation_id


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(CORRELATION_ID_HEADER)
        correlation_id = incoming if is_valid_correlation_id(incoming) else str(uuid4())
        scope.setdefault("state", {})[CORRELATION_ID_STATE_KEY] = correlation_id

        async def send_with_correlation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[CORRELATION_ID_HEADER] = correlation_id
            await send(message)

        await self.app(scope, receive, send_with_correlation_id)
```

- [ ] **Step 4: Run middleware unit tests**

Run:

```powershell
pytest utility_service/web_api/tests/test_correlation_id_middleware.py -q
```

Expected: `10 passed`.

- [ ] **Step 5: Rebuild the main ASGI boundary with outer CORS**

Replace the app construction in `main.py` with this exact shape while keeping
the existing router imports:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utility_service.web_api.api.lifespan import lifespan
from utility_service.web_api.api.auth import auth_router
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.secure_router import secure_router
from utility_service.web_api.api.utility_network import utility_network_router
from utility_service.web_api.api.layers import layers_router
from utility_service.web_api.api.ws_layers import ws_layers_router
from utility_service.web_api.api.work_orders import work_orders_router
from utility_service.web_api.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
)
from utility_service.utils.settings import settings


api = FastAPI(lifespan=lifespan)
api.add_middleware(CorrelationIdMiddleware)

api.include_router(auth_router)
api.include_router(utility_network_router)
api.include_router(secure_router)
api.include_router(layers_router)
api.include_router(ws_layers_router)
api.include_router(work_orders_router)


@api.get("/health")
def health():
    return {"ok": True}


install_exception_handlers(api)

app = CORSMiddleware(
    app=api,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=[CORRELATION_ID_HEADER],
)
```

Outer CORS is intentional: Starlette's server error middleware surrounds
FastAPI user middleware, so an outer wrapper is required for CORS headers on
the later `INTERNAL_ERROR` response.

- [ ] **Step 6: Add and run a main-boundary health regression test**

Append to `test_correlation_id_middleware.py`:

```python
def test_main_health_uses_production_correlation_boundary() -> None:
    from utility_service.web_api.main import app
    from utility_service.utils.settings import settings

    origin = settings.cors_origins[0]

    response = TestClient(app).get(
        "/health",
        headers={"Origin": origin},
    )

    assert response.status_code == 200
    UUID(response.headers[CORRELATION_ID_HEADER])
    assert response.headers["access-control-allow-origin"] == origin
    assert CORRELATION_ID_HEADER in response.headers["access-control-expose-headers"]
```

Run:

```powershell
pytest utility_service/web_api/tests/test_correlation_id_middleware.py -q
```

Expected: `11 passed`; production app uses the first configured origin without
changing `settings.cors_origins` in this feature.

- [ ] **Step 7: Review checkpoint**

Run:

```powershell
ruff check utility_service/web_api/middleware utility_service/web_api/main.py utility_service/web_api/tests/test_correlation_id_middleware.py
git diff --check
git status --short
```

Expected: Ruff and diff checks pass; only intended unstaged files are listed.

---

### Task 2: Structured API Error Logging And INTERNAL_ERROR

**Files:**

- Create: `apps/backend/utility_service/web_api/observability/__init__.py`
- Create: `apps/backend/utility_service/web_api/observability/api_error_logging.py`
- Modify: `apps/backend/utility_service/web_api/api/exception_handlers.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_exception_handlers.py`

**Interfaces:**

- Consumes: `get_correlation_id(request)` and typed exception status/code/message.
- Produces: `API_ERROR_LOGGER_NAME`,
  `log_handled_api_error(request: Request, *, code: str, status: int) -> None`,
  `log_unhandled_api_error(request: Request, error: Exception) -> None`, strict
  response headers/body.
- Frontend parser tests later rely on `X-Correlation-ID` being present even
  when a body is unstructured.

- [ ] **Step 1: Update the test app boundary and write failing strict/log tests**

In `test_exception_handlers.py`, make `create_test_app()` build an inner
FastAPI app with `CorrelationIdMiddleware`, install handlers, add the existing
routes plus these two routes, then return an outer `CORSMiddleware`:

```python
@api.get("/utility-invalid")
def utility_invalid() -> None:
    raise UtilityNetworkApiError(
        500,
        "UTILITY_DATASET_INVALID",
        "Utility dataset поврежден и не может быть прочитан.",
    )


@api.get("/work-orders/{work_order_id}")
def unexpected_value_error(work_order_id: str) -> None:
    raise ValueError(f"Внутренняя ошибка для {work_order_id}")
```

Use this wrapping code:

```python
api.add_middleware(CorrelationIdMiddleware)
install_exception_handlers(api)
return CORSMiddleware(
    app=api,
    allow_origins=["http://frontend.local"],
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=[CORRELATION_ID_HEADER],
)
```

Add imports for `json`, `logging`, `CORSMiddleware`, the correlation exports,
and `API_ERROR_LOGGER_NAME`. Add these tests:

```python
def test_unexpected_error_returns_safe_structured_500(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger=API_ERROR_LOGGER_NAME):
        response = client.get(
            "/work-orders/wo-secret?token=query-secret",
            headers={
                "Origin": "http://frontend.local",
                "Authorization": "Bearer auth-secret",
                "Cookie": "geoservice_session=cookie-secret",
                CORRELATION_ID_HEADER: "internal-correlation-id",
            },
        )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Внутренняя ошибка сервиса",
        "correlationId": "internal-correlation-id",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "internal-correlation-id"
    assert response.headers["access-control-allow-origin"] == "http://frontend.local"
    assert "wo-secret" not in response.text

    records = [record for record in caplog.records if record.name == API_ERROR_LOGGER_NAME]
    assert len(records) == 1
    record = records[0]
    event = json.loads(record.getMessage())
    assert event == {
        "event": "api_error_unhandled",
        "correlationId": "internal-correlation-id",
        "code": "INTERNAL_ERROR",
        "status": 500,
        "method": "GET",
        "route": "/work-orders/{work_order_id}",
    }
    assert record.exc_info is not None
    assert "query-secret" not in record.getMessage()
    assert "auth-secret" not in record.getMessage()
    assert "cookie-secret" not in record.getMessage()


def test_handled_4xx_writes_sanitized_info_event(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.INFO, logger=API_ERROR_LOGGER_NAME):
        response = client.get(
            "/auth-required?token=query-secret",
            headers={
                "Authorization": "Bearer auth-secret",
                CORRELATION_ID_HEADER: "auth-correlation-id",
            },
        )

    records = [record for record in caplog.records if record.name == API_ERROR_LOGGER_NAME]
    assert len(records) == 1
    record = records[0]
    event = json.loads(record.getMessage())
    assert record.levelno == logging.INFO
    assert record.exc_info is None
    assert event == {
        "event": "api_error_handled",
        "correlationId": "auth-correlation-id",
        "code": "AUTH_REQUIRED",
        "status": 401,
        "method": "GET",
        "route": "/auth-required",
    }
    assert response.headers[CORRELATION_ID_HEADER] == "auth-correlation-id"
    assert "query-secret" not in record.getMessage()
    assert "auth-secret" not in record.getMessage()


def test_handled_5xx_writes_error_without_exception_trace(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger=API_ERROR_LOGGER_NAME):
        response = client.get(
            "/utility-invalid",
            headers={CORRELATION_ID_HEADER: "utility-correlation-id"},
        )

    records = [record for record in caplog.records if record.name == API_ERROR_LOGGER_NAME]
    assert len(records) == 1
    record = records[0]
    event = json.loads(record.getMessage())
    assert response.status_code == 500
    assert record.levelno == logging.ERROR
    assert record.exc_info is None
    assert event["code"] == "UTILITY_DATASET_INVALID"
    assert event["correlationId"] == "utility-correlation-id"
```

Also add header equality assertions to the existing Auth, Utility and
WorkOrder strict body tests. In the legacy business-validation test, validate
that `UUID(response.headers[CORRELATION_ID_HEADER])` succeeds while its body
remains `{"error": "Некорректный bbox"}`.

- [ ] **Step 2: Run the focused tests and verify missing observability behavior**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_exception_handlers.py -q
```

Expected: failures for the non-structured 500 response, missing logger module,
missing response headers in the old test app, or absent log records.

- [ ] **Step 3: Implement the JSON logging helper**

Create an empty `observability/__init__.py`, then create
`observability/api_error_logging.py`:

```python
from __future__ import annotations

import json
import logging

from fastapi import Request

from utility_service.web_api.middleware.correlation_id import get_correlation_id


API_ERROR_LOGGER_NAME = "utility_service.api_errors"
_logger = logging.getLogger(API_ERROR_LOGGER_NAME)


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) and path else "<unmatched>"


def _event(request: Request, *, event: str, code: str, status: int) -> dict[str, object]:
    return {
        "event": event,
        "correlationId": get_correlation_id(request),
        "code": code,
        "status": status,
        "method": request.method,
        "route": _route_template(request),
    }


def log_handled_api_error(request: Request, *, code: str, status: int) -> None:
    level = logging.INFO if status < 500 else logging.ERROR
    payload = _event(request, event="api_error_handled", code=code, status=status)
    _logger.log(level, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def log_unhandled_api_error(request: Request, error: Exception) -> None:
    payload = _event(
        request,
        event="api_error_unhandled",
        code="INTERNAL_ERROR",
        status=500,
    )
    _logger.error(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        exc_info=(type(error), error, error.__traceback__),
    )
```

- [ ] **Step 4: Centralize strict responses and add the global handler**

In `exception_handlers.py`, import `CORRELATION_ID_HEADER`,
`get_correlation_id`, `log_handled_api_error`, and
`log_unhandled_api_error`. Replace `structured_error_response()` and add the
global handler inside `install_exception_handlers()`:

```python
def structured_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    correlation_id = get_correlation_id(request)
    log_handled_api_error(request, code=code, status=status_code)
    return JSONResponse(
        status_code=status_code,
        headers={CORRELATION_ID_HEADER: correlation_id},
        content={
            "code": code,
            "message": message,
            "correlationId": correlation_id,
        },
    )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_api_error(request: Request, error: Exception):
        correlation_id = get_correlation_id(request)
        log_unhandled_api_error(request, error)
        return JSONResponse(
            status_code=500,
            headers={CORRELATION_ID_HEADER: correlation_id},
            content={
                "code": "INTERNAL_ERROR",
                "message": "Внутренняя ошибка сервиса",
                "correlationId": correlation_id,
            },
        )
```

Keep all existing typed and legacy handlers below this addition. Typed
`AuthApiError`, `UtilityNetworkApiError` and `WorkOrderApiError` continue to
call `structured_error_response`; legacy handlers retain their current body.
Remove the unused `uuid4` import.

- [ ] **Step 5: Run focused backend tests**

Run:

```powershell
pytest utility_service/web_api/tests/test_correlation_id_middleware.py utility_service/web_api/tests/test_exception_handlers.py -q
```

Expected: all middleware, strict body, header and logging tests pass.

- [ ] **Step 6: Run structured API regression tests**

Run:

```powershell
pytest utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py utility_service/web_api/tests/test_utility_network_api.py -q
```

Expected: existing structured bodies remain exact and all tests pass. If a
test app installs exception handlers without correlation middleware, update
that test app to mirror the production boundary; do not add UUID generation
back into handlers.

- [ ] **Step 7: Review checkpoint**

Run:

```powershell
ruff check utility_service/web_api/api/exception_handlers.py utility_service/web_api/observability utility_service/web_api/tests/test_exception_handlers.py
git diff --check
git status --short
```

Expected: checks pass and no dependency files changed.

---

### Task 3: Frontend Transport Error Contract And Parser

**Files:**

- Create: `apps/frontend/src/contracts/api-error.ts`
- Create: `apps/frontend/src/api/parseApiError.ts`
- Create: `apps/frontend/src/api/parseApiError.test.ts`

**Interfaces:**

- Consumes: Axios error-like `unknown` and response header/body.
- Produces: `ParsedApiError`, `ErrorPresentation`, `ErrorActionId`,
  `parseApiError(error: unknown) -> ParsedApiError`.
- Policies and stores in later tasks import only these exports.

- [ ] **Step 1: Write parser tests for every transport category**

Create `parseApiError.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { parseApiError } from "@/api/parseApiError";

function axiosFailure(args: {
  status?: number;
  data?: unknown;
  headers?: Record<string, unknown>;
  code?: string;
  cancelled?: boolean;
}) {
  return {
    isAxiosError: true,
    code: args.code,
    __CANCEL__: args.cancelled,
    response:
      args.status === undefined
        ? undefined
        : {
            status: args.status,
            data: args.data,
            headers: args.headers ?? {},
          },
  };
}

describe("parseApiError", () => {
  it("parses a structured error and prefers the response header", () => {
    const parsed = parseApiError(
      axiosFailure({
        status: 404,
        headers: { "x-correlation-id": "header-id" },
        data: {
          code: "FEEDER_NOT_FOUND",
          message: "Фидер не найден.",
          correlationId: "body-id",
        },
      }),
    );

    expect(parsed).toEqual({
      kind: "api",
      status: 404,
      code: "FEEDER_NOT_FOUND",
      message: "Фидер не найден.",
      correlationId: "header-id",
    });
  });

  it("uses the structured body correlation id as fallback", () => {
    expect(
      parseApiError(
        axiosFailure({
          status: 401,
          data: {
            code: "AUTH_REQUIRED",
            message: "Сессия недействительна.",
            correlationId: "body-id",
          },
        }),
      ),
    ).toMatchObject({ kind: "api", correlationId: "body-id" });
  });

  it("keeps only status and header for an unstructured HTTP body", () => {
    expect(
      parseApiError(
        axiosFailure({
          status: 422,
          headers: { "X-Correlation-ID": "validation-id" },
          data: { detail: "raw detail must stay hidden" },
        }),
      ),
    ).toEqual({ kind: "http", status: 422, correlationId: "validation-id" });
  });

  it("ignores invalid diagnostic identifiers", () => {
    expect(
      parseApiError(
        axiosFailure({
          status: 500,
          headers: { "x-correlation-id": "contains space" },
          data: {
            code: "INTERNAL_ERROR",
            message: "Внутренняя ошибка сервиса",
            correlationId: "also invalid",
          },
        }),
      ),
    ).toMatchObject({ kind: "api", correlationId: null });
  });

  it.each([
    [axiosFailure({ code: "ECONNABORTED" }), "timeout"],
    [axiosFailure({ code: "ETIMEDOUT" }), "timeout"],
    [axiosFailure({}), "network"],
    [axiosFailure({ code: "ERR_CANCELED", cancelled: true }), "cancelled"],
    [new Error("not axios"), "unknown"],
  ])("classifies transport failure %#", (error, kind) => {
    expect(parseApiError(error).kind).toBe(kind);
  });
});
```

- [ ] **Step 2: Run the parser test and verify missing modules**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/api/parseApiError.test.ts
```

Expected: FAIL because `parseApiError` and the contract file do not exist.

- [ ] **Step 3: Define the shared contract**

Create `contracts/api-error.ts`:

```ts
export type ErrorActionId = "retry" | "refresh" | "reopen" | "sign-in";

export type ParsedApiError =
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
  | { kind: "cancelled" };

export type ErrorPresentation = {
  summary: string;
  guidance: string | null;
  action: { id: ErrorActionId; label: string } | null;
  diagnostics: {
    code: string | null;
    correlationId: string | null;
  };
};

const CORRELATION_ID_PATTERN = /^[A-Za-z0-9._:-]{1,128}$/;

export function isValidCorrelationId(value: unknown): value is string {
  return typeof value === "string" && CORRELATION_ID_PATTERN.test(value);
}
```

- [ ] **Step 4: Implement minimal transport parsing**

Create `api/parseApiError.ts`:

```ts
import axios from "axios";

import {
  isValidCorrelationId,
  type ParsedApiError,
} from "@/contracts/api-error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function nonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function headerValue(headers: unknown, name: string): unknown {
  if (!isRecord(headers)) {
    return undefined;
  }

  const get = headers.get;
  if (typeof get === "function") {
    return get.call(headers, name);
  }

  const entry = Object.entries(headers).find(
    ([key]) => key.toLowerCase() === name.toLowerCase(),
  );
  return entry?.[1];
}

function responseCorrelationId(headers: unknown, body: unknown): string | null {
  const fromHeader = headerValue(headers, "X-Correlation-ID");
  if (isValidCorrelationId(fromHeader)) {
    return fromHeader;
  }
  if (isRecord(body) && isValidCorrelationId(body.correlationId)) {
    return body.correlationId;
  }
  return null;
}

export function parseApiError(error: unknown): ParsedApiError {
  if (axios.isCancel(error)) {
    return { kind: "cancelled" };
  }
  if (!axios.isAxiosError(error)) {
    return { kind: "unknown", status: null, correlationId: null };
  }
  if (error.code === "ERR_CANCELED") {
    return { kind: "cancelled" };
  }
  if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT") {
    return { kind: "timeout", status: null, correlationId: null };
  }
  if (!error.response) {
    return { kind: "network", status: null, correlationId: null };
  }

  const { status, data, headers } = error.response;
  const correlationId = responseCorrelationId(headers, data);
  if (
    isRecord(data) &&
    nonEmptyString(data.code) &&
    nonEmptyString(data.message)
  ) {
    return {
      kind: "api",
      status,
      code: data.code.trim(),
      message: data.message.trim(),
      correlationId,
    };
  }
  return { kind: "http", status, correlationId };
}
```

- [ ] **Step 5: Run parser tests and typecheck**

Run:

```powershell
npm run test -- --run src/api/parseApiError.test.ts
npm run typecheck
```

Expected: parser tests and typecheck pass. If TypeScript rejects `headers.get`,
replace only `headerValue()` with a narrow local interface
`{get(name: string): unknown}`; do not cast the entire Axios response to `any`.

- [ ] **Step 6: Review checkpoint**

Run:

```powershell
npm run lint -- --no-fix
git diff --check
git status --short
```

Expected: no lint errors and only intended unstaged files.

---

### Task 4: Context-Specific Error Presentation Policies

**Files:**

- Create: `apps/frontend/src/errors/apiErrorPresentations.ts`
- Create: `apps/frontend/src/errors/apiErrorPresentations.test.ts`

**Interfaces:**

- Consumes: `ParsedApiError`.
- Produces: `presentLoginError`, `presentSessionError`,
  `presentWorkOrdersLoadError`, `presentWorkspaceOpenError`,
  `presentWorkspaceRestoreError`.
- Each function returns `ErrorPresentation | null`; only cancellation and
  initial anonymous `AUTH_REQUIRED` return `null`.

- [ ] **Step 1: Write table-driven failing policy tests**

Create `apiErrorPresentations.test.ts` with helpers and exact cases:

```ts
import { describe, expect, it } from "vitest";

import type { ParsedApiError } from "@/contracts/api-error";
import {
  presentLoginError,
  presentSessionError,
  presentWorkOrdersLoadError,
  presentWorkspaceOpenError,
  presentWorkspaceRestoreError,
} from "@/errors/apiErrorPresentations";

function api(code: string, status: number, message = `Причина ${code}`): ParsedApiError {
  return { kind: "api", code, status, message, correlationId: "request-id" };
}

const network: ParsedApiError = {
  kind: "network",
  status: null,
  correlationId: null,
};

describe("api error presentations", () => {
  it("keeps invalid credentials actionable through the existing form", () => {
    expect(presentLoginError(api("INVALID_CREDENTIALS", 401))).toEqual({
      summary: "Причина INVALID_CREDENTIALS",
      guidance: "Проверьте электронную почту и пароль.",
      action: null,
      diagnostics: { code: "INVALID_CREDENTIALS", correlationId: "request-id" },
    });
  });

  it("keeps initial AUTH_REQUIRED silent", () => {
    expect(presentSessionError(api("AUTH_REQUIRED", 401), "initial")).toBeNull();
  });

  it("turns runtime AUTH_REQUIRED into sign-in action", () => {
    expect(presentSessionError(api("AUTH_REQUIRED", 401), "runtime")).toMatchObject({
      action: { id: "sign-in", label: "Войти снова" },
    });
  });

  it.each([
    ["WORK_ORDER_NOT_FOUND", "refresh"],
    ["WORK_ORDER_NOT_ASSIGNED", "refresh"],
    ["WORK_ORDER_STATE_CONFLICT", "refresh"],
    ["WORK_ORDER_CONTEXT_INVALID", null],
    ["ROLE_NOT_ALLOWED", null],
  ])("maps workspace open code %s", (code, actionId) => {
    const presentation = presentWorkspaceOpenError(api(code, 409));
    expect(presentation?.action?.id ?? null).toBe(actionId);
  });

  it.each([
    ["EDIT_VERSION_NOT_FOUND", "reopen"],
    ["EDIT_VERSION_STATE_CONFLICT", "refresh"],
    ["WORKSPACE_CONTEXT_INVALID", null],
  ])("maps workspace restore code %s", (code, actionId) => {
    const presentation = presentWorkspaceRestoreError(api(code, 409));
    expect(presentation?.action?.id ?? null).toBe(actionId);
  });

  it("retries list transport failures", () => {
    expect(presentWorkOrdersLoadError(network)?.action).toEqual({
      id: "retry",
      label: "Повторить",
    });
  });

  it("routes a missing workflow actor to sign-in", () => {
    expect(
      presentWorkOrdersLoadError(api("WORK_ORDER_ACTOR_NOT_FOUND", 404))?.action,
    ).toEqual({ id: "sign-in", label: "Войти снова" });
  });

  it("keeps an inactive account non-retryable", () => {
    const presentation = presentWorkOrdersLoadError(api("USER_INACTIVE", 403));
    expect(presentation?.guidance).toBe("Обратитесь к администратору.");
    expect(presentation?.action).toBeNull();
  });

  it("does not present a cancelled request", () => {
    expect(presentWorkOrdersLoadError({ kind: "cancelled" })).toBeNull();
  });

  it("does not invent a retry for an unknown client error", () => {
    const presentation = presentWorkspaceOpenError(
      api("UNKNOWN_CLIENT_ERROR", 422),
    );
    expect(presentation?.summary).toBe("Причина UNKNOWN_CLIENT_ERROR");
    expect(presentation?.action).toBeNull();
  });

  it("preserves only correlation diagnostics for unstructured HTTP", () => {
    const presentation = presentWorkOrdersLoadError({
      kind: "http",
      status: 503,
      correlationId: "http-id",
    });
    expect(presentation?.diagnostics).toEqual({ code: null, correlationId: "http-id" });
    expect(presentation?.action?.id).toBe("retry");
  });
});
```

- [ ] **Step 2: Run the policy test and verify the missing module failure**

Run:

```powershell
npm run test -- --run src/errors/apiErrorPresentations.test.ts
```

Expected: FAIL because the policy module does not exist.

- [ ] **Step 3: Implement common helpers and login/session policies**

Create `errors/apiErrorPresentations.ts` with the following shared core:

```ts
import type {
  ErrorActionId,
  ErrorPresentation,
  ParsedApiError,
} from "@/contracts/api-error";

type SessionMode = "initial" | "runtime";

const ACTION_LABELS: Record<ErrorActionId, string> = {
  retry: "Повторить",
  refresh: "Обновить список",
  reopen: "Открыть заново",
  "sign-in": "Войти снова",
};

function action(id: ErrorActionId): ErrorPresentation["action"] {
  return { id, label: ACTION_LABELS[id] };
}

function diagnostics(error: ParsedApiError): ErrorPresentation["diagnostics"] {
  if (error.kind === "api") {
    return { code: error.code, correlationId: error.correlationId };
  }
  if (error.kind === "http") {
    return { code: null, correlationId: error.correlationId };
  }
  return { code: null, correlationId: null };
}

function summary(error: ParsedApiError, fallback: string): string {
  return error.kind === "api" ? error.message : fallback;
}

function status(error: ParsedApiError): number | null {
  return error.kind === "api" || error.kind === "http" ? error.status : null;
}

function retryable(error: ParsedApiError): boolean {
  const httpStatus = status(error);
  return (
    error.kind === "network" ||
    error.kind === "timeout" ||
    (httpStatus !== null && httpStatus >= 500)
  );
}

function presentation(
  error: ParsedApiError,
  fallback: string,
  guidance: string | null,
  actionId: ErrorActionId | null,
): ErrorPresentation | null {
  if (error.kind === "cancelled") {
    return null;
  }
  return {
    summary: summary(error, fallback),
    guidance,
    action: actionId ? action(actionId) : null,
    diagnostics: diagnostics(error),
  };
}

export function presentLoginError(error: ParsedApiError): ErrorPresentation | null {
  if (error.kind === "api" && error.code === "INVALID_CREDENTIALS") {
    return presentation(error, error.message, "Проверьте электронную почту и пароль.", null);
  }
  if (error.kind === "api" && error.code === "USER_INACTIVE") {
    return presentation(error, error.message, "Обратитесь к администратору.", null);
  }
  return presentation(
    error,
    "Сейчас не удалось выполнить вход.",
    "Проверьте соединение и попробуйте ещё раз.",
    null,
  );
}

export function presentSessionError(
  error: ParsedApiError,
  mode: SessionMode,
): ErrorPresentation | null {
  if (mode === "initial" && status(error) === 401) {
    return null;
  }
  if (mode === "runtime" && status(error) === 401) {
    return presentation(error, "Сессия завершена.", "Войдите снова.", "sign-in");
  }
  if (error.kind === "api" && error.code === "USER_INACTIVE") {
    return presentation(error, error.message, "Обратитесь к администратору.", null);
  }
  return presentation(
    error,
    "Не удалось восстановить сессию.",
    retryable(error) ? "Проверьте соединение и повторите запрос." : null,
    retryable(error) ? "retry" : null,
  );
}
```

- [ ] **Step 4: Add WorkOrder/Workspace policies without a global error bus**

Append to the same file:

```ts
function requiresSignIn(error: ParsedApiError): boolean {
  return (
    status(error) === 401 ||
    (error.kind === "api" && error.code === "WORK_ORDER_ACTOR_NOT_FOUND")
  );
}

function workflowFallback(
  error: ParsedApiError,
  fallback: string,
  retryAction: ErrorActionId,
): ErrorPresentation | null {
  if (requiresSignIn(error)) {
    return presentation(error, "Сессия завершена.", "Войдите снова.", "sign-in");
  }
  if (error.kind === "api" && error.code === "ROLE_NOT_ALLOWED") {
    return presentation(
      error,
      error.message,
      "Обратитесь к администратору, если доступ должен быть предоставлен.",
      null,
    );
  }
  if (error.kind === "api" && error.code === "USER_INACTIVE") {
    return presentation(error, error.message, "Обратитесь к администратору.", null);
  }
  return presentation(
    error,
    fallback,
    retryable(error) ? "Проверьте соединение и повторите запрос." : null,
    retryable(error) ? retryAction : null,
  );
}

export function presentWorkOrdersLoadError(
  error: ParsedApiError,
): ErrorPresentation | null {
  return workflowFallback(error, "Не удалось загрузить назначенные наряды.", "retry");
}

export function presentWorkspaceOpenError(
  error: ParsedApiError,
): ErrorPresentation | null {
  if (error.kind === "api") {
    if (["WORK_ORDER_NOT_FOUND", "WORK_ORDER_NOT_ASSIGNED"].includes(error.code)) {
      return presentation(error, error.message, "Список назначений мог измениться.", "refresh");
    }
    if (error.code === "WORK_ORDER_STATE_CONFLICT") {
      return presentation(error, error.message, "Состояние наряда изменилось.", "refresh");
    }
    if (error.code === "WORK_ORDER_CONTEXT_INVALID") {
      return presentation(
        error,
        error.message,
        "Повтор не устранит проблему. Передайте код обращения поддержке.",
        null,
      );
    }
  }
  return workflowFallback(error, "Не удалось открыть рабочую версию.", "retry");
}

export function presentWorkspaceRestoreError(
  error: ParsedApiError,
): ErrorPresentation | null {
  if (error.kind === "api") {
    if (error.code === "EDIT_VERSION_NOT_FOUND") {
      return presentation(
        error,
        error.message,
        "Сохранённая рабочая версия больше недоступна.",
        "reopen",
      );
    }
    if (error.code === "EDIT_VERSION_STATE_CONFLICT") {
      return presentation(error, error.message, "Состояние рабочей версии изменилось.", "refresh");
    }
    if (error.code === "WORKSPACE_CONTEXT_INVALID") {
      return presentation(
        error,
        error.message,
        "Workspace невозможно сформировать. Передайте код обращения поддержке.",
        null,
      );
    }
  }
  return workflowFallback(error, "Не удалось восстановить рабочую версию.", "retry");
}
```

- [ ] **Step 5: Run policy tests, typecheck and formatter check**

Run:

```powershell
npm run test -- --run src/errors/apiErrorPresentations.test.ts
npm run typecheck
npm run format:check
```

Expected: tests and typecheck pass. If Prettier reports only the new policy
files, run
`npx prettier --write src/errors/apiErrorPresentations.ts src/errors/apiErrorPresentations.test.ts`,
then rerun the checks. Do not use the repository-wide `format:write` script
for this focused task.

- [ ] **Step 6: Review checkpoint**

Run:

```powershell
git diff --check
git status --short
```

Expected: only shared parser/policy files and prior backend files are unstaged.

---

### Task 5: Reusable Accessible ActionableError Component

**Files:**

- Create: `apps/frontend/src/components/ActionableError.vue`
- Create: `apps/frontend/src/components/ActionableError.test.ts`

**Interfaces:**

- Consumes: `presentation: ErrorPresentation`, optional `id`.
- Produces: `action` event with `ErrorActionId`.
- Does not import Axios, Pinia or workflow stores.

- [ ] **Step 1: Write failing render/action/copy tests**

Create `ActionableError.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ActionableError from "@/components/ActionableError.vue";
import type { ErrorPresentation } from "@/contracts/api-error";

const presentation: ErrorPresentation = {
  summary: "Рабочая версия не найдена.",
  guidance: "Откройте рабочую версию заново.",
  action: { id: "reopen", label: "Открыть заново" },
  diagnostics: {
    code: "EDIT_VERSION_NOT_FOUND",
    correlationId: "workspace-correlation-id",
  },
};

describe("ActionableError", () => {
  beforeEach(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("renders an alert with closed diagnostics", () => {
    const wrapper = mount(ActionableError, { props: { presentation } });

    expect(wrapper.get('[role="alert"]').text()).toContain("Рабочая версия не найдена");
    expect(wrapper.text()).toContain("Откройте рабочую версию заново");
    expect(wrapper.get("details").attributes("open")).toBeUndefined();
    expect(wrapper.get('[data-test="error-code"]').text()).toContain("EDIT_VERSION_NOT_FOUND");
    expect(wrapper.get('[data-test="correlation-id"]').text()).toContain("workspace-correlation-id");
  });

  it("emits the selected workflow action", async () => {
    const wrapper = mount(ActionableError, { props: { presentation } });

    await wrapper.get('[data-test="error-action"]').trigger("click");

    expect(wrapper.emitted("action")).toEqual([["reopen"]]);
  });

  it("copies the full correlation id and announces success", async () => {
    const wrapper = mount(ActionableError, { props: { presentation } });

    await wrapper.get('[data-test="copy-correlation-id"]').trigger("click");

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("workspace-correlation-id");
    expect(wrapper.get('[data-test="copy-status"]').text()).toBe(
      "Код обращения скопирован",
    );
    expect(wrapper.get('[data-test="copy-status"]').attributes("aria-live")).toBe("polite");
  });

  it("keeps the id visible when clipboard is unavailable", async () => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: undefined,
    });
    const wrapper = mount(ActionableError, { props: { presentation } });

    await wrapper.get('[data-test="copy-correlation-id"]').trigger("click");

    expect(wrapper.get('[data-test="correlation-id"]').text()).toContain(
      "workspace-correlation-id",
    );
    expect(wrapper.get('[data-test="copy-status"]').text()).toBe(
      "Не удалось скопировать код обращения",
    );
  });

  it("hides diagnostics and action when absent", () => {
    const wrapper = mount(ActionableError, {
      props: {
        presentation: {
          summary: "Ошибка сети",
          guidance: null,
          action: null,
          diagnostics: { code: null, correlationId: null },
        },
      },
    });

    expect(wrapper.find("details").exists()).toBe(false);
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(false);
  });
});
```

- [ ] **Step 2: Run the component test and verify the missing component failure**

Run:

```powershell
npm run test -- --run src/components/ActionableError.test.ts
```

Expected: FAIL because `ActionableError.vue` does not exist.

- [ ] **Step 3: Implement the component behavior**

Create `ActionableError.vue`:

```vue
<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type {
  ErrorActionId,
  ErrorPresentation,
} from "@/contracts/api-error";

const props = defineProps<{
  presentation: ErrorPresentation;
  id?: string;
}>();

const emit = defineEmits<{
  action: [actionId: ErrorActionId];
}>();

const copyStatus = ref("");
const hasDiagnostics = computed(
  () =>
    props.presentation.diagnostics.code !== null ||
    props.presentation.diagnostics.correlationId !== null,
);

watch(
  () => props.presentation.diagnostics.correlationId,
  () => {
    copyStatus.value = "";
  },
);

async function copyCorrelationId(): Promise<void> {
  const correlationId = props.presentation.diagnostics.correlationId;
  if (!correlationId) {
    return;
  }
  try {
    if (!navigator.clipboard) {
      throw new Error("Clipboard API недоступен");
    }
    await navigator.clipboard.writeText(correlationId);
    copyStatus.value = "Код обращения скопирован";
  } catch {
    copyStatus.value = "Не удалось скопировать код обращения";
  }
}

function emitAction(): void {
  const selectedAction = props.presentation.action;
  if (selectedAction) {
    emit("action", selectedAction.id);
  }
}
</script>

<template>
  <div :id="props.id" class="actionableError">
    <div class="errorContent" role="alert">
      <p class="errorSummary">{{ props.presentation.summary }}</p>
      <p v-if="props.presentation.guidance" class="errorGuidance">
        {{ props.presentation.guidance }}
      </p>
    </div>

    <button
      v-if="props.presentation.action"
      class="errorAction"
      data-test="error-action"
      type="button"
      @click="emitAction"
    >
      {{ props.presentation.action.label }}
    </button>

    <details v-if="hasDiagnostics" class="errorDiagnostics">
      <summary>Технические сведения</summary>
      <dl>
        <div v-if="props.presentation.diagnostics.code">
          <dt>Код ошибки</dt>
          <dd data-test="error-code">{{ props.presentation.diagnostics.code }}</dd>
        </div>
        <div v-if="props.presentation.diagnostics.correlationId">
          <dt>Код обращения</dt>
          <dd data-test="correlation-id">
            {{ props.presentation.diagnostics.correlationId }}
          </dd>
        </div>
      </dl>
      <button
        v-if="props.presentation.diagnostics.correlationId"
        data-test="copy-correlation-id"
        type="button"
        @click="copyCorrelationId"
      >
        Копировать код обращения
      </button>
    </details>

    <p
      class="copyStatus"
      data-test="copy-status"
      aria-live="polite"
      aria-atomic="true"
    >
      {{ copyStatus }}
    </p>
  </div>
</template>

<style scoped>
.actionableError {
  display: grid;
  justify-items: start;
  gap: 10px;
  color: #991b1b;
}

.errorSummary,
.errorGuidance,
.copyStatus {
  margin: 0;
  line-height: 1.4;
}

.errorSummary {
  font-weight: 700;
}

.errorGuidance,
.errorDiagnostics,
.copyStatus {
  font-size: 13px;
}

.errorAction,
.errorDiagnostics button {
  border: 1px solid rgba(153, 27, 27, 0.3);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  color: #7f1d1d;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.errorDiagnostics dl {
  display: grid;
  gap: 8px;
  margin: 8px 0;
}

.errorDiagnostics dt {
  color: #64748b;
}

.errorDiagnostics dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
  color: #0f172a;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.copyStatus:empty {
  display: none;
}
</style>
```

- [ ] **Step 4: Run component tests and quality checks**

Run:

```powershell
npm run test -- --run src/components/ActionableError.test.ts
npm run typecheck
npm run format:check
```

Expected: tests, typecheck and formatting pass.

- [ ] **Step 5: Review checkpoint**

Run:

```powershell
git diff --check
git status --short
```

Expected: component files are unstaged and no unrelated files changed.

---

### Task 6: Auth Store And Runtime 401 State

**Files:**

- Modify: `apps/frontend/src/stores/auth.ts`
- Modify: `apps/frontend/src/stores/auth.test.ts`
- Modify: `apps/frontend/src/api/http.ts`
- Modify: `apps/frontend/src/api/http.test.ts`

**Interfaces:**

- Consumes: `parseApiError()` and `presentSessionError()`.
- Produces: `sessionError: ErrorPresentation | null`,
  `handleUnauthorizedResponse(error: unknown): void`,
  `dismissSessionError(): void`.
- App integration in Task 7 calls `dismissSessionError` and existing
  `restoreSession`/`logout` actions.

- [ ] **Step 1: Change auth/http tests to require structured session state**

In `auth.test.ts`, retain the existing silent initial `401` test and replace
the generic `503` string assertion with:

```ts
expect(store.sessionError).toEqual({
  summary: "Не удалось восстановить сессию.",
  guidance: "Проверьте соединение и повторите запрос.",
  action: { id: "retry", label: "Повторить" },
  diagnostics: { code: null, correlationId: null },
});
```

Add:

```ts
it("keeps an actionable sign-in error after a runtime 401", async () => {
  const { useAuthStore } = await import("@/stores/auth");
  const store = useAuthStore();
  store.token = "token-1";
  store.user = {
    id: "user-1",
    email: "editor@example.com",
    role: "editor",
  };

  store.handleUnauthorizedResponse({
    isAxiosError: true,
    response: {
      status: 401,
      headers: { "x-correlation-id": "runtime-auth-id" },
      data: {
        code: "AUTH_REQUIRED",
        message: "Сессия недействительна.",
        correlationId: "runtime-auth-id",
      },
    },
  });

  expect(store.token).toBeNull();
  expect(store.user).toBeNull();
  expect(store.sessionError?.action?.id).toBe("sign-in");
  expect(store.sessionError?.diagnostics.correlationId).toBe("runtime-auth-id");
});

it("does not create a runtime notice for an already anonymous user", async () => {
  const { useAuthStore } = await import("@/stores/auth");
  const store = useAuthStore();

  store.handleUnauthorizedResponse({
    isAxiosError: true,
    response: { status: 401, data: {} },
  });

  expect(store.sessionError).toBeNull();
});
```

In `http.test.ts`, change `authStoreMock` to expose
`handleUnauthorizedResponse: vi.fn()`, remove its unused
`clearLocalSession` mock, and replace the interceptor test body with:

```ts
it("delegates a 401 to the auth store without backend logout", async () => {
  await import("@/api/http");
  const rejectHandler = responseUseMock.mock.calls[0]?.[1] as (
    error: unknown,
  ) => Promise<never>;
  const error = { response: { status: 401 } };

  await expect(rejectHandler(error)).rejects.toBe(error);

  expect(authStoreMock.handleUnauthorizedResponse).toHaveBeenCalledWith(error);
  expect(authStoreMock.logout).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run focused tests and verify type/behavior failures**

Run:

```powershell
npm run test -- --run src/stores/auth.test.ts src/api/http.test.ts
```

Expected: failures because `sessionError` is still a string and the new store
actions do not exist.

- [ ] **Step 3: Replace string session errors with presentations**

In `stores/auth.ts`:

```ts
import type { ErrorPresentation } from "@/contracts/api-error";
import { parseApiError } from "@/api/parseApiError";
import { presentSessionError } from "@/errors/apiErrorPresentations";
```

Change `AuthState.sessionError` to `ErrorPresentation | null`, remove the
Axios import, capture the mode before the request, and use this flow in
`restoreSession()`:

```ts
const restoreMode = this.isAuthenticated ? "runtime" : "initial";

try {
  const result = await refreshSession();
  this.setAuth(result.access_token, result.user, {
    preserveOpenedWorkspaceOnInitialUser: true,
  });
} catch (error: unknown) {
  const parsed = parseApiError(error);
  const sessionError = presentSessionError(parsed, restoreMode);
  this.clearLocalSession();
  this.sessionError = sessionError;
} finally {
  this.isReady = true;
  this.isRestoring = false;
}
```

Add these actions next to `clearLocalSession()`:

```ts
handleUnauthorizedResponse(error: unknown): void {
  const hadActiveSession = this.isAuthenticated;
  const parsed = parseApiError(error);
  this.clearLocalSession();
  if (hadActiveSession) {
    this.sessionError = presentSessionError(parsed, "runtime");
  }
},
dismissSessionError(): void {
  this.sessionError = null;
},
```

Do not change `logout()` ordering: it must clear local state before awaiting
the backend.

- [ ] **Step 4: Delegate runtime 401 handling from the interceptor**

Replace the `401` branch in `api/http.ts`:

```ts
if (status === 401) {
  auth.handleUnauthorizedResponse(err);
}
```

The interceptor still returns `Promise.reject(err)` and never calls backend
logout.

- [ ] **Step 5: Run auth/http tests and typecheck**

Run:

```powershell
npm run test -- --run src/stores/auth.test.ts src/api/http.test.ts
npm run typecheck
```

Expected: tests pass; existing workOrders reset assertions remain green.

- [ ] **Step 6: Review checkpoint**

Run:

```powershell
git diff --check
git status --short
```

Expected: auth/http changes remain unstaged.

---

### Task 7: Login And Session Error UI Integration

**Files:**

- Modify: `apps/frontend/src/components/LoginScreen.vue`
- Modify: `apps/frontend/src/components/LoginScreen.test.ts`
- Modify: `apps/frontend/src/App.vue`
- Modify: `apps/frontend/src/App.test.ts`

**Interfaces:**

- Consumes: `ActionableError`, login/session policies and auth store actions.
- Produces: actionable login diagnostics and session retry/sign-in controls.
- Login form retains its existing submit button as the only retry control.

- [ ] **Step 1: Update login tests to require guidance and diagnostics**

In `LoginScreen.test.ts`, keep the current error fixtures and replace the
structured assertion with:

```ts
const alert = wrapper.get('[role="alert"]');
expect(alert.text()).toContain("Неверная электронная почта или пароль");
expect(alert.text()).toContain("Проверьте электронную почту и пароль");
expect(wrapper.get('[data-test="error-code"]').text()).toContain(
  "INVALID_CREDENTIALS",
);
expect(wrapper.get('[data-test="correlation-id"]').text()).toContain(
  "login-correlation-id",
);
expect(wrapper.find('[data-test="error-action"]').exists()).toBe(false);
```

Keep the malformed response test, but assert that neither
`legacy detail should not be rendered` nor a technical action is shown.

- [ ] **Step 2: Add App tests for retry and sign-in actions**

Add to `App.test.ts`:

```ts
it("retries session restoration through the actionable error", async () => {
  const { useAuthStore } = await import("@/stores/auth");
  const auth = useAuthStore();
  auth.isReady = true;
  auth.sessionError = {
    summary: "Не удалось восстановить сессию.",
    guidance: "Проверьте соединение и повторите запрос.",
    action: { id: "retry", label: "Повторить" },
    diagnostics: { code: "INTERNAL_ERROR", correlationId: "session-id" },
  };
  auth.restoreSession = vi.fn();

  const { default: App } = await import("@/App.vue");
  const wrapper = mount(App);
  await wrapper.get('[data-test="error-action"]').trigger("click");

  expect(auth.restoreSession).toHaveBeenCalledTimes(1);
});

it("dismisses an expired-session error before showing login", async () => {
  const { useAuthStore } = await import("@/stores/auth");
  const auth = useAuthStore();
  auth.isReady = true;
  auth.sessionError = {
    summary: "Сессия завершена.",
    guidance: "Войдите снова.",
    action: { id: "sign-in", label: "Войти снова" },
    diagnostics: { code: "AUTH_REQUIRED", correlationId: "session-id" },
  };

  const { default: App } = await import("@/App.vue");
  const wrapper = mount(App);
  await wrapper.get('[data-test="error-action"]').trigger("click");

  expect(auth.sessionError).toBeNull();
  expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(true);
});
```

- [ ] **Step 3: Run focused component tests and verify old string UI failures**

Run:

```powershell
npm run test -- --run src/components/LoginScreen.test.ts src/App.test.ts
```

Expected: failures because both components still render string errors.

- [ ] **Step 4: Integrate ActionableError into LoginScreen**

In `LoginScreen.vue`, import `ActionableError`, `parseApiError`,
`presentLoginError`, and `ErrorPresentation`. Replace the string ref and catch:

```ts
const errorPresentation = ref<ErrorPresentation | null>(null);

async function onSubmit() {
  errorPresentation.value = null;
  isSubmitting.value = true;
  try {
    await auth.loginWithPassword(email.value, password.value);
  } catch (error: unknown) {
    errorPresentation.value = presentLoginError(parseApiError(error));
  } finally {
    isSubmitting.value = false;
  }
}
```

Replace the old error paragraph with:

```vue
<ActionableError
  v-if="errorPresentation"
  :presentation="errorPresentation"
/>
```

Remove the direct Axios import and obsolete `.errorMessage` style. Keep form
inputs and the existing `Войти` button unchanged.

- [ ] **Step 5: Integrate ActionableError into App session state**

In `App.vue`, import `ActionableError` and `ErrorActionId`, then add:

```ts
function handleSessionErrorAction(actionId: ErrorActionId): void {
  if (actionId === "retry") {
    void auth.restoreSession();
    return;
  }
  if (actionId === "sign-in") {
    auth.dismissSessionError();
  }
}
```

Replace `.statusText` and the primary retry button in the `auth.sessionError`
branch with:

```vue
<ActionableError
  :presentation="auth.sessionError"
  @action="handleSessionErrorAction"
/>
```

Keep the secondary `Выйти` button outside the component. Remove only CSS that
became unused.

- [ ] **Step 6: Run login/App tests and frontend checks**

Run:

```powershell
npm run test -- --run src/components/LoginScreen.test.ts src/App.test.ts src/components/ActionableError.test.ts
npm run typecheck
npm run format:check
```

Expected: component tests and checks pass.

- [ ] **Step 7: Review checkpoint**

Run:

```powershell
git diff --check
git status --short
```

Expected: only intended auth/session UI files changed.

---

### Task 8: WorkOrders Store Error State And Recovery Actions

**Files:**

- Modify: `apps/frontend/src/stores/workOrders.ts`
- Modify: `apps/frontend/src/stores/workOrders.test.ts`

**Interfaces:**

- Consumes: parser and WorkOrder/Workspace presentation policies.
- Produces: `loadError`, keyed `ErrorPresentation` state,
  `retrySelectedWorkspaceError()`, `reopenSelectedWorkOrder()` and
  `selectedOpenWorkspaceErrorOperation`.
- Task 9 maps component action IDs to these store actions.

- [ ] **Step 1: Update store tests to assert structured list/open errors**

Add an Axios-like helper to `workOrders.test.ts`:

```ts
function apiFailure(code: string, status: number, correlationId = "request-id") {
  return {
    isAxiosError: true,
    response: {
      status,
      headers: { "x-correlation-id": correlationId },
      data: { code, message: `Причина ${code}`, correlationId },
    },
  };
}

function networkFailure() {
  return { isAxiosError: true };
}
```

Rename `errorMessage` assertions/setup to `loadError`. Change the load failure
fixture to `fetchAssignedWorkOrdersMock.mockRejectedValue(networkFailure())`
and its assertion to:

```ts
expect(store.loadError).toMatchObject({
  summary: "Не удалось загрузить назначенные наряды.",
  action: { id: "retry", label: "Повторить" },
});
```

Add:

```ts
it("maps a missing work order to refresh", async () => {
  openEditVersionMock.mockRejectedValue(apiFailure("WORK_ORDER_NOT_FOUND", 404));
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [{
    id: "wo-1",
    code: "WO-001",
    title: "Наряд",
    description: null,
    status: "assigned",
  }];
  store.selectWorkOrder("wo-1");

  await store.openSelectedWorkOrder();

  expect(store.selectedOpenWorkspaceError?.action?.id).toBe("refresh");
  expect(store.selectedOpenWorkspaceError?.diagnostics.correlationId).toBe("request-id");
  expect(store.selectedOpenWorkspaceErrorOperation).toBe("open");
});
```

- [ ] **Step 2: Add restore persistence and retry tests**

Add:

```ts
it("clears a stale marker and offers reopen when the edit version disappeared", async () => {
  sessionStorage.setItem(
    "geoservice:opened-workspace",
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );
  fetchWorkspaceMock.mockRejectedValue(apiFailure("EDIT_VERSION_NOT_FOUND", 404));
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [{
    id: "wo-1",
    code: "WO-001",
    title: "Наряд",
    description: null,
    status: "in_progress",
  }];

  await store.restoreOpenedWorkspace();

  expect(sessionStorage.getItem("geoservice:opened-workspace")).toBeNull();
  expect(store.selectedOpenWorkspaceError?.action?.id).toBe("reopen");
  expect(store.selectedOpenWorkspaceErrorOperation).toBe("restore");
});

it("preserves the marker and retries the original restore after a network failure", async () => {
  sessionStorage.setItem(
    "geoservice:opened-workspace",
    JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
  );
  fetchWorkspaceMock.mockRejectedValueOnce(networkFailure());
  fetchWorkspaceMock.mockResolvedValueOnce(workspaceResponse("wo-1", "ev-1"));
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [{
    id: "wo-1",
    code: "WO-001",
    title: "Наряд",
    description: null,
    status: "in_progress",
  }];

  await store.restoreOpenedWorkspace();
  await store.retrySelectedWorkspaceError();

  expect(openEditVersionMock).not.toHaveBeenCalled();
  expect(fetchWorkspaceMock).toHaveBeenCalledTimes(2);
  expect(store.activeWorkspace?.workOrder.id).toBe("wo-1");
});
```

- [ ] **Step 3: Run focused store tests and verify state failures**

Run:

```powershell
npm run test -- --run src/stores/workOrders.test.ts
```

Expected: failures for old string state, missing operation tracking and missing
recovery actions.

- [ ] **Step 4: Change state types and initial/reset state**

In `workOrders.ts`, import the parser, policies, `ErrorPresentation`, and
`ParsedApiError`. Add:

```ts
type WorkspaceErrorOperation = "open" | "restore";

type ClearOpenedWorkspaceOptions = {
  preserveStoredWorkspace?: boolean;
};
```

Change `WorkOrdersState` fields to:

```ts
loadError: ErrorPresentation | null;
openWorkspaceErrorByWorkOrderId: Record<
  string,
  ErrorPresentation | undefined
>;
openWorkspaceErrorOperationByWorkOrderId: Record<
  string,
  WorkspaceErrorOperation | undefined
>;
```

Initialize/reset them with `loadError: null` and empty records. Add getter:

```ts
selectedOpenWorkspaceErrorOperation: (state) => {
  if (!state.selectedWorkOrderId) {
    return null;
  }
  return (
    state.openWorkspaceErrorOperationByWorkOrderId[
      state.selectedWorkOrderId
    ] ?? null
  );
},
```

- [ ] **Step 5: Parse list/open failures and track their operation**

Use `catch (error: unknown)` in each action. In `loadAssigned()`:

```ts
const parsed = parseApiError(error);
this.loadError = presentWorkOrdersLoadError(parsed);
```

Set `loadError = null` before the request. In `openSelectedWorkOrder()`, clear
both keyed presentation and operation before the request, then in the guarded
catch:

```ts
const parsed = parseApiError(error);
const errorPresentation = presentWorkspaceOpenError(parsed);
this.openWorkspaceErrorByWorkOrderId = {
  ...this.openWorkspaceErrorByWorkOrderId,
  [workOrderId]: errorPresentation ?? undefined,
};
this.openWorkspaceErrorOperationByWorkOrderId = {
  ...this.openWorkspaceErrorOperationByWorkOrderId,
  [workOrderId]: errorPresentation ? "open" : undefined,
};
```

On successful open, clear both keyed values for that work order.

- [ ] **Step 6: Preserve only retryable restore markers**

Add this helper outside the store:

```ts
function shouldPreserveStoredWorkspace(error: ParsedApiError): boolean {
  return (
    error.kind === "network" ||
    error.kind === "timeout" ||
    ((error.kind === "api" || error.kind === "http") && error.status >= 500)
  );
}
```

Change `clearOpenedWorkspace()` to accept options:

```ts
clearOpenedWorkspace(options: ClearOpenedWorkspaceOptions = {}): void {
  this.openedWorkOrderId = null;
  this.openedEditVersionId = null;
  this.workspace = null;
  this.lastFittedWorkspaceKey = null;
  if (!options.preserveStoredWorkspace) {
    clearStoredOpenedWorkspace();
  }
},
```

In the guarded `restoreOpenedWorkspace()` catch:

```ts
const parsed = parseApiError(error);
const errorPresentation = presentWorkspaceRestoreError(parsed);
this.clearOpenedWorkspace({
  preserveStoredWorkspace: shouldPreserveStoredWorkspace(parsed),
});
this.openWorkspaceErrorByWorkOrderId = {
  ...this.openWorkspaceErrorByWorkOrderId,
  [workOrderId]: errorPresentation ?? undefined,
};
this.openWorkspaceErrorOperationByWorkOrderId = {
  ...this.openWorkspaceErrorOperationByWorkOrderId,
  [workOrderId]: errorPresentation ? "restore" : undefined,
};
```

- [ ] **Step 7: Add explicit retry and reopen actions**

Add store actions:

```ts
async retrySelectedWorkspaceError(): Promise<void> {
  if (this.selectedOpenWorkspaceErrorOperation === "restore") {
    await this.restoreOpenedWorkspace();
    return;
  }
  await this.openSelectedWorkOrder();
},
async reopenSelectedWorkOrder(): Promise<void> {
  clearStoredOpenedWorkspace();
  await this.openSelectedWorkOrder();
},
```

Keep action routing out of `ActionableError`; Task 9 decides which store
method corresponds to the emitted action ID.

- [ ] **Step 8: Run store tests and typecheck**

Run:

```powershell
npm run test -- --run src/stores/workOrders.test.ts
npm run typecheck
```

Expected: all existing concurrency/persistence tests and new presentation
tests pass.

- [ ] **Step 9: Review checkpoint**

Run:

```powershell
git diff --check
git status --short
```

Expected: store changes remain unstaged and no unrelated state changed.

---

### Task 9: WorkOrder List And Workspace Component Integration

**Files:**

- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
- Modify: `apps/frontend/src/components/WorkspaceDetailsPanel.vue`
- Modify: `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts`

**Interfaces:**

- Consumes: store presentations/actions and `ActionableError`.
- Produces: list retry, refresh, reopen, sign-in and contextual workspace error
  behavior without duplicate open buttons.

- [ ] **Step 1: Update WorkspaceDetailsPanel tests to use ErrorPresentation**

Change `PanelTestProps.errorMessage` to
`error: ErrorPresentation | null`, import the shared types, and change the
default prop to `error: null`. Replace the old error test with:

```ts
it("renders a workspace error action instead of the normal open action", async () => {
  const wrapper = mountPanel({
    error: {
      summary: "Рабочая версия не найдена.",
      guidance: "Откройте рабочую версию заново.",
      action: { id: "reopen", label: "Открыть заново" },
      diagnostics: {
        code: "EDIT_VERSION_NOT_FOUND",
        correlationId: "workspace-id",
      },
    },
  });

  expect(wrapper.get('[role="alert"]').text()).toContain("Рабочая версия не найдена");
  expect(wrapper.find('[data-test="workspace-open-action"]').exists()).toBe(false);
  await wrapper.get('[data-test="error-action"]').trigger("click");
  expect(wrapper.emitted("errorAction")).toEqual([["reopen"]]);
});
```

- [ ] **Step 2: Update EditorWorkOrdersView tests for action routing**

Add `const reopenSelectedWorkOrderMock = vi.fn();` beside the existing action
mocks, replace the old string-error test, and add these cases:

```ts
it("routes the list retry action to loadAssigned", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.loadError = {
    summary: "Не удалось загрузить назначенные наряды.",
    guidance: "Проверьте соединение и повторите запрос.",
    action: { id: "retry", label: "Повторить" },
    diagnostics: { code: "INTERNAL_ERROR", correlationId: "list-id" },
  };
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);
  await flushPromises();
  loadAssignedMock.mockClear();

  expect(wrapper.get('[role="alert"]').text()).toContain(
    "Не удалось загрузить назначенные наряды",
  );
  await wrapper.get('[data-test="error-action"]').trigger("click");
  expect(loadAssignedMock).toHaveBeenCalledTimes(1);
});

it("routes reopen from the selected workspace error", async () => {
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const store = useWorkOrdersStore();
  store.items = [assignedWorkOrder()];
  store.selectedWorkOrderId = "wo-1";
  store.openWorkspaceErrorByWorkOrderId = {
    "wo-1": {
      summary: "Рабочая версия не найдена.",
      guidance: "Откройте рабочую версию заново.",
      action: { id: "reopen", label: "Открыть заново" },
      diagnostics: {
        code: "EDIT_VERSION_NOT_FOUND",
        correlationId: "workspace-id",
      },
    },
  };
  store.loadAssigned = loadAssignedMock;
  store.reopenSelectedWorkOrder = reopenSelectedWorkOrderMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  await wrapper.get('[data-test="error-action"]').trigger("click");
  expect(reopenSelectedWorkOrderMock).toHaveBeenCalledTimes(1);
});

it("routes sign-in errors to local logout", async () => {
  const { useAuthStore } = await import("@/stores/auth");
  const { useWorkOrdersStore } = await import("@/stores/workOrders");
  const auth = useAuthStore();
  const store = useWorkOrdersStore();
  auth.logout = vi.fn();
  store.loadError = {
    summary: "Сессия завершена.",
    guidance: "Войдите снова.",
    action: { id: "sign-in", label: "Войти снова" },
    diagnostics: { code: "AUTH_REQUIRED", correlationId: "auth-id" },
  };
  store.loadAssigned = loadAssignedMock;

  const { default: EditorWorkOrdersView } =
    await import("@/components/EditorWorkOrdersView.vue");
  const wrapper = mount(EditorWorkOrdersView);

  await wrapper.get('[data-test="error-action"]').trigger("click");
  expect(auth.logout).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 3: Run focused component tests and verify prop/template failures**

Run:

```powershell
npm run test -- --run src/components/WorkspaceDetailsPanel.test.ts src/components/EditorWorkOrdersView.test.ts
```

Expected: failures for the old string props and missing action handlers.

- [ ] **Step 4: Replace workspace string error rendering**

In `WorkspaceDetailsPanel.vue`, import `ActionableError`, `ErrorActionId` and
`ErrorPresentation`. Change props/emits:

```ts
const props = defineProps<{
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  error: ErrorPresentation | null;
}>();

const emit = defineEmits<{
  open: [];
  errorAction: [actionId: ErrorActionId];
}>();
```

In the preview body, render:

```vue
<ActionableError
  v-if="props.error"
  id="workspace-open-error"
  :presentation="props.error"
  @action="emit('errorAction', $event)"
/>

<button
  v-else
  class="openAction"
  type="button"
  data-test="workspace-open-action"
  :disabled="props.isOpenActionDisabled"
  @click="emit('open')"
>
  {{ actionText }}
</button>
```

Remove the old `.openError` styles and obsolete `aria-describedby`; the
actionable component owns the alert semantics.

- [ ] **Step 5: Route list and workspace actions in EditorWorkOrdersView**

Import `ActionableError`, `ErrorActionId` and `useAuthStore`. Add handlers:

```ts
const auth = useAuthStore();

function handleLoadErrorAction(actionId: ErrorActionId): void {
  if (actionId === "retry" || actionId === "refresh") {
    void workOrders.loadAssigned();
    return;
  }
  if (actionId === "sign-in") {
    void auth.logout();
  }
}

function handleWorkspaceErrorAction(actionId: ErrorActionId): void {
  if (actionId === "retry") {
    void workOrders.retrySelectedWorkspaceError();
    return;
  }
  if (actionId === "refresh") {
    void workOrders.loadAssigned();
    return;
  }
  if (actionId === "reopen") {
    void workOrders.reopenSelectedWorkOrder();
    return;
  }
  if (actionId === "sign-in") {
    void auth.logout();
  }
}
```

Replace the list error branch with:

```vue
<div v-else-if="workOrders.loadError" class="panelState isError">
  <ActionableError
    :presentation="workOrders.loadError"
    @action="handleLoadErrorAction"
  />
</div>
```

Pass the selected presentation and action handler to the panel:

```vue
:error="workOrders.selectedOpenWorkspaceError"
@error-action="handleWorkspaceErrorAction"
```

Update `onMounted()` to check `!workOrders.loadError` before restore.

- [ ] **Step 6: Run component/store regression tests and typecheck**

Run:

```powershell
npm run test -- --run src/components/WorkspaceDetailsPanel.test.ts src/components/EditorWorkOrdersView.test.ts src/stores/workOrders.test.ts
npm run typecheck
npm run format:check
```

Expected: all tests and checks pass; workspace open button is absent whenever
an error presentation is active.

- [ ] **Step 7: Review checkpoint**

Run:

```powershell
git diff --check
git status --short
```

Expected: only planned files are unstaged.

---

### Task 10: End-To-End Regression And Delivery Review

**Files:**

- Verify: all files listed in this plan.
- Do not create additional documentation unless implementation reveals a
  durable contract that contradicts the approved spec.

**Interfaces:**

- Consumes: completed Tasks 1–9.
- Produces: verified unstaged implementation ready for user review.

- [ ] **Step 1: Run the complete backend error-contract suite**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_correlation_id_middleware.py utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py utility_service/web_api/tests/test_utility_network_api.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 2: Run full backend quality gates**

Run:

```powershell
pytest -q
ruff check utility_service tests
```

Expected: full backend test suite and Ruff pass.

- [ ] **Step 3: Run focused frontend feature tests**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/api/parseApiError.test.ts src/errors/apiErrorPresentations.test.ts src/components/ActionableError.test.ts src/stores/auth.test.ts src/api/http.test.ts src/components/LoginScreen.test.ts src/App.test.ts src/stores/workOrders.test.ts src/components/EditorWorkOrdersView.test.ts src/components/WorkspaceDetailsPanel.test.ts
```

Expected: all focused frontend tests pass.

- [ ] **Step 4: Run full frontend gates**

Run:

```powershell
npm run test -- --run
npm run typecheck
npm run lint -- --no-fix
npm run format:check
npm run build
```

Expected: tests, typecheck, lint, formatting and production build pass.

- [ ] **Step 5: Verify security and contract invariants from the diff**

Run from repository root:

```powershell
rg -n "detail|details|response\.data\.error|response\.data\.message" apps/frontend/src/components apps/frontend/src/stores apps/frontend/src/api
rg -n "Authorization|Cookie|request\.body|query_params" apps/backend/utility_service/web_api/observability apps/backend/utility_service/web_api/api/exception_handlers.py
rg -n "X-Correlation-ID|correlationId|INTERNAL_ERROR" apps/backend/utility_service/web_api apps/frontend/src
```

Expected:

- no UI path renders raw legacy body fields;
- observability code does not read secrets or request bodies;
- correlation identifiers appear only in the planned middleware, handlers,
  parser, diagnostics and tests.

- [ ] **Step 6: Check final diff and decide whether knowledge ingest is needed**

Run:

```powershell
git diff --check
git status --short
git diff --stat
```

Expected: all planned files remain unstaged and no unrelated changes exist.

The approved spec plus code/tests already preserve the durable contract, so
do not invoke `/ingest repository-change` merely because implementation is
complete. Invoke it only if implementation introduces durable technical
knowledge not captured by the spec, code, tests or an existing Code_wiki node.

- [ ] **Step 7: Hand off for user review without Git writes**

Report:

- changed files grouped by backend correlation/logging, frontend shared error
  path and UI integrations;
- exact verification commands and results;
- any intentional deviation from this plan;
- confirmation that no files were staged, committed or pushed.
