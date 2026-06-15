import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from core.passwords import hash_password
from domain.exceptions.auth_api_error import AuthApiError
from services.auth_service import AuthService


def test_authenticate_user_returns_user_for_valid_credentials() -> None:
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

    result = asyncio.run(service.authenticate_user("editor@example.com", "editor-password"))

    assert result is user
    repository.get_by_email.assert_awaited_once_with("editor@example.com")


def test_authenticate_user_raises_401_for_unknown_email() -> None:
    repository = AsyncMock()
    repository.get_by_email.return_value = None
    service = AuthService(session=None, user_repository=repository)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.authenticate_user("missing@example.com", "editor-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Неверная электронная почта или пароль"


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

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.authenticate_user("editor@example.com", "wrong-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Неверная электронная почта или пароль"


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

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.authenticate_user(
                "marina.reviewer@example.local",
                "marina-reviewer-password",
            )
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Неверная электронная почта или пароль"


def test_authenticate_user_rejects_inactive_user() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        password_hash=hash_password("marina-reviewer-password"),
        is_active=False,
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

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"
