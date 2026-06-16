import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import WebSocketException
from jose import jwt

from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.websocket_auth import authenticate_websocket_token
from utility_service.utils.settings import settings


def test_authenticate_websocket_token_returns_user_context_for_valid_token() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="editor@example.com",
        role=SimpleNamespace(value="editor"),
        is_active=True,
    )

    result = asyncio.run(authenticate_websocket_token(token, auth_service))

    assert result.user_id == user_id
    assert result.email == "editor@example.com"
    assert result.role == "editor"


def test_authenticate_websocket_token_rejects_invalid_token() -> None:
    auth_service = AsyncMock()

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token("broken-token", auth_service))

    assert exc_info.value.code == 1008


def test_authenticate_websocket_token_rejects_payload_without_role() -> None:
    user_id = uuid4()
    token = jwt.encode({"sub": str(user_id)}, settings.jwt_secret, algorithm=settings.jwt_alg)
    auth_service = AsyncMock()

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token(token, auth_service))

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Некорректное содержимое токена"


def test_authenticate_websocket_token_rejects_missing_user() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = None

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token(token, auth_service))

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Токен недействителен или срок его действия истёк"


def test_authenticate_websocket_token_rejects_inactive_user() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "reviewer")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        is_active=False,
    )

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token(token, auth_service))

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Учетная запись отключена."


def test_authenticate_websocket_token_rejects_legacy_viewer_role() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "viewer")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="marina.reviewer@example.local",
        role=SimpleNamespace(value="reviewer"),
        is_active=True,
    )

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token(token, auth_service))

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Некорректное содержимое токена"
