from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import (
    get_auth_service,
    get_edit_version_service,
    get_work_order_service,
    get_workspace_service,
)
from utility_service.use_cases.dtos import AuthRole
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.schemas.work_order import AssignedWorkOrdersOut, WorkOrderSummaryOut
from utility_service.use_cases.schemas.workspace import (
    WorkspaceAoiOut,
    WorkspaceEditVersionOut,
    WorkspaceFeatureCollectionOut,
    WorkspaceOut,
    WorkspaceScopeOut,
    WorkspaceWorkOrderOut,
)
from utility_service.use_cases.services.edit_version_service import OpenEditVersionResult
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.work_orders import work_orders_router
from utility_service.web_api.tests.auth_user_factory import auth_user


def build_app(
    auth_service: object,
    edit_version_service: object,
    workspace_service: object | None = None,
    work_order_service: object | None = None,
) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(work_orders_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_edit_version_service] = lambda: edit_version_service
    if workspace_service is not None:
        app.dependency_overrides[get_workspace_service] = lambda: workspace_service
    if work_order_service is not None:
        app.dependency_overrides[get_work_order_service] = lambda: work_order_service
    return app


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


def edit_version(work_order_id, owner_user_id):
    now = datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        work_order_id=work_order_id,
        owner_user_id=owner_user_id,
        status="open",
        base_network_revision=12,
        created_at=now,
        last_opened_at=now,
    )


def work_order_summary(
    *,
    code: str = "WO-001",
    status: str = "assigned",
):
    return SimpleNamespace(
        id=uuid4(),
        code=code,
        title=f"Наряд {code}",
        description=f"Описание {code}",
        status=SimpleNamespace(value=status),
    )


def workspace_response(work_order_id, edit_version_id) -> WorkspaceOut:
    return WorkspaceOut(
        work_order=WorkspaceWorkOrderOut(
            id=work_order_id,
            code="WO-001",
            title="Проверка участка фидера",
            description=None,
            status="in_progress",
            scope=WorkspaceScopeOut(
                aoi=WorkspaceAoiOut(
                    id=uuid4(),
                    name="Рабочая область WO-001",
                    description=None,
                    geometry={"type": "Polygon", "coordinates": []},
                    extent=[65.495, 44.795, 65.545, 44.835],
                )
            ),
            edit_version=WorkspaceEditVersionOut(
                id=edit_version_id,
                status="open",
                base_network_revision=12,
                features=WorkspaceFeatureCollectionOut(features=[]),
                associations=[],
            ),
        )
    )


def test_open_edit_version_returns_201_when_created() -> None:
    work_order_id = uuid4()
    auth_service, token, user_id = auth_context("editor")
    version = edit_version(work_order_id, user_id)
    edit_version_service = AsyncMock()
    edit_version_service.open_for_work_order.return_value = OpenEditVersionResult(
        created=True,
        edit_version=version,
    )

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["created"] is True
    assert response.json()["editVersion"]["id"] == str(version.id)
    assert response.json()["editVersion"]["workOrderId"] == str(work_order_id)
    assert response.json()["editVersion"]["ownerId"] == str(user_id)
    assert response.json()["editVersion"]["status"] == "open"
    assert response.json()["editVersion"]["baseNetworkRevision"] == 12
    edit_version_service.open_for_work_order.assert_awaited_once_with(work_order_id, user_id)


def test_list_assigned_to_me_returns_compact_work_orders_without_audit_fields() -> None:
    auth_service, token, user_id = auth_context("editor")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()
    assigned = work_order_summary(code="WO-002", status="in_progress")
    work_order_service.list_assigned_to_editor.return_value = AssignedWorkOrdersOut(
        work_orders=[
            WorkOrderSummaryOut(
                id=assigned.id,
                code=assigned.code,
                title=assigned.title,
                description=assigned.description,
                status=assigned.status.value,
            )
        ]
    )

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "workOrders": [
            {
                "id": str(assigned.id),
                "code": "WO-002",
                "title": "Наряд WO-002",
                "description": "Описание WO-002",
                "status": "in_progress",
            }
        ]
    }
    assert "updatedAt" not in payload["workOrders"][0]
    assert "createdAt" not in payload["workOrders"][0]
    work_order_service.list_assigned_to_editor.assert_awaited_once_with(user_id)


def test_list_assigned_to_me_returns_empty_list() -> None:
    auth_service, token, user_id = auth_context("editor")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()
    work_order_service.list_assigned_to_editor.return_value = AssignedWorkOrdersOut(work_orders=[])

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"workOrders": []}
    work_order_service.list_assigned_to_editor.assert_awaited_once_with(user_id)


