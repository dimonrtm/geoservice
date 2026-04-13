import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.auth_service import AuthService
from services.password_service import hash_password


def test_authenticate_user_returns_user_for_valid_credentials() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        password_hash=hash_password("editor-password"),
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
        email="viewer@example.com",
        role=SimpleNamespace(value="viewer"),
        password_hash=None,
    )
    repository = AsyncMock()
    repository.get_by_email.return_value = user
    service = AuthService(session=None, user_repository=repository)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.authenticate_user("viewer@example.com", "viewer-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Неверная электронная почта или пароль"
