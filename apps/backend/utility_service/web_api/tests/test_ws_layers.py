from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from utility_service.web_api.api.auth import create_access_token
from utility_service.use_cases.deps import get_auth_service, get_layer_service
from utility_service.web_api.api.ws_layers import ws_layers_router
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)


def create_test_app(
    auth_service: object,
    layer_service: object,
    connection_manager: WebSocketConnectionManager | None = None,
) -> FastAPI:
    app = FastAPI()
    app.state.websocket_connection_manager = connection_manager or WebSocketConnectionManager()
    app.include_router(ws_layers_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_layer_service] = lambda: layer_service
    return app


@pytest.mark.parametrize("role", ["editor", "reviewer"])
def test_ws_layer_subscription_accepts_authorized_users(role: str) -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), role)

    async def get_user_by_id(_user_id):
        return SimpleNamespace(
            id=user_id,
            email=f"{role}@example.com",
            role=SimpleNamespace(value=role),
            is_active=True,
        )

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    auth_service = SimpleNamespace(get_user_by_id=get_user_by_id)
    layer_service = SimpleNamespace(get_layer_by_id=get_layer_by_id)
    connection_manager = WebSocketConnectionManager()
    app = create_test_app(auth_service, layer_service, connection_manager)

    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?token={token}") as websocket:
            assert websocket.receive_json() == {"type": "connected", "layerId": str(layer_id)}
            assert connection_manager.get_connection_count(layer_id) == 1

    assert connection_manager.get_connection_count(layer_id) == 0


def test_ws_layer_subscription_rejects_missing_token() -> None:
    layer_id = uuid4()

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}"):
                pass

    assert exc_info.value.code == 1008


def test_ws_layer_subscription_rejects_invalid_token() -> None:
    layer_id = uuid4()

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?token=broken-token"):
                pass

    assert exc_info.value.code == 1008


def test_ws_layer_subscription_rejects_unknown_layer() -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "reviewer")

    async def get_user_by_id(_user_id):
        return SimpleNamespace(
            id=user_id,
            email="marina.reviewer@example.local",
            role=SimpleNamespace(value="reviewer"),
            is_active=True,
        )

    async def get_layer_by_id(_layer_id):
        return None

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?token={token}"):
                pass

    assert exc_info.value.code == 1008
