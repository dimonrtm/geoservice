# Legacy GIS API Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Закрыть legacy `/api/v1/layers*` и `/api/v1/ws/layers*` по secure-by-default feature flag и разрешать compatibility-доступ только активному `Editor`.

**Architecture:** Backend получает `LEGACY_GIS_API_ENABLED=false` по умолчанию и единый guard `require_legacy_gis_editor`. Legacy REST endpoints и HTTP endpoint выдачи websocket ticket проходят через этот guard; сам websocket handshake остается ticket-only, а `WebSocketTicketService` дополнительно допускает только `editor` как defense-in-depth.

**Tech Stack:** FastAPI, Pydantic settings, pytest, Starlette TestClient, SQLAlchemy async service dependencies.

---

## Source Spec

- `docs/superpowers/specs/2026-07-05-legacy-gis-api-guard-design.md`

## Scope Check

План покрывает один связный security slice: settings flag, backend guard, REST legacy layer routes, websocket ticket issue, service-level realtime role defense-in-depth, regression tests и repository-change ingest после реализации. Object-level ACL, workspace realtime и новый workspace-specific layer API остаются вне scope.

## File Structure

Modify:

- `apps/backend/utility_service/utils/settings.py` - добавить `legacy_gis_api_enabled`.
- `apps/backend/utility_service/utils/tests/test_settings.py` - закрепить default `False` и env alias.
- `apps/backend/utility_service/web_api/api/auth.py` - добавить `LEGACY_GIS_API_DISABLED_CODE`, `LEGACY_GIS_API_DISABLED_MESSAGE`, `require_legacy_gis_editor`.
- `apps/backend/utility_service/web_api/tests/test_auth_access.py` - unit tests для нового guard.
- `apps/backend/utility_service/web_api/api/layers.py` - заменить общий `get_current_user`/mutation-only `require_editor` на единый legacy guard для всего router.
- `apps/backend/utility_service/web_api/api/ws_layers.py` - выдавать websocket ticket только через `require_legacy_gis_editor`.
- `apps/backend/utility_service/web_api/tests/test_ws_layers.py` - обновить ticket issue tests и сузить subscription role fixture до `editor`.
- `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py` - разрешить realtime ticket consume/issue только для `editor`.
- `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py` - обновить service-level expectations с `reviewer` на reject.

Create:

- `apps/backend/utility_service/web_api/tests/test_layers_api.py` - route-level regression tests для legacy REST flag/role behavior.

Docs after implementation:

- Run `/ingest repository-change` so `Code_wiki/архитектура/api_and_realtime.md` and `Code_wiki/архитектура/backend.md` stop stating that `reviewer` can read legacy layers/realtime.

---

### Task 1: Settings And Auth Guard

**Files:**

- Modify: `apps/backend/utility_service/utils/tests/test_settings.py`
- Modify: `apps/backend/utility_service/utils/settings.py`
- Modify: `apps/backend/utility_service/web_api/tests/test_auth_access.py`
- Modify: `apps/backend/utility_service/web_api/api/auth.py`

- [ ] **Step 1: Write failing settings tests**

Append to `apps/backend/utility_service/utils/tests/test_settings.py` after `test_settings_reads_websocket_ticket_ttl_seconds_from_env_alias`:

```python
def test_settings_defaults_legacy_gis_api_enabled_to_false() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.legacy_gis_api_enabled is False


def test_settings_reads_legacy_gis_api_enabled_from_env_alias() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        LEGACY_GIS_API_ENABLED=True,
    )

    assert settings.legacy_gis_api_enabled is True
```

- [ ] **Step 2: Run settings tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'legacy_gis_api_enabled'`.

- [ ] **Step 3: Add the settings field**

In `apps/backend/utility_service/utils/settings.py`, add this field after `dev_auth_enabled`:

```python
    legacy_gis_api_enabled: bool = Field(False, alias="LEGACY_GIS_API_ENABLED")
