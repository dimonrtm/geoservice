import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from utility_service.utils.passwords import hash_password
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.services.auth_service import AuthService


class FakeReadSession:
    def __init__(self) -> None:
        self.begin_calls = 0
        self.in_transaction = False

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        self.in_transaction = True
        try:
            yield self
        finally:
            self.in_transaction = False


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


def test_get_user_by_id_closes_read_transaction_before_session_reuse() -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        password_hash=hash_password("editor-password"),
        is_active=True,
    )
    repository = AsyncMock()
    repository.get_by_id.return_value = user
    session = FakeReadSession()
    service = AuthService(session=session, user_repository=repository)

    result = asyncio.run(service.get_user_by_id(user.id))

    assert result is user
    assert session.begin_calls == 1
    assert session.in_transaction is False
    repository.get_by_id.assert_awaited_once_with(user.id)


def test_authenticate_user_raises_401_for_unknown_email() -> None:
    repository = AsyncMock()
    repository.get_by_email.return_value = None
    service = AuthService(session=None, user_repository=repository)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.authenticate_user("missing@example.com", "editor-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_CREDENTIALS"
    assert exc_info.value.message == "Неверная электронная почта или пароль"


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

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.authenticate_user("editor@example.com", "wrong-password"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_CREDENTIALS"
    assert exc_info.value.message == "Неверная электронная почта или пароль"


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

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(
            service.authenticate_user(
                "marina.reviewer@example.local",
                "marina-reviewer-password",
            )
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_CREDENTIALS"
    assert exc_info.value.message == "Неверная электронная почта или пароль"


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
