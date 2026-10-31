from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utility_service.use_cases.deps import (
    get_auth_service,
    get_auth_session_service,
    get_auth_session_access_service,
)
from utility_service.use_cases.dtos import AuthRole, AuthUserDTO
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
from utility_service.web_api.middleware.correlation_id import CorrelationIdMiddleware
from utility_service.web_api.tests.auth_user_factory import auth_user
from utility_service.use_cases.tests.test_auth_session_access_service import access_fixture, signed
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.tests.test_realtime_connection_manager import active_session


def build_auth_app(
    auth_service: object,
    auth_session_service: object | None = None,
    access_service=None,
) -> FastAPI:
    app = FastAPI()
    app.state.websocket_connection_manager = WebSocketConnectionManager(active_session)
    app.add_middleware(CorrelationIdMiddleware)
    install_exception_handlers(app)
    app.include_router(auth_router)
    app.dependency_overrides[get_auth_session_access_service] = (
        lambda: access_service or access_fixture()[0]
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_auth_session_service] = lambda: auth_session_service or AsyncMock()
    return app


def build_auth_user(role: AuthRole = "editor") -> AuthUserDTO:
    return auth_user(role)


def test_login_invalid_credentials_returns_strict_structured_error() -> None:
    auth_service = AsyncMock()
    auth_service.authenticate_user.side_effect = AuthApiError(
        401,
        "INVALID_CREDENTIALS",
        "Неверная электронная почта или пароль",
    )

    response = TestClient(build_auth_app(auth_service)).post(
        "/api/v1/auth/login",
        headers={
            "X-Correlation-ID": "login-correlation-id",
        },
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
        session_id=uuid4(),
        token="raw-session-token",
        expires_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

    response = TestClient(
        build_auth_app(
            auth_service,
            auth_session_service,
        )
    ).post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "correct-password",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "user", "session_id"}
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
    auth_session_service.issue_session.assert_awaited_once_with(
        user,
        previous_token=None,
    )


def test_refresh_with_cookie_rotates_session_cookie_and_returns_auth_success() -> None:
    user = build_auth_user(role="reviewer")
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    auth_session_service.refresh_session.return_value = RefreshedAuthSessionOut(
        session_id=uuid4(),
        token="new-session-token",
        expires_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        user=user,
    )

    client = TestClient(
        build_auth_app(
            auth_service,
            auth_session_service,
        )
    )
    client.cookies.set(
        "geoservice_session",
        "old-session-token",
    )

    response = client.post("/api/v1/auth/session/refresh")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "user", "session_id"}
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
    auth_session_service.refresh_session.assert_awaited_once_with(
        "old-session-token",
        expected_session_id=None,
    )
    assert not auth_service.mock_calls