```

- [ ] **Step 4: Run settings tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: PASS.

- [ ] **Step 5: Write failing auth guard tests**

Append to `apps/backend/utility_service/web_api/tests/test_auth_access.py` after `test_role_guards_are_mutually_exclusive`:

```python
def test_legacy_gis_guard_returns_feature_flag_error_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", False)
    editor = SimpleNamespace(role=SimpleNamespace(value="editor"))

    with pytest.raises(AuthApiError) as exc_info:
        auth_api.require_legacy_gis_editor(editor)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "LEGACY_GIS_API_DISABLED"
    assert exc_info.value.message == "Legacy GIS API отключен."


def test_legacy_gis_guard_allows_editor_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    editor = SimpleNamespace(role=SimpleNamespace(value="editor"))

    assert auth_api.require_legacy_gis_editor(editor) is editor


def test_legacy_gis_guard_rejects_reviewer_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    reviewer = SimpleNamespace(role=SimpleNamespace(value="reviewer"))

    with pytest.raises(AuthApiError) as exc_info:
        auth_api.require_legacy_gis_editor(reviewer)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
```

- [ ] **Step 6: Run auth guard tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_auth_access.py::test_legacy_gis_guard_returns_feature_flag_error_when_disabled utility_service/web_api/tests/test_auth_access.py::test_legacy_gis_guard_allows_editor_when_enabled utility_service/web_api/tests/test_auth_access.py::test_legacy_gis_guard_rejects_reviewer_when_enabled -q
```

Expected: FAIL with `AttributeError: module 'utility_service.web_api.api.auth' has no attribute 'require_legacy_gis_editor'`.

- [ ] **Step 7: Implement the auth guard**

In `apps/backend/utility_service/web_api/api/auth.py`, add constants after `REVIEWER_ROLE`:

```python
LEGACY_GIS_API_DISABLED_CODE = "LEGACY_GIS_API_DISABLED"
LEGACY_GIS_API_DISABLED_MESSAGE = "Legacy GIS API отключен."
```

Then add this function after `require_editor`:

```python
def require_legacy_gis_editor(user: Any = Depends(get_current_user)) -> Any:
    if not settings.legacy_gis_api_enabled:
        raise AuthApiError(
            status.HTTP_403_FORBIDDEN,
            LEGACY_GIS_API_DISABLED_CODE,
            LEGACY_GIS_API_DISABLED_MESSAGE,
        )
    return require_editor(user)
```

- [ ] **Step 8: Run settings and auth tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_access.py -q
```

Expected: PASS.

---

### Task 2: Legacy REST Layers Guard

**Files:**

- Create: `apps/backend/utility_service/web_api/tests/test_layers_api.py`
- Modify: `apps/backend/utility_service/web_api/api/layers.py`

- [ ] **Step 1: Write failing route regression tests**

Create `apps/backend/utility_service/web_api/tests/test_layers_api.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import (
    get_auth_service,
    get_feature_service,
    get_layer_service,
)
from utility_service.use_cases.schemas.feature.delete_feature_response import (
    DeleteFeatureResponse,
)
from utility_service.use_cases.schemas.feature.feature_collection_out import (
    FeatureCollectionMetaOut,
    FeatureCollectionOut,
)
from utility_service.use_cases.schemas.feature.feature_out import FeatureOut
from utility_service.use_cases.schemas.layer.layer_list_out import LayerListOut
from utility_service.use_cases.schemas.layer.layer_out import LayerOut
from utility_service.web_api.api import auth as auth_api
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.layers import layers_router


USER_ID = UUID("10000000-0000-0000-0000-000000000001")
LAYER_ID = UUID("20000000-0000-0000-0000-000000000001")
FEATURE_ID = UUID("30000000-0000-0000-0000-000000000001")


@dataclass(frozen=True)
class LegacyLayerRequest:
    method: str
    path: str
    params: dict[str, str] | None = None
    json: dict[str, object] | None = None


