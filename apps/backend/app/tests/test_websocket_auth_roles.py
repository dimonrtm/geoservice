import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import WebSocketException

from api.auth import create_access_token
from api.websocket_auth import authenticate_websocket_token


def test_authenticate_websocket_token_rejects_unsupported_token_role() -> None:
    user_id = uuid4()
    token = create_access_token(str(user_id), "admin")
    auth_service = AsyncMock()
    auth_service.get_user_by_id.return_value = SimpleNamespace(
        id=user_id,
        email="admin@example.com",
        role=SimpleNamespace(value="admin"),
        is_active=True,
    )

    with pytest.raises(WebSocketException) as exc_info:
        asyncio.run(authenticate_websocket_token(token, auth_service))

    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Некорректное содержимое токена"
    auth_service.get_user_by_id.assert_not_awaited()