def test_refresh_without_cookie_returns_strict_structured_error() -> None:
    auth_service = AsyncMock()
    auth_session_service = AsyncMock()
    auth_session_service.refresh_session.side_effect = AuthApiError(
        401,
        "AUTH_REQUIRED",
        "Сессия недействительна.",
    )

    response = TestClient(
        build_auth_app(
            auth_service,
            auth_session_service,
        )
    ).post(
        "/api/v1/auth/session/refresh",
        headers={
            "X-Correlation-ID": "refresh-correlation-id",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "AUTH_REQUIRED",
        "message": "Сессия недействительна.",
        "correlationId": "refresh-correlation-id",
    }
    assert "detail" not in response.json()
    assert "details" not in response.json()
    auth_session_service.refresh_session.assert_awaited_once_with(
        None,
        expected_session_id=None,
    )
    assert not auth_service.mock_calls


def test_refresh_forwards_expected_session_id_and_returns_signed_sid() -> None:
    from jose import jwt

    user = build_auth_user()
    session_id = uuid4()
    sessions = AsyncMock()
    sessions.refresh_session.return_value = RefreshedAuthSessionOut(
        session_id=session_id,
        token="new-cookie",
        expires_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        user=user,
    )
    client = TestClient(
        build_auth_app(
            AsyncMock(),
            sessions,
        )
    )
    client.cookies.set(
        "geoservice_session",
        "current-cookie",
    )
    response = client.post(
        "/api/v1/auth/session/refresh",
        headers={
            "X-Expected-Session-Id": str(session_id),
        },
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == str(session_id)
    claims = jwt.decode(
        response.json()["access_token"],
        auth_api.settings.jwt_secret,
        algorithms=[auth_api.settings.jwt_alg],
    )
    assert claims["sid"] == str(session_id)
    assert claims["sub"] == str(user.id)
    sessions.refresh_session.assert_awaited_once_with(
        "current-cookie",
        expected_session_id=session_id,
    )


def test_logout_has_no_set_cookie_and_cannot_revoke_other_sid() -> None:
    service, parent, user = access_fixture()
    client = TestClient(
        build_auth_app(
            AsyncMock(),
            access_service=service,
        )
    )
    client.cookies.set(
        "geoservice_session",
        "known",
    )
    denied = client.post(
        "/api/v1/auth/logout",
        json={
            "session_id": str(uuid4()),
        },
    )
    assert denied.status_code == 401
    assert parent.revoked_at is None
    for _ in range(2):
        response = client.post(
            "/api/v1/auth/logout",
            json={
                "session_id": str(parent.id),
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "ok": True,
            "session_id": str(parent.id),
        }
        assert "set-cookie" not in response.headers
    assert parent.revoked_at is not None


def test_logout_without_proof_is_rejected() -> None:
    service, parent, _ = access_fixture()
    response = TestClient(
        build_auth_app(
            AsyncMock(),
            access_service=service,
        )
    ).post(
        "/api/v1/auth/logout",
        json={
            "session_id": str(parent.id),
        },
    )
    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert parent.revoked_at is None


def test_status_expired_jwt_returns_only_state_without_cookie() -> None:
    service, parent, user = access_fixture()
    client = TestClient(
        build_auth_app(
            AsyncMock(),
            access_service=service,
        )
    )
    response = client.post(
        "/api/v1/auth/session/status",
        json={
            "session_id": str(parent.id),
        },
        headers={
            "Authorization": f"Bearer {signed(user, parent, expired=True,)}",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "session_id": str(parent.id),
        "state": "active",
    }
    assert "set-cookie" not in response.headers


def test_status_database_error_is_not_ended() -> None:
    service, parent, user = access_fixture()

    async def fail(*args, **kwargs):
        raise RuntimeError("База недоступна")

    service.browser_session_repository.get_session = fail
    response = TestClient(
        build_auth_app(
            AsyncMock(),
            access_service=service,
        ),
        raise_server_exceptions=False,
    ).post(
        "/api/v1/auth/session/status",
        json={
            "session_id": str(parent.id),
        },
        headers={
            "Authorization": f"Bearer {signed(user, parent,)}",
        },
    )
    assert response.status_code == 500
    assert "state" not in response.json()


def test_secure_session_cookie_login_refresh_logout_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_api.settings,
        "auth_session_cookie_secure",
        True,
    )
    user = build_auth_user()
    auth_service = AsyncMock()
    auth_service.authenticate_user.return_value = user
    auth_session_service = AsyncMock()
    auth_session_service.issue_session.return_value = IssuedAuthSessionOut(
        session_id=uuid4(),
        token="login-session-token",
        expires_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )
    auth_session_service.refresh_session.return_value = RefreshedAuthSessionOut(
        session_id=uuid4(),
        token="refreshed-session-token",
        expires_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        user=user,
    )
    access_service, parent, _ = access_fixture()
    client = TestClient(
        build_auth_app(
            auth_service,
            auth_session_service,
            access_service,
        ),
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
    logout_response = client.post(
        "/api/v1/auth/logout",
        json={
            "session_id": str(parent.id),
        },
        headers={
            "Authorization": f"Bearer {signed(_, parent,)}",
        },
    )

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
    assert "set-cookie" not in logout_response.headers
    auth_service.authenticate_user.assert_awaited_once_with(
        user.email,
        "correct-password",
    )
    auth_session_service.issue_session.assert_awaited_once_with(
        user,
        previous_token=None,
    )
    auth_session_service.refresh_session.assert_awaited_once_with(
        "login-session-token",
        expected_session_id=None,
    )
    assert parent.revoked_at is not None


def test_dev_login_route_is_not_registered() -> None:
    auth_service = AsyncMock()

    response = TestClient(build_auth_app(auth_service)).post(
        "/api/v1/auth/dev-login",
        json={
            "email": "new@example.local",
            "role": "editor",
        },
    )

    assert response.status_code == 404
    assert not auth_service.mock_calls
