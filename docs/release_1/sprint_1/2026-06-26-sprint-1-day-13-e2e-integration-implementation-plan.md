# Day 13 Full Path API Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not create a git commit unless the user explicitly asks for it after review.

**Goal:** Add a lightweight CI smoke that verifies the full Sprint 1 API path `login -> assigned work order -> open/reopen edit version -> workspace` in Docker Compose.

**Architecture:** Create a small reusable Python smoke runner under `apps/backend/tests/smoke` and call it from the existing GitHub Actions `smoke_test` job after Compose starts `utility_service`. Keep the smoke outside pytest collection for live-service execution, but add focused unit tests for its request sequencing and assertion behavior. Do not add browser E2E tooling or new product behavior.

**Tech Stack:** Python 3.12 standard library `urllib`, pytest, GitHub Actions, Docker Compose, existing FastAPI Work Orders/Auth/Workspace API, existing demo seed contracts.

---

## File Structure

- Create: `apps/backend/tests/smoke/__init__.py` - makes `tests.smoke` importable for unit tests.
- Create: `apps/backend/tests/smoke/full_path_workspace_smoke.py` - reusable live HTTP smoke runner for the full path.
- Create: `apps/backend/tests/smoke/test_full_path_workspace_smoke.py` - unit tests for smoke runner sequencing, headers and failure messages.
- Modify: `.github/workflows/ci.yml` - add a `Full path workspace API smoke` step to the existing `smoke_test` job.
- Modify: `docs/release_1/sprint_1/README.md` - add the Day 13 implementation plan link.
- Modify: `docs/agent-memory/file-map.md` - update the compact Day 13 retrieval entry with the implementation plan and smoke test file.

The smoke runner intentionally lives under `apps/backend/tests/smoke` because it is test/support code, not production application code. The file name does not start with `test_`, so normal backend `pytest` does not execute live HTTP calls.

## Task 1: Smoke Runner Unit Tests

**Files:**
- Create: `apps/backend/tests/smoke/__init__.py`
- Create: `apps/backend/tests/smoke/test_full_path_workspace_smoke.py`
- Later create: `apps/backend/tests/smoke/full_path_workspace_smoke.py`

- [ ] **Step 1: Create the smoke package marker**

Create `apps/backend/tests/smoke/__init__.py` as an empty file.

- [ ] **Step 2: Write failing smoke runner tests**

Create `apps/backend/tests/smoke/test_full_path_workspace_smoke.py`:

