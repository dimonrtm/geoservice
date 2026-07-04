from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import get_auth_service, get_auth_session_service
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.schemas.auth.issued_auth_session_out import (
    IssuedAuthSessionOut,
)
from utility_service.use_cases.schemas.auth.refreshed_auth_session_out import (
    RefreshedAuthSessionOut,
)
from utility_service.web_api.api import auth as auth_api
from utility_service.web_api.api.auth import auth_router
from utility_service.web_api.api.exception_handlers import install_exception_handlers


def build_auth_app(auth_service: object, auth_session_service: object | None = None) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(auth_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_auth_session_service] = lambda: auth_session_service or AsyncMock()
    return app


def build_auth_user(role: str = "editor") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        email=f"{role}@example.local",
        role=SimpleNamespace(value=role),
        is_active=True,
    )


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


def test_login_success_sets_session_cookie_and_returns_auth_success() -> None:
    user = build_auth_user()
    auth_service = AsyncMock()
    auth_service.authenticate_user.return_value = user
    auth_session_service = AsyncMock()
    auth_session_service.issue_session.return_value = IssuedAuthSessionOut(
        token="raw-session-token",
        expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    response = TestClient(build_auth_app(auth_service, auth_session_service)).post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "correct-password",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "user"}
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"] == {
        "id": str(user.id),
        "email": user.email,
        "role": "editor",
    }
    assert "refresh_token" not in body
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=raw-session-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Max-Age=43200" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    assert "SameSite=lax" in set_cookie
    auth_service.authenticate_user.assert_awaited_once_with(
        user.email,
        "correct-password",
    )
    auth_session_service.issue_session.assert_awaited_once_with(user)


def test_refresh_with_cookie_rotates_session_cookie_and_returns_auth_success() -> None:
    user = build_auth_user(role="reviewer")
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    auth_session_service.refresh_session.return_value = RefreshedAuthSessionOut(
        token="new-session-token",
        expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        user=user,
    )

    client = TestClient(build_auth_app(auth_service, auth_session_service))
    client.cookies.set("geoservice_session", "old-session-token")

    response = client.post("/api/v1/auth/session/refresh")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "user"}
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"] == {
        "id": str(user.id),
        "email": user.email,
        "role": "reviewer",
    }
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=new-session-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Max-Age=43200" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    assert "SameSite=lax" in set_cookie
    auth_session_service.refresh_session.assert_awaited_once_with("old-session-token")
    assert not auth_service.mock_calls


def test_refresh_without_cookie_returns_strict_structured_error() -> None:
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    auth_session_service.refresh_session.side_effect = AuthApiError(
        401,
        "AUTH_REQUIRED",
        "Сессия недействительна.",
    )

    response = TestClient(build_auth_app(auth_service, auth_session_service)).post(
        "/api/v1/auth/session/refresh",
        headers={"X-Correlation-ID": "refresh-correlation-id"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "AUTH_REQUIRED",
        "message": "Сессия недействительна.",
        "correlationId": "refresh-correlation-id",
    }
    assert "detail" not in response.json()
    assert "details" not in response.json()
    auth_session_service.refresh_session.assert_awaited_once_with(None)
    assert not auth_service.mock_calls


def test_logout_with_cookie_revokes_session_and_clears_cookie() -> None:
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()

    client = TestClient(build_auth_app(auth_service, auth_session_service))
    client.cookies.set("geoservice_session", "raw-session-token")

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    auth_session_service.revoke_session.assert_awaited_once_with("raw-session-token")
    assert not auth_service.mock_calls


def test_logout_without_cookie_is_ok_and_revokes_none() -> None:
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()

    response = TestClient(build_auth_app(auth_service, auth_session_service)).post(
        "/api/v1/auth/logout",
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    set_cookie = response.headers["set-cookie"]
    assert "geoservice_session=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    auth_session_service.revoke_session.assert_awaited_once_with(None)
    assert not auth_service.mock_calls


def test_secure_session_cookie_login_refresh_logout_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr(auth_api.settings, "auth_session_cookie_secure", True)
    user = build_auth_user()
    auth_service = AsyncMock()
    auth_service.authenticate_user.return_value = user
    auth_session_service = AsyncMock()
    auth_session_service.issue_session.return_value = IssuedAuthSessionOut(
        token="login-session-token",
        expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    auth_session_service.refresh_session.return_value = RefreshedAuthSessionOut(
        token="refreshed-session-token",
        expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        user=user,
    )
    client = TestClient(
        build_auth_app(auth_service, auth_session_service),
        base_url="https://testserver",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "correct-password",
        },
    )
    refresh_response = client.post("/api/v1/auth/session/refresh")
    logout_response = client.post("/api/v1/auth/logout")

    assert login_response.status_code == 200
    login_cookie = login_response.headers["set-cookie"]
    assert "geoservice_session=login-session-token" in login_cookie
    assert "Secure" in login_cookie
    assert "HttpOnly" in login_cookie
    assert "Max-Age=43200" in login_cookie
    assert "Path=/api/v1/auth" in login_cookie

    assert refresh_response.status_code == 200
    refresh_cookie = refresh_response.headers["set-cookie"]
    assert "geoservice_session=refreshed-session-token" in refresh_cookie
    assert "Secure" in refresh_cookie
    assert "HttpOnly" in refresh_cookie
    assert "Max-Age=43200" in refresh_cookie
    assert "Path=/api/v1/auth" in refresh_cookie

    assert logout_response.status_code == 200
    logout_cookie = logout_response.headers["set-cookie"]
    assert "geoservice_session=" in logout_cookie
    assert "Secure" in logout_cookie
    assert "HttpOnly" in logout_cookie
    assert "Max-Age=0" in logout_cookie
    assert "Path=/api/v1/auth" in logout_cookie
    auth_service.authenticate_user.assert_awaited_once_with(
        user.email,
        "correct-password",
    )
    auth_session_service.issue_session.assert_awaited_once_with(user)
    auth_session_service.refresh_session.assert_awaited_once_with("login-session-token")
    auth_session_service.revoke_session.assert_awaited_once_with("refreshed-session-token")


def test_dev_login_route_is_not_registered() -> None:
    auth_service = AsyncMock()

    response = TestClient(build_auth_app(auth_service)).post(
        "/api/v1/auth/dev-login",
        json={"email": "new@example.local", "role": "editor"},
    )

    assert response.status_code == 404
    assert not auth_service.mock_calls