LEGACY_LAYER_REQUESTS = [
    LegacyLayerRequest("GET", "/api/v1/layers"),
    LegacyLayerRequest(
        "GET",
        f"/api/v1/layers/{LAYER_ID}/features",
        params={"bbox": "0,0,1,1"},
    ),
    LegacyLayerRequest(
        "GET",
        f"/api/v1/layers/{LAYER_ID}/features/{FEATURE_ID}",
    ),
    LegacyLayerRequest(
        "POST",
        f"/api/v1/layers/{LAYER_ID}/features",
        json={
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
            "properties": {"name": "Created"},
        },
    ),
    LegacyLayerRequest(
        "PATCH",
        f"/api/v1/layers/{LAYER_ID}/features/{FEATURE_ID}",
        json={
            "version": 1,
            "geometry": None,
            "properties": {"name": "Updated"},
        },
    ),
    LegacyLayerRequest(
        "DELETE",
        f"/api/v1/layers/{LAYER_ID}/features/{FEATURE_ID}",
        json={"version": 1},
    ),
]


class FakeLayerService:
    def __init__(self):
        self.get_layers_calls = 0

    async def get_layers(self) -> LayerListOut:
        self.get_layers_calls += 1
        return LayerListOut(
            layers=[
                LayerOut(
                    id=LAYER_ID,
                    name="points",
                    title="Points",
                    geometryType="Point",
                    srid=4326,
                )
            ]
        )


class FakeFeatureService:
    def __init__(self):
        self.calls: list[tuple[str, UUID]] = []

    async def get_features_from_bbox(self, layer_id, bbox, limit, after_id):
        self.calls.append(("get_features_from_bbox", layer_id))
        return FeatureCollectionOut(
            features=[],
            meta=FeatureCollectionMetaOut(
                bbox=(bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat),
                limit=limit or 500,
                returned=0,
                truncated=False,
            ),
        )

    async def create_feature(self, layer_id, request):
        self.calls.append(("create_feature", layer_id))
        return feature_out(version=1, properties=request.properties)

    async def update_feature(self, layer_id, feature_id, request):
        self.calls.append(("update_feature", layer_id))
        return feature_out(version=request.version + 1, properties=request.properties or {})

    async def delete_feature(self, layer_id, feature_id, request):
        self.calls.append(("delete_feature", layer_id))
        return DeleteFeatureResponse(featureId=feature_id)

    async def get_feature(self, layer_id, feature_id):
        self.calls.append(("get_feature", layer_id))
        return feature_out(version=1, properties={"name": "Existing"})


def feature_out(version: int, properties: dict[str, object]) -> FeatureOut:
    return FeatureOut(
        id=FEATURE_ID,
        version=version,
        geometry={"type": "Point", "coordinates": [1.0, 2.0]},
        properties=properties,
    )