```python
from __future__ import annotations

import json
from urllib.parse import urlparse

import pytest

from tests.smoke.full_path_workspace_smoke import (
    EXPECTED_AOI_ID,
    EXPECTED_ASSOCIATION_COUNT,
    EXPECTED_FEATURE_COUNT,
    EXPECTED_WORK_ORDER_CODE,
    EXPECTED_WORK_ORDER_ID,
    SmokeConfig,
    SmokeFailure,
    assert_workspace,
    run_smoke,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def workspace_payload(
    *,
    work_order_id: str = EXPECTED_WORK_ORDER_ID,
    edit_version_id: str = "edit-version-1",
    aoi_id: str = EXPECTED_AOI_ID,
    feature_count: int = EXPECTED_FEATURE_COUNT,
    association_count: int = EXPECTED_ASSOCIATION_COUNT,
) -> dict:
    return {
        "workOrder": {
            "id": work_order_id,
            "code": EXPECTED_WORK_ORDER_CODE,
            "scope": {
                "aoi": {
                    "id": aoi_id,
                },
            },
            "editVersion": {
                "id": edit_version_id,
                "features": {
                    "type": "FeatureCollection",
                    "features": [{"id": f"feature-{index}"} for index in range(feature_count)],
                },
                "associations": [
                    {"id": f"association-{index}"} for index in range(association_count)
                ],
            },
        }
    }


def fake_opener(routes: dict[tuple[str, str], dict], calls: list[tuple[str, str, str | None]]):
    def opener(request, timeout: int = 10) -> FakeResponse:
        parsed = urlparse(request.full_url)
        method = request.get_method()
        auth_header = request.headers.get("Authorization")
        calls.append((method, parsed.path, auth_header))
        payload = routes[(method, parsed.path)]
        return FakeResponse(payload)

    return opener


def test_run_smoke_uses_assigned_work_order_for_workspace_path() -> None:
    calls: list[tuple[str, str, str | None]] = []
    edit_version_id = "edit-version-1"
    routes = {
        ("POST", "/api/v1/auth/login"): {
            "access_token": "token-1",
            "token_type": "bearer",
        },
        ("GET", "/api/v1/work-orders/assigned-to-me"): {
            "workOrders": [
                {
                    "id": EXPECTED_WORK_ORDER_ID,
                    "code": EXPECTED_WORK_ORDER_CODE,
                    "title": "Проверка участка фидера",
                    "description": "Открыть рабочий участок.",
                    "status": "assigned",
                }
            ]
        },
        ("POST", f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions"): {
            "created": False,
            "editVersion": {
                "id": edit_version_id,
                "workOrderId": EXPECTED_WORK_ORDER_ID,
                "ownerId": "editor-1",
                "status": "open",
                "baseNetworkRevision": 1,
            },
        },
        (
            "GET",
            f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions/"
            f"{edit_version_id}/workspace",
        ): workspace_payload(edit_version_id=edit_version_id),
    }

    config = SmokeConfig(
        base_url="http://utility_service:8000",
        editor_email="alexey.editor@example.local",
        editor_password="alexey-editor-password",
    )

    run_smoke(config, opener=fake_opener(routes, calls))

    assert calls == [
        ("POST", "/api/v1/auth/login", None),
        ("GET", "/api/v1/work-orders/assigned-to-me", "Bearer token-1"),
        ("POST", f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions", "Bearer token-1"),
        (
            "GET",
            f"/api/v1/work-orders/{EXPECTED_WORK_ORDER_ID}/edit-versions/"
            f"{edit_version_id}/workspace",
            "Bearer token-1",
        ),
    ]


def test_run_smoke_fails_when_assigned_list_has_no_expected_work_order() -> None:
    calls: list[tuple[str, str, str | None]] = []
    routes = {
        ("POST", "/api/v1/auth/login"): {
            "access_token": "token-1",
            "token_type": "bearer",
        },
        ("GET", "/api/v1/work-orders/assigned-to-me"): {
            "workOrders": [
                {
                    "id": "other-work-order",
                    "code": "WO-999",
                    "title": "Другой наряд",
                    "description": None,
                    "status": "assigned",
                }
            ]
        },
    }
    config = SmokeConfig(
        base_url="http://utility_service:8000",
        editor_email="alexey.editor@example.local",
        editor_password="alexey-editor-password",
    )

    with pytest.raises(SmokeFailure, match="Проверка назначенного наряда не прошла"):
        run_smoke(config, opener=fake_opener(routes, calls))


def test_assert_workspace_reports_data_slice_mismatch() -> None:
    payload = workspace_payload(feature_count=18)

    with pytest.raises(SmokeFailure, match="Данные workspace не совпадают"):
        assert_workspace(
            payload,
            work_order_id=EXPECTED_WORK_ORDER_ID,
            edit_version_id="edit-version-1",
        )
```

- [ ] **Step 3: Run tests and verify the expected import failure**

Run from `apps/backend`:

```powershell
pytest tests/smoke/test_full_path_workspace_smoke.py -q
```

Expected: FAIL during collection because `tests.smoke.full_path_workspace_smoke` does not exist yet.

## Task 2: Smoke Runner Implementation

**Files:**
- Create: `apps/backend/tests/smoke/full_path_workspace_smoke.py`
- Test: `apps/backend/tests/smoke/test_full_path_workspace_smoke.py`

- [ ] **Step 1: Implement the full path smoke runner**

Create `apps/backend/tests/smoke/full_path_workspace_smoke.py`:

