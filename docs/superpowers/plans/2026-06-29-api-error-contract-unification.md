# API Error Contract Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Унифицировать invalid login и structured workflow/API errors в strict body `{code, message, correlationId}` без `detail` и `details`.

**Architecture:** Backend сохраняет существующие доменные exception-классы и централизует HTTP rendering в `exception_handlers.py`. Invalid credentials переходят с FastAPI `HTTPException.detail` на `AuthApiError("INVALID_CREDENTIALS")`; frontend login читает `message` из structured response, а workflow UI сохраняет свои fallback-сообщения.

**Tech Stack:** FastAPI, pytest, Vue 3, Pinia, axios, Vitest, @vue/test-utils.

---

## Источники

- Spec: `docs/superpowers/specs/2026-06-29-api-error-contract-unification-design.md`
- Backend API docs to reconcile after implementation: `Code_wiki/архитектура/api_and_realtime.md`
- Agent memory protocol: `docs/agent-memory/protocol.md`

## File Structure

- Modify: `apps/backend/utility_service/use_cases/services/auth_service.py`
  - Responsibility: authenticate login credentials and raise `AuthApiError` for invalid credentials.
- Modify: `apps/backend/utility_service/use_cases/tests/test_auth_service.py`
  - Responsibility: service-level auth behavior and invalid credentials regression coverage.
- Modify: `apps/backend/utility_service/web_api/api/exception_handlers.py`
  - Responsibility: render existing structured domain API errors as strict `{code, message, correlationId}`.
- Create: `apps/backend/utility_service/web_api/tests/test_auth_api.py`
  - Responsibility: route-level `/api/v1/auth/login` invalid credentials contract.
- Modify: `apps/backend/utility_service/web_api/tests/test_exception_handlers.py`
  - Responsibility: strict body coverage for `AuthApiError`, `UtilityNetworkApiError`, and `WorkOrderApiError` handlers.
- Modify: `apps/backend/utility_service/web_api/tests/test_auth_access.py`
  - Responsibility: strict role/access error response coverage.
- Modify: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`
  - Responsibility: strict workflow error body coverage.
- Modify: `apps/frontend/src/components/LoginScreen.vue`
  - Responsibility: display login error from structured `message`.
- Create: `apps/frontend/src/components/LoginScreen.test.ts`
  - Responsibility: component-level login error rendering regression tests.
- Possibly update through `/ingest repository-change`: `Code_wiki/архитектура/api_and_realtime.md`
  - Responsibility: durable API contract docs if code/tests/spec are not sufficient and existing Code_wiki remains stale.

## Task 1: Backend Auth Service Invalid Credentials

**Files:**

- Modify: `apps/backend/utility_service/use_cases/tests/test_auth_service.py`
- Modify: `apps/backend/utility_service/use_cases/services/auth_service.py`

- [ ] **Step 1: Replace service tests for invalid credentials**

In `apps/backend/utility_service/use_cases/tests/test_auth_service.py`, remove the import:

```python
from fastapi import HTTPException
```

Update these three tests exactly:

```python
def test_authenticate_user_raises_401_for_unknown_email() -> None:
    repository = AsyncMock()
    repository.get_by_email.return_value = None
    service = AuthService(session=None, user_repository=repository)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.authenticate_user("missing@example.com", "editor-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_CREDENTIALS"
    assert exc_info.value.message == "Неверная электронная почта или пароль"
```

```python
def test_authenticate_user_raises_401_for_wrong_password() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        password_hash=hash_password("editor-password"),
        is_active=True,
    )
    repository = AsyncMock()
    repository.get_by_email.return_value = user
    service = AuthService(session=None, user_repository=repository)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.authenticate_user("editor@example.com", "wrong-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_CREDENTIALS"
    assert exc_info.value.message == "Неверная электронная почта или пароль"
```

```python
def test_authenticate_user_raises_401_when_password_hash_is_none() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        password_hash=None,
        is_active=True,
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

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_CREDENTIALS"
    assert exc_info.value.message == "Неверная электронная почта или пароль"
```

- [ ] **Step 2: Run service tests and verify the new tests fail**

Run from `apps/backend`:

```powershell
pytest utility_service/use_cases/tests/test_auth_service.py -q
```

Expected: the three changed invalid credentials tests fail because `AuthService.authenticate_user()` still raises `HTTPException`, not `AuthApiError`.

- [ ] **Step 3: Implement invalid credentials as `AuthApiError`**

In `apps/backend/utility_service/use_cases/services/auth_service.py`, remove `HTTPException` from the import:

```python
from fastapi import status
```

Add constants near the imports or above `class AuthService`:

```python
INVALID_CREDENTIALS_CODE = "INVALID_CREDENTIALS"
INVALID_CREDENTIALS_MESSAGE = "Неверная электронная почта или пароль"
```

Replace the current `raise HTTPException(...)` block in `authenticate_user()` with:

```python
            raise AuthApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=INVALID_CREDENTIALS_CODE,
                message=INVALID_CREDENTIALS_MESSAGE,
            )
