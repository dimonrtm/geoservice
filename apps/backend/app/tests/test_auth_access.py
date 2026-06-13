import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from api import auth as auth_api
from api.auth import create_access_token, get_current_user
from api.deps import get_auth_service
from api.exception_handlers import install_exception_handlers
from api.secure_router import secure_router
from domain.exceptions.auth_api_error import AuthApiError
from models.user import UserRole


def credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_uses_current_database_role() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    current_user = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        is_active=True,
    )
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = current_user

    result = asyncio.run(get_current_user(credentials(token), auth_service))

    assert result is current_user


def test_get_current_user_rejects_legacy_viewer_token() -> None:
    token = create_access_token(str(uuid4()), "viewer")

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(get_current_user(credentials(token), AsyncMock()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "AUTH_REQUIRED"


def test_get_current_user_rejects_inactive_user() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        role=SimpleNamespace(value="editor"),
        is_active=False,
    )

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(get_current_user(credentials(token), auth_service))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"


def test_role_guards_are_mutually_exclusive() -> None:
    editor = SimpleNamespace(role=UserRole.EDITOR)
    reviewer = SimpleNamespace(role=UserRole.REVIEWER)

    assert auth_api.require_editor(editor) is editor
    assert auth_api.require_reviewer(reviewer) is reviewer

    with pytest.raises(AuthApiError):
        auth_api.require_editor(reviewer)
    with pytest.raises(AuthApiError):
        auth_api.require_reviewer(editor)


def build_secure_app(auth_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(secure_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    return app


def test_secure_ping_uses_database_user_model() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="alexey.editor@example.local",
        role=UserRole.EDITOR,
        is_active=True,
    )

    response = TestClient(build_secure_app(auth_service)).get(
        "/api/v1/secure/ping",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "user_id": str(user_id),
        "role": "editor",
    }


def test_reviewer_gets_structured_403_from_editor_endpoint() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "reviewer")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=UserRole.REVIEWER,
        is_active=True,
    )

    response = TestClient(build_secure_app(auth_service)).post(
        "/api/v1/secure/ping",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ROLE_NOT_ALLOWED"
    assert response.json()["message"] == ("Операция доступна только пользователю с ролью Editor.")