```python
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


EXPECTED_WORK_ORDER_CODE = "WO-001"
EXPECTED_WORK_ORDER_ID = "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401"
EXPECTED_AOI_ID = "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100"
EXPECTED_FEATURE_COUNT = 19
EXPECTED_ASSOCIATION_COUNT = 9

JsonPayload = dict[str, Any]
UrlOpen = Callable[..., Any]


class SmokeFailure(RuntimeError):
    """Raised when the live full path smoke finds a broken runtime contract."""


@dataclass(frozen=True)
class SmokeConfig:
    base_url: str
    editor_email: str
    editor_password: str

    @classmethod
    def from_env(cls) -> "SmokeConfig":
        return cls(
            base_url=os.getenv("GEOSERVICE_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
            editor_email=os.getenv(
                "GEOSERVICE_EDITOR_EMAIL",
                "alexey.editor@example.local",
            ),
            editor_password=os.getenv(
                "GEOSERVICE_EDITOR_PASSWORD",
                "alexey-editor-password",
            ),
        )


def request_json(
    config: SmokeConfig,
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: JsonPayload | None = None,
    opener: UrlOpen = urlopen,
) -> JsonPayload:
    url = f"{config.base_url}{path}"
    headers = {"Accept": "application/json"}
    data: bytes | None = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif method in {"POST", "PUT", "PATCH"}:
        data = b""

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, data=data, headers=headers, method=method)

    try:
        with opener(request, timeout=10) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise SmokeFailure(f"HTTP {exc.code} для {method} {path}: {body}") from exc
    except (OSError, URLError, TimeoutError) as exc:
        raise SmokeFailure(f"HTTP-запрос не выполнен для {method} {path}: {exc}") from exc

    if not body:
        return {}

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"Некорректный JSON для {method} {path}: {body[:500]}") from exc

    if not isinstance(decoded, dict):
        raise SmokeFailure(f"Неожиданная форма JSON для {method} {path}: {decoded!r}")
    return decoded


def login(config: SmokeConfig, *, opener: UrlOpen = urlopen) -> str:
    payload = request_json(
        config,
        "POST",
        "/api/v1/auth/login",
        payload={
            "email": config.editor_email,
            "password": config.editor_password,
        },
        opener=opener,
    )
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise SmokeFailure("Проверка входа не прошла: login не вернул access_token")
    return token


def load_assigned_work_order(
    config: SmokeConfig,
    token: str,
    *,
    opener: UrlOpen = urlopen,
) -> JsonPayload:
    payload = request_json(
        config,
        "GET",
        "/api/v1/work-orders/assigned-to-me",
        token=token,
        opener=opener,
    )
    work_orders = payload.get("workOrders")
    if not isinstance(work_orders, list):
        raise SmokeFailure(
            "Проверка назначенного наряда не прошла: response не содержит список workOrders"
        )

    for item in work_orders:
        if not isinstance(item, dict):
            continue
        if item.get("code") == EXPECTED_WORK_ORDER_CODE:
            work_order_id = item.get("id")
            if work_order_id != EXPECTED_WORK_ORDER_ID:
                raise SmokeFailure(
                    "Проверка назначенного наряда не прошла: "
                    f"id {EXPECTED_WORK_ORDER_CODE} равен {work_order_id!r}, "
                    f"ожидается {EXPECTED_WORK_ORDER_ID}"
                )
            return item

    codes = [item.get("code") for item in work_orders if isinstance(item, dict)]
    raise SmokeFailure(
        "Проверка назначенного наряда не прошла: "
        f"{EXPECTED_WORK_ORDER_CODE} не найден в assigned list {codes!r}"
    )


def open_edit_version(
    config: SmokeConfig,
    token: str,
    work_order_id: str,
    *,
    opener: UrlOpen = urlopen,
) -> str:
    payload = request_json(
        config,
        "POST",
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        token=token,
        opener=opener,
    )
    edit_version = payload.get("editVersion")
    if not isinstance(edit_version, dict):
        raise SmokeFailure(
            "Проверка EditVersion не прошла: response не содержит объект editVersion"
        )

    edit_version_id = edit_version.get("id")
    if not isinstance(edit_version_id, str) or not edit_version_id:
        raise SmokeFailure("Проверка EditVersion не прошла: editVersion.id отсутствует")

    returned_work_order_id = edit_version.get("workOrderId")
    if returned_work_order_id != work_order_id:
        raise SmokeFailure(
            "Проверка EditVersion не прошла: "
            f"editVersion.workOrderId равен {returned_work_order_id!r}, "
            f"ожидается {work_order_id}"
        )

    return edit_version_id


def load_workspace(
    config: SmokeConfig,
    token: str,
    work_order_id: str,
    edit_version_id: str,
    *,
    opener: UrlOpen = urlopen,
) -> JsonPayload:
    return request_json(
        config,
        "GET",
        f"/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace",
        token=token,
        opener=opener,
    )


def assert_workspace(
    payload: JsonPayload,
    *,
    work_order_id: str,
    edit_version_id: str,
) -> None:
    work_order = payload.get("workOrder")
    if not isinstance(work_order, dict):
        raise SmokeFailure(
            "Агрегат workspace не совпадает: response не содержит объект workOrder"
        )

    if work_order.get("id") != work_order_id:
        raise SmokeFailure(
            "Агрегат workspace не совпадает: "
            f"workOrder.id равен {work_order.get('id')!r}, ожидается {work_order_id}"
        )

    scope = work_order.get("scope")
    aoi = scope.get("aoi") if isinstance(scope, dict) else None
    if not isinstance(aoi, dict) or aoi.get("id") != EXPECTED_AOI_ID:
        actual_aoi_id = aoi.get("id") if isinstance(aoi, dict) else None
        raise SmokeFailure(
            "Данные workspace не совпадают: "
            f"AOI id равен {actual_aoi_id!r}, ожидается {EXPECTED_AOI_ID}"
        )

    edit_version = work_order.get("editVersion")
    if not isinstance(edit_version, dict) or edit_version.get("id") != edit_version_id:
        actual_edit_version_id = (
            edit_version.get("id") if isinstance(edit_version, dict) else None
        )
        raise SmokeFailure(
            "Агрегат workspace не совпадает: "
            f"editVersion.id равен {actual_edit_version_id!r}, ожидается {edit_version_id}"
        )

    features_payload = edit_version.get("features")
    features = features_payload.get("features") if isinstance(features_payload, dict) else None
    if not isinstance(features, list) or len(features) != EXPECTED_FEATURE_COUNT:
        actual_count = len(features) if isinstance(features, list) else None
        raise SmokeFailure(
            "Данные workspace не совпадают: "
            f"количество features равно {actual_count!r}, ожидается {EXPECTED_FEATURE_COUNT}"
        )

    associations = edit_version.get("associations")
    if not isinstance(associations, list) or len(associations) != EXPECTED_ASSOCIATION_COUNT:
        actual_count = len(associations) if isinstance(associations, list) else None
        raise SmokeFailure(
            "Данные workspace не совпадают: "
            f"количество associations равно {actual_count!r}, "
            f"ожидается {EXPECTED_ASSOCIATION_COUNT}"
        )


def run_smoke(config: SmokeConfig, *, opener: UrlOpen = urlopen) -> None:
    token = login(config, opener=opener)
    work_order = load_assigned_work_order(config, token, opener=opener)
    work_order_id = str(work_order["id"])
    edit_version_id = open_edit_version(config, token, work_order_id, opener=opener)
    workspace = load_workspace(config, token, work_order_id, edit_version_id, opener=opener)
    assert_workspace(
        workspace,
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
    )
    print(
        "Полный smoke-путь workspace прошел успешно: "
        f"{EXPECTED_WORK_ORDER_CODE} -> {edit_version_id}, "
        f"features={EXPECTED_FEATURE_COUNT}, associations={EXPECTED_ASSOCIATION_COUNT}"
    )


def main() -> int:
    try:
        run_smoke(SmokeConfig.from_env())
    except SmokeFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run smoke runner unit tests**

Run from `apps/backend`:

```powershell
pytest tests/smoke/test_full_path_workspace_smoke.py -q
```

Expected: PASS with 3 tests.

- [ ] **Step 3: Run formatter and linter on smoke files**

Run from `apps/backend`:

```powershell
black --check tests/smoke/full_path_workspace_smoke.py tests/smoke/test_full_path_workspace_smoke.py
ruff check tests/smoke/full_path_workspace_smoke.py tests/smoke/test_full_path_workspace_smoke.py
```

Expected: PASS. If Black reports formatting changes are needed, run:

```powershell
black tests/smoke/full_path_workspace_smoke.py tests/smoke/test_full_path_workspace_smoke.py
```

Then rerun the checks.

## Task 3: CI Full Path Smoke Step

**Files:**
- Modify: `.github/workflows/ci.yml`
- Uses: `apps/backend/tests/smoke/full_path_workspace_smoke.py`

- [ ] **Step 1: Add the CI smoke step**

In `.github/workflows/ci.yml`, inside job `smoke_test`, add this step after the existing `Workspace authenticated API smoke` step and before `Teardown`:

```yaml
      - name: Full path workspace API smoke
        working-directory: infra
        run: |
          docker compose -f docker-compose.yml exec -T utility_service \
            python tests/smoke/full_path_workspace_smoke.py