```

The resulting first half of `authenticate_user()` should read:

```python
    async def authenticate_user(self, email: str, password: str) -> User:
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
        return user
```

- [ ] **Step 4: Run service tests and verify they pass**

Run from `apps/backend`:

```powershell
pytest utility_service/use_cases/tests/test_auth_service.py -q
```

Expected: all tests in `test_auth_service.py` pass.

## Task 2: Backend Strict Structured Error Tests

**Files:**

- Create: `apps/backend/utility_service/web_api/tests/test_auth_api.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_exception_handlers.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_auth_access.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`

- [ ] **Step 1: Add route-level invalid login API test**

Create `apps/backend/utility_service/web_api/tests/test_auth_api.py`:

```python
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import get_auth_service
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.web_api.api.auth import auth_router
from utility_service.web_api.api.exception_handlers import install_exception_handlers


def build_auth_app(auth_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(auth_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    return app


def test_login_invalid_credentials_returns_strict_structured_error() -> None:
    auth_service = AsyncMock()
    auth_service.authenticate_user.side_effect = AuthApiError(
        401,
        "INVALID_CREDENTIALS",
        "Неверная электронная почта или пароль",
    )

    response = TestClient(build_auth_app(auth_service)).post(
        "/api/v1/auth/login",
        headers={"X-Correlation-ID": "login-correlation-id"},
        json={
            "email": "missing@example.local",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_CREDENTIALS",
        "message": "Неверная электронная почта или пароль",
        "correlationId": "login-correlation-id",
    }
    assert "detail" not in response.json()
    assert "details" not in response.json()
    auth_service.authenticate_user.assert_awaited_once_with(
        "missing@example.local",
        "wrong-password",
    )
```

- [ ] **Step 2: Expand exception handler strict body tests**

In `apps/backend/utility_service/web_api/tests/test_exception_handlers.py`, add imports:

```python
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
```

Inside `create_test_app()`, add routes:

```python
    @app.get("/auth-required")
    def auth_required() -> None:
        raise AuthApiError(401, "AUTH_REQUIRED", "Требуется вход в систему.")

    @app.get("/work-order-context")
    def work_order_context() -> None:
        raise WorkOrderApiError(
            422,
            "WORK_ORDER_CONTEXT_INVALID",
            "Контекст рабочей задачи поврежден или неполон.",
        )
```

Replace `test_utility_network_api_error_returns_structured_response()` expected body with no `details`:

```python
    assert response.json() == {
        "code": "FEEDER_NOT_FOUND",
        "message": "Фидер не найден.",
        "correlationId": "test-correlation-id",
    }
    assert "details" not in response.json()
```

Add tests:

```python
def test_auth_api_error_returns_strict_structured_response() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get(
        "/auth-required",
        headers={"X-Correlation-ID": "auth-correlation-id"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "AUTH_REQUIRED",
        "message": "Требуется вход в систему.",
        "correlationId": "auth-correlation-id",
    }
    assert "detail" not in response.json()
    assert "details" not in response.json()


def test_work_order_api_error_returns_strict_structured_response() -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get(
        "/work-order-context",
        headers={"X-Correlation-ID": "workflow-correlation-id"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "WORK_ORDER_CONTEXT_INVALID",
        "message": "Контекст рабочей задачи поврежден или неполон.",
        "correlationId": "workflow-correlation-id",
    }
    assert "detail" not in response.json()
    assert "details" not in response.json()
```

- [ ] **Step 3: Tighten auth access strict body assertion**

In `apps/backend/utility_service/web_api/tests/test_auth_access.py`, replace the body assertions in `test_reviewer_gets_structured_403_from_editor_endpoint()` with:

```python
    body = response.json()
    assert body["code"] == "ROLE_NOT_ALLOWED"
    assert body["message"] == (
        "Операция доступна только пользователю с ролью Editor."
    )
    assert isinstance(body["correlationId"], str)
    assert body["correlationId"]
    assert "detail" not in body
    assert "details" not in body
```

- [ ] **Step 4: Tighten workflow strict body assertions**

In `apps/backend/utility_service/web_api/tests/test_work_orders_api.py`, update `test_service_error_becomes_structured_response()` request to include a correlation header:

```python
    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": "workflow-correlation-id",
        },
    )
```

Replace its body assertions with:

```python
    assert response.json() == {
        "code": "WORK_ORDER_CONTEXT_INVALID",
        "message": "Контекст рабочей задачи поврежден или неполон.",
        "correlationId": "workflow-correlation-id",
    }
```

Update `test_workspace_service_404_is_structured()` request to include a correlation header:

```python
    response = TestClient(build_app(auth_service, edit_version_service, workspace_service)).get(
        f"/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": "workspace-correlation-id",
        },
    )
```

Replace its body assertions with:

```python
    assert response.json() == {
        "code": "EDIT_VERSION_NOT_FOUND",
        "message": "Рабочая версия не найдена.",
        "correlationId": "workspace-correlation-id",
    }
```

- [ ] **Step 5: Run backend API tests and verify strict body tests fail**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: strict structured response tests fail because handlers still include `details`.

## Task 3: Backend Strict Error Renderer

**Files:**

- Modify: `apps/backend/utility_service/web_api/api/exception_handlers.py`

- [ ] **Step 1: Add shared structured response helper**

In `apps/backend/utility_service/web_api/api/exception_handlers.py`, add this helper above `install_exception_handlers()`:

```python
def structured_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
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

- [ ] **Step 2: Replace the three structured handlers**

Replace `auth_api_error()`, `utility_network_api_error()`, and `work_order_api_error()` bodies with calls to the helper:

```python
    @app.exception_handler(AuthApiError)
    async def auth_api_error(request: Request, error: AuthApiError):
        return structured_error_response(
            request,
            error.status_code,
            error.code,
            error.message,
        )
```

```python
    @app.exception_handler(UtilityNetworkApiError)
    async def utility_network_api_error(
        request: Request,
        error: UtilityNetworkApiError,
    ):
        return structured_error_response(
            request,
            error.status_code,
            error.code,
            error.message,
        )
```

```python
    @app.exception_handler(WorkOrderApiError)
    async def work_order_api_error(request: Request, error: WorkOrderApiError):
        return structured_error_response(
            request,
            error.status_code,
            error.code,
            error.message,
        )
```

No other exception handler changes in this task.

- [ ] **Step 3: Run backend API tests and verify they pass**

Run from `apps/backend`:

```powershell
pytest utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: all listed tests pass.

- [ ] **Step 4: Run combined backend auth/error tests**

Run from `apps/backend`:

```powershell
pytest utility_service/use_cases/tests/test_auth_service.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: all listed tests pass.

## Task 4: Frontend Login Error Tests

**Files:**

- Create: `apps/frontend/src/components/LoginScreen.test.ts`

- [ ] **Step 1: Add failing component tests for structured login error body**

Create `apps/frontend/src/components/LoginScreen.test.ts`:

```ts
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const loginWithPasswordMock = vi.hoisted(() => vi.fn());

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    loginWithPassword: loginWithPasswordMock,
  }),
}));

async function fillAndSubmitLoginForm(wrapper: VueWrapper) {
  await wrapper.get('input[type="email"]').setValue("editor@example.local");
  await wrapper.get('input[type="password"]').setValue("wrong-password");
  await wrapper.get("form").trigger("submit");
  await flushPromises();
}

describe("LoginScreen", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("shows structured message for invalid credentials", async () => {
    loginWithPasswordMock.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          code: "INVALID_CREDENTIALS",
          message: "Неверная электронная почта или пароль",
          correlationId: "login-correlation-id",
        },
      },
    });

    const { default: LoginScreen } = await import("@/components/LoginScreen.vue");
    const wrapper = mount(LoginScreen);

    await fillAndSubmitLoginForm(wrapper);

    expect(loginWithPasswordMock).toHaveBeenCalledWith(
      "editor@example.local",
      "wrong-password",
    );
    expect(wrapper.get(".errorMessage").text()).toBe(
      "Неверная электронная почта или пароль",
    );
  });

  it("uses generic fallback when invalid login response has no structured message", async () => {
    loginWithPasswordMock.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          detail: "legacy detail should not be rendered",
        },
      },
    });

    const { default: LoginScreen } = await import("@/components/LoginScreen.vue");
    const wrapper = mount(LoginScreen);

    await fillAndSubmitLoginForm(wrapper);

    expect(wrapper.get(".errorMessage").text()).toBe(
      "Сейчас не удалось выполнить вход. Попробуйте ещё раз.",
    );
  });
});
```

- [ ] **Step 2: Run frontend login component tests and verify they fail**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/components/LoginScreen.test.ts
```

Expected: the structured `message` test fails because `LoginScreen.vue` still reads `data.detail`; the legacy `detail` fallback test fails if the component renders legacy `detail`.

## Task 5: Frontend Login Error Parser

**Files:**

- Modify: `apps/frontend/src/components/LoginScreen.vue`

- [ ] **Step 1: Replace `detail` parsing with `message` parsing**

In `apps/frontend/src/components/LoginScreen.vue`, replace the `catch` block inside `onSubmit()` with:

```ts
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const message =
        typeof error.response?.data?.message === "string"
          ? error.response.data.message
          : "";

      if (status === 401 && message) {
        errorMessage.value = message;
      } else {
        errorMessage.value =
          "Сейчас не удалось выполнить вход. Попробуйте ещё раз.";
      }
    } else {
      errorMessage.value =
        "Сейчас не удалось выполнить вход. Попробуйте ещё раз.";
    }
```

Do not change the form markup, store call, styling, or `http` interceptor in this task.

- [ ] **Step 2: Run frontend login component tests and verify they pass**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/components/LoginScreen.test.ts
```

Expected: both `LoginScreen` tests pass.

- [ ] **Step 3: Run nearby frontend auth/workflow regression tests**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/components/LoginScreen.test.ts src/stores/auth.test.ts src/stores/workOrders.test.ts
```

Expected: all listed frontend tests pass.

## Task 6: Regression Gates And Knowledge Sync Decision

**Files:**

- Possibly modify via repository-change ingest: `Code_wiki/архитектура/api_and_realtime.md`

- [ ] **Step 1: Run backend targeted regression gate**

Run from `apps/backend`:

```powershell
pytest utility_service/use_cases/tests/test_auth_service.py utility_service/web_api/tests/test_auth_api.py utility_service/web_api/tests/test_exception_handlers.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_work_orders_api.py -q
```

Expected: all listed backend tests pass.

- [ ] **Step 2: Run frontend targeted regression gate**

Run from `apps/frontend`:

```powershell
npm run test -- --run src/components/LoginScreen.test.ts src/stores/auth.test.ts src/stores/workOrders.test.ts
```

Expected: all listed frontend tests pass.

- [ ] **Step 3: Run frontend typecheck**

Run from `apps/frontend`:

```powershell
npm run typecheck
```

Expected: typecheck exits with code 0.

- [ ] **Step 4: Search for stale `detail` and `details` assumptions in touched surface**

Run from repository root:

```powershell
rg -n "response\\.data\\.detail|\\\"details\\\"|details|detail" apps/backend/utility_service/web_api apps/backend/utility_service/use_cases apps/frontend/src/components/LoginScreen.vue apps/frontend/src/components/LoginScreen.test.ts
```

Expected:

- no `response.data.detail` usage in `LoginScreen.vue`;
- no expected `details` field in tests for `AuthApiError`, `UtilityNetworkApiError`, or `WorkOrderApiError`;
- unrelated FastAPI `detail` usage in `decode_token()` may remain because token decode is converted to `AuthApiError` by `get_current_user()`;
- unrelated non-scope handlers may still return `{"error": ...}` or `VERSION_MISMATCH` body.

- [ ] **Step 5: Decide and perform repository-change ingest for durable API docs**

Because `Code_wiki/архитектура/api_and_realtime.md` currently states that structured errors include `details`, this implementation creates durable technical knowledge that can make Code_wiki stale.

Follow `.agents/skills/source-command-ingest/SKILL.md` in `/ingest repository-change` mode. The expected documentation outcome is that `Code_wiki/архитектура/api_and_realtime.md` describes structured auth, utility network, and work order/workspace errors as `{code, message, correlationId}` without `details`.

Do not edit production code, tests, migrations, or config during repository-change ingest.

- [ ] **Step 6: Run memory-needed check if memory or knowledge-pipeline files changed**

If repository-change ingest modified `Code_wiki` only, no `scripts/check-memory-needed.py --check` run is required by the memory protocol. If the implementation changed `docs/agent-memory`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/knowledge-pipeline/`, or repo-local command skills, run from repository root:

```powershell
python scripts/check-memory-needed.py --check
```

Expected: either no memory update required, or update an existing durable memory entry before finishing.

- [ ] **Step 7: Final status**

Summarize:

- changed contract: `{code, message, correlationId}`;
- invalid login code: `INVALID_CREDENTIALS`;
- regression commands and results;
- whether repository-change ingest updated Code_wiki;
- whether durable agent memory was needed.

## Self-Review

- Spec coverage:
  - invalid credentials is covered by Task 1 and Task 2;
  - strict handler body without `details` is covered by Task 2 and Task 3;
  - frontend login `message` rendering is covered by Task 4 and Task 5;
  - workflow strict response is covered by Task 2 and Task 3;
  - non-goals are preserved because no tasks modify WebSocket, FastAPI validation, Feature/Layer, `VERSION_MISMATCH`, workOrders fallback UI, or global error bus.
- Placeholder scan:
  - no task contains unspecified implementation work; every changed code path has concrete snippets or exact expected outcomes.
- Type and name consistency:
  - backend uses existing `AuthApiError`, `WorkOrderApiError`, and `UtilityNetworkApiError` fields: `status_code`, `code`, `message`;
  - frontend reads `error.response?.data?.message`, matching response body key `message`;
  - correlation header remains `X-Correlation-ID`, response key remains `correlationId`.