def test_reviewer_is_denied_before_assigned_work_orders_service_call() -> None:
    auth_service, token, _ = auth_context("reviewer")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    work_order_service.list_assigned_to_editor.assert_not_awaited()


def test_list_assigned_to_me_preserves_service_order() -> None:
    auth_service, token, _ = auth_context("editor")
    edit_version_service = AsyncMock()
    work_order_service = AsyncMock()
    first = work_order_summary(code="WO-002", status="in_progress")
    second = work_order_summary(code="WO-001", status="assigned")
    work_order_service.list_assigned_to_editor.return_value = AssignedWorkOrdersOut(
        work_orders=[
            WorkOrderSummaryOut(
                id=first.id,
                code=first.code,
                title=first.title,
                description=first.description,
                status=first.status.value,
            ),
            WorkOrderSummaryOut(
                id=second.id,
                code=second.code,
                title=second.title,
                description=second.description,
                status=second.status.value,
            ),
        ]
    )

    response = TestClient(
        build_app(
            auth_service,
            edit_version_service,
            work_order_service=work_order_service,
        )
    ).get(
        "/api/v1/work-orders/assigned-to-me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert [item["code"] for item in response.json()["workOrders"]] == [
        "WO-002",
        "WO-001",
    ]


def test_open_edit_version_returns_200_when_reopened() -> None:
    work_order_id = uuid4()
    auth_service, token, user_id = auth_context("editor")
    version = edit_version(work_order_id, user_id)
    edit_version_service = AsyncMock()
    edit_version_service.open_for_work_order.return_value = OpenEditVersionResult(
        created=False,
        edit_version=version,
    )

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["created"] is False
    assert response.json()["editVersion"]["id"] == str(version.id)


def test_reviewer_is_denied_before_edit_version_service_call() -> None:
    work_order_id = uuid4()
    auth_service, token, _ = auth_context("reviewer")
    edit_version_service = AsyncMock()

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    edit_version_service.open_for_work_order.assert_not_awaited()


def test_service_error_becomes_structured_response() -> None:
    work_order_id = uuid4()
    auth_service, token, _ = auth_context("editor")
    edit_version_service = AsyncMock()
    edit_version_service.open_for_work_order.side_effect = WorkOrderApiError(
        422,
        "WORK_ORDER_CONTEXT_INVALID",
        "Контекст рабочей задачи поврежден или неполон.",
    )

    response = TestClient(build_app(auth_service, edit_version_service)).post(
        f"/api/v1/work-orders/{work_order_id}/edit-versions",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": "workflow-correlation-id",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "WORK_ORDER_CONTEXT_INVALID",
        "message": "Контекст рабочей задачи поврежден или неполон.",
        "correlationId": "workflow-correlation-id",
    }


def test_get_workspace_returns_nested_work_order_payload() -> None:
    work_order_id = uuid4()
    edit_version_id = uuid4()
    auth_service, token, user_id = auth_context("editor")
    edit_version_service = AsyncMock()
    workspace_service = AsyncMock()
    workspace_service.get_workspace.return_value = workspace_response(
        work_order_id,
        edit_version_id,
    )

    response = TestClient(build_app(auth_service, edit_version_service, workspace_service)).get(
        f"/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workOrder"]["id"] == str(work_order_id)
    assert payload["workOrder"]["scope"]["aoi"]["name"] == "Рабочая область WO-001"
    assert payload["workOrder"]["editVersion"]["id"] == str(edit_version_id)
    workspace_service.get_workspace.assert_awaited_once_with(
        work_order_id=work_order_id,
        edit_version_id=edit_version_id,
        actor_id=user_id,
    )


def test_workspace_service_404_is_structured() -> None:
    work_order_id = uuid4()
    edit_version_id = uuid4()
    auth_service, token, _ = auth_context("editor")
    edit_version_service = AsyncMock()
    workspace_service = AsyncMock()
    workspace_service.get_workspace.side_effect = WorkOrderApiError(
        404,
        "EDIT_VERSION_NOT_FOUND",
        "Рабочая версия не найдена.",
    )

    response = TestClient(build_app(auth_service, edit_version_service, workspace_service)).get(
        f"/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": "workspace-correlation-id",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "EDIT_VERSION_NOT_FOUND",
        "message": "Рабочая версия не найдена.",
        "correlationId": "workspace-correlation-id",
    }