def build_app(role: str, layer_service: FakeLayerService, feature_service: FakeFeatureService):
    user = SimpleNamespace(
        id=USER_ID,
        email=f"{role}@example.local",
        role=SimpleNamespace(value=role),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(layers_router)
    app.dependency_overrides[get_auth_service] = lambda: SimpleNamespace(
        get_user_by_id=get_user_by_id
    )
    app.dependency_overrides[get_layer_service] = lambda: layer_service
    app.dependency_overrides[get_feature_service] = lambda: feature_service
    return app


def auth_headers(role: str) -> dict[str, str]:
    token = create_access_token(str(USER_ID), role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("role", ["editor", "reviewer"])
@pytest.mark.parametrize("request_spec", LEGACY_LAYER_REQUESTS)
def test_legacy_layers_disabled_blocks_authenticated_roles(
    monkeypatch,
    role: str,
    request_spec: LegacyLayerRequest,
) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", False)
    layer_service = FakeLayerService()
    feature_service = FakeFeatureService()
    client = TestClient(build_app(role, layer_service, feature_service))

    response = client.request(
        request_spec.method,
        request_spec.path,
        headers=auth_headers(role),
        params=request_spec.params,
        json=request_spec.json,
    )

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "LEGACY_GIS_API_DISABLED"
    assert body["message"] == "Legacy GIS API отключен."
    assert layer_service.get_layers_calls == 0
    assert feature_service.calls == []


@pytest.mark.parametrize("request_spec", LEGACY_LAYER_REQUESTS)
def test_legacy_layers_enabled_blocks_reviewer_before_services(
    monkeypatch,
    request_spec: LegacyLayerRequest,
) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    layer_service = FakeLayerService()
    feature_service = FakeFeatureService()
    client = TestClient(build_app("reviewer", layer_service, feature_service))

    response = client.request(
        request_spec.method,
        request_spec.path,
        headers=auth_headers("reviewer"),
        params=request_spec.params,
        json=request_spec.json,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    assert layer_service.get_layers_calls == 0
    assert feature_service.calls == []


def test_legacy_layers_enabled_allows_editor_to_list_layers(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    layer_service = FakeLayerService()
    feature_service = FakeFeatureService()
    client = TestClient(build_app("editor", layer_service, feature_service))

    response = client.get("/api/v1/layers", headers=auth_headers("editor"))

    assert response.status_code == 200
    assert response.json() == {
        "layers": [
            {
                "id": str(LAYER_ID),
                "name": "points",
                "title": "Points",
                "geometryType": "Point",
                "srid": 4326,
            }
        ]
    }
    assert layer_service.get_layers_calls == 1
```

- [ ] **Step 2: Run new route tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_layers_api.py -q
```

Expected: FAIL because disabled requests return `200` or reach feature handlers instead of `403 LEGACY_GIS_API_DISABLED`.

- [ ] **Step 3: Apply the legacy guard to `layers_router`**

In `apps/backend/utility_service/web_api/api/layers.py`, replace:

```python
from .auth import get_current_user, require_editor

layers_router = APIRouter(
    prefix="/api/v1/layers", tags=["layers"], dependencies=[Depends(get_current_user)]
)
```

with:

```python
from .auth import require_legacy_gis_editor

layers_router = APIRouter(
    prefix="/api/v1/layers",
    tags=["layers"],
    dependencies=[Depends(require_legacy_gis_editor)],
)
```

Then remove the `dependencies=[Depends(require_editor)]` argument from the `@layers_router.post`, `@layers_router.patch`, and `@layers_router.delete` decorators. The decorators should become:

```python
@layers_router.post(
    "/{layer_id}/features",
    status_code=status.HTTP_201_CREATED,
    response_model=FeatureOut,
)
```

```python
@layers_router.patch(
    "/{layer_id}/features/{feature_id}",
    response_model=PatchFeatureSuccesResponse,
)
```

```python
@layers_router.delete(
    "/{layer_id}/features/{feature_id}",
    response_model=DeleteFeatureResponse,
)
```

- [ ] **Step 4: Run route tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_layers_api.py utility_service/web_api/tests/test_auth_access.py -q
```

Expected: PASS.

---

### Task 3: WebSocket Ticket Route Guard

**Files:**

- Modify: `apps/backend/utility_service/web_api/tests/test_ws_layers.py`
- Modify: `apps/backend/utility_service/web_api/api/ws_layers.py`

- [ ] **Step 1: Update ticket issue route tests**

In `apps/backend/utility_service/web_api/tests/test_ws_layers.py`, add this import:

```python
from utility_service.web_api.api import auth as auth_api
```

Replace `test_ws_layer_ticket_issue_accepts_authenticated_realtime_roles` with these tests:

```python
def test_ws_layer_ticket_issue_accepts_editor_when_legacy_enabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    user = SimpleNamespace(
        id=user_id,
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    ticket_service = FakeWebSocketTicketService(ticket="editor-ticket")
    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "ticket": "editor-ticket",
        "expiresAt": "2026-07-02T10:00:00Z",
    }
    assert ticket_service.issued == [(user, layer_id)]


def test_ws_layer_ticket_issue_rejects_editor_when_legacy_disabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", False)
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    user = SimpleNamespace(
        id=user_id,
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    ticket_service = FakeWebSocketTicketService(ticket="editor-ticket")
    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["code"] == "LEGACY_GIS_API_DISABLED"
    assert ticket_service.issued == []


def test_ws_layer_ticket_issue_rejects_reviewer_when_legacy_enabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "reviewer")
    user = SimpleNamespace(
        id=user_id,
        email="reviewer@example.com",
        role=SimpleNamespace(value="reviewer"),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    ticket_service = FakeWebSocketTicketService(ticket="reviewer-ticket")
    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    assert ticket_service.issued == []
```

In `test_ws_layer_ticket_issue_returns_structured_layer_not_found`, add this line as the first statement:

```python
    monkeypatch.setattr(auth_api.settings, "legacy_gis_api_enabled", True)
```

and add `monkeypatch` to the function signature:

```python
def test_ws_layer_ticket_issue_returns_structured_layer_not_found(monkeypatch) -> None:
```

Replace the subscription test parametrization:

```python
@pytest.mark.parametrize("role", ["editor", "reviewer"])
def test_ws_layer_subscription_accepts_authorized_users(role: str) -> None:
```

with:

```python
def test_ws_layer_subscription_accepts_valid_editor_ticket() -> None:
    role = "editor"
```

- [ ] **Step 2: Run websocket route tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_ws_layers.py -q
```

Expected: FAIL because `POST /api/v1/ws/layers/{layer_id}/ticket` still uses `get_current_user` and does not check `LEGACY_GIS_API_ENABLED`.

- [ ] **Step 3: Apply the legacy guard to ticket issue**

In `apps/backend/utility_service/web_api/api/ws_layers.py`, replace:

```python
from utility_service.web_api.api.auth import get_current_user
```

with:

```python
from utility_service.web_api.api.auth import require_legacy_gis_editor
```

Then update the ticket endpoint dependency:

```python
async def issue_layer_websocket_ticket(
    layer_id: UUID,
    user: Any = Depends(require_legacy_gis_editor),
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
) -> WebSocketTicketOut:
    return await ticket_service.issue_ticket(user, layer_id)
```

- [ ] **Step 4: Run websocket route tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/web_api/tests/test_ws_layers.py utility_service/web_api/tests/test_auth_access.py -q
```

Expected: PASS.

---

### Task 4: WebSocket Ticket Service Defense-In-Depth

**Files:**

- Modify: `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py`
- Modify: `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`

- [ ] **Step 1: Update service tests to reject reviewer**

In `apps/backend/utility_service/use_cases/tests/test_websocket_ticket_service.py`, replace:

```python
def test_issue_ticket_rejects_role_not_allowed() -> None:
    user = make_user(role="viewer")
```

with:

```python
@pytest.mark.parametrize("role", ["viewer", "reviewer"])
def test_issue_ticket_rejects_role_not_allowed(role: str) -> None:
    user = make_user(role=role)
```

In `test_consume_ticket_returns_user_context_once`, replace:

```python
    user = make_user(role="reviewer")
```

with:

```python
    user = make_user(role="editor")
```

and replace:

```python
    assert context.role == "reviewer"
```

with:

```python
    assert context.role == "editor"
```

Append this test after `test_consume_ticket_rejects_wrong_layer`:

```python
def test_consume_ticket_rejects_reviewer_user_after_ticket_row_exists() -> None:
    user = make_user(role="reviewer")
    layer = SimpleNamespace(id=uuid4())
    repository = FakeTicketRepository()
    service = WebSocketTicketService(
        DummySession(),
        repository,
        FakeLayerRepository(layer),
        FakeUserRepository(user),
        ticket_ttl_seconds=60,
    )
    ticket = "reviewer-ticket"
    repository.created.append(
        SimpleNamespace(
            ticket_hash=hash_websocket_ticket(ticket),
            user_id=user.id,
            layer_id=layer.id,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=60),
        )
    )

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(ticket, layer.id))
```

- [ ] **Step 2: Run service tests to verify failure**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: FAIL because `reviewer` is still in `ALLOWED_REALTIME_ROLES`.

- [ ] **Step 3: Restrict service allowed realtime roles**

In `apps/backend/utility_service/use_cases/services/websocket_ticket_service.py`, replace:

```python
ALLOWED_REALTIME_ROLES = {"editor", "reviewer"}
```

with:

```python
ALLOWED_REALTIME_ROLES = {"editor"}
```

- [ ] **Step 4: Run service tests to verify pass**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: PASS.

- [ ] **Step 5: Run all focused backend guard tests**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_layers_api.py utility_service/web_api/tests/test_ws_layers.py utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: PASS.

---

### Task 5: Verification And Knowledge Update

**Files:**

- Verify: backend test files from Tasks 1-4
- Update through `/ingest repository-change`: `Code_wiki/архитектура/api_and_realtime.md`, `Code_wiki/архитектура/backend.md`

- [ ] **Step 1: Run the focused backend regression suite**

Run:

```powershell
cd apps/backend
python -m pytest utility_service/utils/tests/test_settings.py utility_service/web_api/tests/test_auth_access.py utility_service/web_api/tests/test_layers_api.py utility_service/web_api/tests/test_ws_layers.py utility_service/use_cases/tests/test_websocket_ticket_service.py -q
```

Expected: PASS.

- [ ] **Step 2: Run backend lint if available in this checkout**

Run:

```powershell
cd apps/backend
python -m ruff check utility_service
```

Expected: PASS. If `ruff` is not installed in the active environment, record the exact error in the final implementation notes and rely on the pytest regression suite above.

- [ ] **Step 3: Inspect for stale reviewer realtime claims in changed code**

Run:

```powershell
rg -n "reviewer.*layers|reviewer.*realtime|ALLOWED_REALTIME_ROLES|LEGACY_GIS_API_ENABLED|LEGACY_GIS_API_DISABLED" apps/backend/utility_service
```

Expected:

- `ALLOWED_REALTIME_ROLES = {"editor"}` appears in `websocket_ticket_service.py`.
- `LEGACY_GIS_API_ENABLED` appears in `settings.py` and `test_settings.py`.
- `LEGACY_GIS_API_DISABLED` appears in `auth.py`, `test_auth_access.py`, `test_layers_api.py`, and `test_ws_layers.py`.
- No production code says that `reviewer` can read legacy layers or subscribe to legacy realtime.

- [ ] **Step 4: Run repository-change ingest for durable technical knowledge**

Run the agent command:

```text
/ingest repository-change
```

Expected: repository-change ingest inspects the completed implementation and updates Code_wiki knowledge about legacy GIS API access. The resulting docs should state that `/api/v1/layers*` and `/api/v1/ws/layers*/ticket` are behind `LEGACY_GIS_API_ENABLED`, default to disabled, and allow only active `Editor` when enabled.

- [ ] **Step 5: Inspect knowledge docs after ingest**

Run:

```powershell
rg -n "layers/features|realtime|LEGACY_GIS_API_ENABLED|reviewer" Code_wiki/архитектура/api_and_realtime.md Code_wiki/архитектура/backend.md
```

Expected:

- docs mention `LEGACY_GIS_API_ENABLED`;
- docs no longer claim that `reviewer` can read legacy layers/features or subscribe to legacy layer realtime;
- reviewer access remains documented only for reviewer workflow boundaries that are not part of legacy GIS API.

---

## Final Verification Checklist

- [ ] `LEGACY_GIS_API_ENABLED` defaults to `False`.
- [ ] `require_legacy_gis_editor` returns `403 LEGACY_GIS_API_DISABLED` before role checks when flag is disabled.
- [ ] With flag enabled, `Editor` can reach legacy REST and ticket issue.
- [ ] With flag enabled, `Reviewer` receives `403 ROLE_NOT_ALLOWED` before legacy services are called.
- [ ] WebSocket handshake remains ticket-only and does not accept JWT query auth.
- [ ] `WebSocketTicketService` rejects `reviewer` on issue and consume.
- [ ] Focused backend pytest suite passes.
- [ ] Code_wiki is updated through `/ingest repository-change` when implementation creates durable technical knowledge.
