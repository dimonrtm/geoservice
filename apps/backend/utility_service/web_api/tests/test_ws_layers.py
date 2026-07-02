from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from utility_service.web_api.api.auth import create_access_token
from utility_service.use_cases.deps import (
    get_auth_service,
    get_layer_service,
    get_websocket_ticket_service,
)
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.websocket_ticket_error import WebSocketTicketError
from utility_service.use_cases.schemas.realtime import WebSocketTicketOut
from utility_service.web_api.api.ws_layers import ws_layers_router
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
    WebSocketUserContext,
)


def create_test_app(
    auth_service: object,
    layer_service: object,
    connection_manager: WebSocketConnectionManager | None = None,
    ticket_service: object | None = None,
) -> FastAPI:
    app = FastAPI()
    app.state.websocket_connection_manager = connection_manager or WebSocketConnectionManager()
    install_exception_handlers(app)
    app.include_router(ws_layers_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_layer_service] = lambda: layer_service
    if ticket_service is not None:
        app.dependency_overrides[get_websocket_ticket_service] = lambda: ticket_service
    return app


class FakeWebSocketTicketService:
    def __init__(self, ticket: str = "ticket-1", error: Exception | None = None):
        self.ticket = ticket
        self.error = error
        self.issued = []
        self.consumed = []
        self.user_context = WebSocketUserContext(
            user_id=uuid4(),
            email="editor@example.local",
            role="editor",
        )

    async def issue_ticket(self, user, layer_id):
        self.issued.append((user, layer_id))
        if self.error is not None:
            raise self.error
        return WebSocketTicketOut(
            ticket=self.ticket,
            expires_at=datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc),
        )

    async def consume_ticket(self, ticket, layer_id):
        self.consumed.append((ticket, layer_id))
        if self.error is not None:
            raise self.error
        return self.user_context


@pytest.mark.parametrize("role", ["editor", "reviewer"])
def test_ws_layer_ticket_issue_accepts_authenticated_realtime_roles(role: str) -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), role)
    user = SimpleNamespace(
        id=user_id,
        email=f"{role}@example.com",
        role=SimpleNamespace(value=role),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    ticket_service = FakeWebSocketTicketService(ticket=f"{role}-ticket")
    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "ticket": f"{role}-ticket",
        "expiresAt": "2026-07-02T10:00:00Z",
    }
    assert ticket_service.issued == [(user, layer_id)]


def test_ws_layer_ticket_issue_rejects_missing_auth() -> None:
    layer_id = uuid4()

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=FakeWebSocketTicketService(),
    )

    with TestClient(app) as client:
        response = client.post(f"/api/v1/ws/layers/{layer_id}/ticket")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_ws_layer_ticket_issue_returns_structured_layer_not_found() -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    user = SimpleNamespace(
        id=user_id,
        email="editor@example.local",
        role=SimpleNamespace(value="editor"),
        is_active=True,
    )

    async def get_user_by_id(_user_id):
        return user

    async def get_layer_by_id(_layer_id):
        return None

    ticket_service = FakeWebSocketTicketService(
        error=AuthApiError(404, "LAYER_NOT_FOUND", "Слой не найден.")
    )
    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/ws/layers/{layer_id}/ticket",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    assert response.json()["code"] == "LAYER_NOT_FOUND"


@pytest.mark.parametrize("role", ["editor", "reviewer"])
def test_ws_layer_subscription_accepts_authorized_users(role: str) -> None:
    layer_id = uuid4()
    ticket = f"{role}-ticket"
    ticket_service = FakeWebSocketTicketService(ticket=ticket)
    ticket_service.user_context = WebSocketUserContext(
        user_id=uuid4(),
        email=f"{role}@example.com",
        role=role,
    )

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    auth_service = SimpleNamespace(get_user_by_id=get_user_by_id)
    layer_service = SimpleNamespace(get_layer_by_id=get_layer_by_id)
    connection_manager = WebSocketConnectionManager()
    app = create_test_app(auth_service, layer_service, connection_manager, ticket_service)

    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?ticket={ticket}") as websocket:
            assert websocket.receive_json() == {"type": "connected", "layerId": str(layer_id)}
            assert connection_manager.get_connection_count(layer_id) == 1

    assert ticket_service.consumed == [(ticket, layer_id)]
    assert connection_manager.get_connection_count(layer_id) == 0


def test_ws_layer_subscription_rejects_missing_ticket() -> None:
    layer_id = uuid4()
    ticket_service = FakeWebSocketTicketService()

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}"):
                pass

    assert ticket_service.consumed == []
    assert exc_info.value.code == 1008


def test_ws_layer_subscription_rejects_legacy_jwt_query_token() -> None:
    layer_id = uuid4()
    user_id = uuid4()
    token = create_access_token(str(user_id), "editor")
    ticket_service = FakeWebSocketTicketService()

    async def get_user_by_id(_user_id):
        return SimpleNamespace(
            id=user_id,
            email="editor@example.local",
            role=SimpleNamespace(value="editor"),
            is_active=True,
        )

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?token={token}"):
                pass

    assert ticket_service.consumed == []
    assert exc_info.value.code == 1008


def test_ws_layer_subscription_rejects_invalid_or_reused_ticket() -> None:
    layer_id = uuid4()
    ticket_service = FakeWebSocketTicketService(
        error=WebSocketTicketError("ticket already consumed")
    )

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return SimpleNamespace(id=layer_id)

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?ticket=reused-ticket"):
                pass

    assert ticket_service.consumed == [("reused-ticket", layer_id)]
    assert exc_info.value.code == 1008


def test_ws_layer_subscription_rejects_unknown_layer_after_ticket_consume() -> None:
    layer_id = uuid4()
    ticket_service = FakeWebSocketTicketService(ticket="valid-ticket")

    async def get_user_by_id(_user_id):
        return None

    async def get_layer_by_id(_layer_id):
        return None

    app = create_test_app(
        SimpleNamespace(get_user_by_id=get_user_by_id),
        SimpleNamespace(get_layer_by_id=get_layer_by_id),
        ticket_service=ticket_service,
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/ws/layers/{layer_id}?ticket=valid-ticket"):
                pass

    assert ticket_service.consumed == [("valid-ticket", layer_id)]
    assert exc_info.value.code == 1008
