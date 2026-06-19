from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import get_auth_service, get_edit_version_service
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.services.edit_version_service import OpenEditVersionResult
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.work_orders import work_orders_router


def build_app(auth_service: object, edit_version_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(work_orders_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_edit_version_service] = lambda: edit_version_service
    return app


def auth_context(role: str, *, is_active: bool = True):
    user_id = uuid4()
    token = create_access_token(str(user_id), role)
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email=f"{role}@example.local",
        role=SimpleNamespace(value=role),
        is_active=is_active,
    )
    return auth_service, token, user_id


def edit_version(work_order_id, owner_id):
    now = datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        work_order_id=work_order_id,
        owner_id=owner_id,
        status="open",
        base_revision=12,
        created_at=now,
        last_opened_at=now,
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
    assert response.json()["editVersion"]["baseRevision"] == 12
    edit_version_service.open_for_work_order.assert_awaited_once_with(work_order_id, user_id)


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
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "WORK_ORDER_CONTEXT_INVALID"
