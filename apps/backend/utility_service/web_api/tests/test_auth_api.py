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


def test_dev_login_route_is_not_registered() -> None:
    auth_service = AsyncMock()

    response = TestClient(build_auth_app(auth_service)).post(
        "/api/v1/auth/dev-login",
        json={"email": "new@example.local", "role": "editor"},
    )

    assert response.status_code == 404
    assert not auth_service.mock_calls