```

Keep the existing `Utility dataset authenticated API smoke` and `Workspace authenticated API smoke` steps. They can be consolidated in a later cleanup, but Day 13 only adds the missing full path through `assigned-to-me`.

- [ ] **Step 2: Validate workflow syntax by inspection**

Run from repo root:

```powershell
rg -n "Full path workspace API smoke|full_path_workspace_smoke.py" .github\workflows\ci.yml
```

Expected:

```text
The command prints two matches: one for the step name and one for the
`python tests/smoke/full_path_workspace_smoke.py` command.
```

- [ ] **Step 3: Run existing backend unit smoke locally**

Run from `apps/backend`:

```powershell
pytest tests/smoke/test_full_path_workspace_smoke.py utility_service/web_api/tests/test_work_orders_api.py utility_service/use_cases/tests/test_workspace_service.py -q
```

Expected: PASS. This does not prove Compose runtime, but it protects the smoke script and the route/use-case contracts before CI executes the live service.

## Task 4: Local Compose Smoke Verification

**Files:**
- No additional file edits.
- Uses: `infra/docker-compose.yml`
- Uses: `apps/backend/tests/smoke/full_path_workspace_smoke.py`

- [ ] **Step 1: Start the Compose backend stack if local Docker is available**

Run from repo root:

```powershell
cd infra
docker compose -f docker-compose.yml up -d --build postgis utility_service
```

Expected: `postgis` and `utility_service` start. If Docker is not available in the local environment, skip to Task 4 Step 5 and record that local Compose smoke was not run.

- [ ] **Step 2: Wait for utility_service health**

Run from `infra`:

```powershell
$containerId = docker compose -f docker-compose.yml ps -q utility_service
docker inspect -f "{{.State.Health.Status}}" $containerId
```

Expected:

```text
healthy
```

If the status is `starting`, wait and rerun. If it becomes `unhealthy`, inspect logs:

```powershell
docker compose -f docker-compose.yml logs utility_service --tail=200
```

- [ ] **Step 3: Run the full path smoke inside the container**

Run from `infra`:

```powershell
docker compose -f docker-compose.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
```

Expected output contains:

```text
Полный smoke-путь workspace прошел успешно: WO-001
features=19, associations=9
```

The command must exit with code `0`.

- [ ] **Step 4: Run the smoke a second time**

Run from `infra`:

```powershell
docker compose -f docker-compose.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
```

Expected: PASS again. This confirms idempotent reopen behavior when `EditVersion` already exists and `POST /edit-versions` returns `200 created=false`.

- [ ] **Step 5: Tear down the local stack if this task started it**

Run from `infra`:

```powershell
docker compose -f docker-compose.yml down -v
```

Expected: containers and `geo_pgdata` volume from this smoke run are removed. Do not run this command if the user already had a local dev stack running before this task.

## Task 5: Sprint Documentation And Retrieval Map

**Files:**
- Modify: `docs/release_1/sprint_1/README.md`
- Modify: `docs/agent-memory/file-map.md`
- Uses: `docs/release_1/sprint_1/2026-06-26-sprint-1-day-13-e2e-integration-design.md`
- Uses: `docs/release_1/sprint_1/2026-06-26-sprint-1-day-13-e2e-integration-implementation-plan.md`

- [ ] **Step 1: Add the implementation plan link to sprint README**

In `docs/release_1/sprint_1/README.md`, directly after the Day 13 design link, add:

```markdown
- [План реализации End-to-end интеграции Дня 13](2026-06-26-sprint-1-day-13-e2e-integration-implementation-plan.md)
```

The Day 13 block should become:

```markdown
- [End-to-end интеграция Дня 13](2026-06-26-sprint-1-day-13-e2e-integration-design.md)
- [План реализации End-to-end интеграции Дня 13](2026-06-26-sprint-1-day-13-e2e-integration-implementation-plan.md)
```

- [ ] **Step 2: Update the file-map Day 13 entry**

In `docs/agent-memory/file-map.md`, replace the current Day 13 entry with:

```markdown
- GeoService Sprint 1 Day 13 full path API smoke: `docs/release_1/sprint_1/2026-06-26-sprint-1-day-13-e2e-integration-design.md`, `docs/release_1/sprint_1/2026-06-26-sprint-1-day-13-e2e-integration-implementation-plan.md`, `.github/workflows/ci.yml`, `apps/backend/tests/smoke/full_path_workspace_smoke.py`, `apps/backend/tests/smoke/test_full_path_workspace_smoke.py`
```

- [ ] **Step 3: Verify links and retrieval text**

Run from repo root:

```powershell
rg -n "Day 13 full path API smoke|End-to-end интеграция Дня 13|План реализации End-to-end интеграции Дня 13" docs\agent-memory\file-map.md docs\release_1\sprint_1\README.md
```

Expected: matches in `file-map.md` and both Day 13 README links.

## Task 6: Final Verification

**Files:**
- No additional file edits.

- [ ] **Step 1: Run focused backend verification**

Run from `apps/backend`:

```powershell
pytest tests/smoke/test_full_path_workspace_smoke.py utility_service/web_api/tests/test_work_orders_api.py utility_service/use_cases/tests/test_workspace_service.py -q
```

Expected: PASS.

- [ ] **Step 2: Run backend formatting/lint checks for changed Python files**

Run from `apps/backend`:

```powershell
black --check tests/smoke/full_path_workspace_smoke.py tests/smoke/test_full_path_workspace_smoke.py
ruff check tests/smoke/full_path_workspace_smoke.py tests/smoke/test_full_path_workspace_smoke.py
```

Expected: PASS.

- [ ] **Step 3: Run local Compose smoke if Docker is available**

Run from `infra` after the stack is healthy:

```powershell
docker compose -f docker-compose.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
docker compose -f docker-compose.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
```

Expected: both runs PASS. If Docker is unavailable or starting Compose would disrupt a user-owned local stack, record that this verification was not run.

- [ ] **Step 4: Run memory-needed check because file-map changed**

Run from repo root:

```powershell
python scripts/check-memory-needed.py --check
```

Expected:

```text
Memory update check passed.
```

If the local `python` command resolves to the Windows Store launcher instead of a real interpreter, use the bundled runtime available in the Codex desktop environment:

```powershell
& 'C:\Users\dimon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\check-memory-needed.py --check
```

- [ ] **Step 5: Review final working tree without staging**

Run from repo root:

```powershell
git status --short
```

Expected changed files include the smoke runner, smoke tests, CI workflow and docs. Existing unrelated changes such as `.obsidian/graph.json` must remain untouched. Do not run `git add` or `git commit` unless the user explicitly asks for Git operations after review.

## Self-Review Notes

- Spec coverage: Task 1 and Task 2 implement the reusable smoke runner and diagnostic assertions. Task 3 integrates it into CI. Task 4 verifies the same path locally in Docker Compose when available. Task 5 updates sprint navigation and retrieval. Task 6 covers focused tests, lint, Compose smoke, memory gate and git status.
- Scope guard: the plan does not add Playwright, Cypress, browser automation, new endpoints, frontend behavior, seed semantics changes, editing, validation, reconcile, review, post, audit workflow or performance benchmarking.
- Type consistency: tests and implementation use the same exported names: `SmokeConfig`, `SmokeFailure`, `run_smoke`, `assert_workspace`, `EXPECTED_WORK_ORDER_CODE`, `EXPECTED_WORK_ORDER_ID`, `EXPECTED_AOI_ID`, `EXPECTED_FEATURE_COUNT`, `EXPECTED_ASSOCIATION_COUNT`.
- Idempotency: Task 4 runs the live smoke twice to prove both clean open and reopen paths are acceptable.
- Git rule: the plan intentionally leaves staging and committing out of the task steps because this repository requires explicit user approval for Git operations.
