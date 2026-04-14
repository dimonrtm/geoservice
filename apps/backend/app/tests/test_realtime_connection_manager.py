import asyncio
from uuid import uuid4

from services.realtime_connection_manager import WebSocketConnectionManager, WebSocketUserContext


class DummyWebSocket:
    def __init__(self, fail_on_send: bool = False) -> None:
        self.accepted = False
        self.sent_json: list[dict[str, object]] = []
        self.fail_on_send = fail_on_send

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict[str, object]) -> None:
        if self.fail_on_send:
            raise RuntimeError("connection lost")
        self.sent_json.append(payload)


def build_user_context() -> WebSocketUserContext:
    return WebSocketUserContext(
        user_id=uuid4(),
        email="viewer@example.com",
        role="viewer",
    )


def test_connect_registers_connection_for_layer() -> None:
    manager = WebSocketConnectionManager()
    layer_id = uuid4()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(layer_id, websocket, build_user_context()))

    assert websocket.accepted is True
    assert manager.get_connection_count(layer_id) == 1


def test_disconnect_removes_connection_for_layer() -> None:
    manager = WebSocketConnectionManager()
    layer_id = uuid4()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(layer_id, websocket, build_user_context()))
    asyncio.run(manager.disconnect(layer_id, websocket))

    assert manager.get_connection_count(layer_id) == 0


def test_disconnect_is_idempotent() -> None:
    manager = WebSocketConnectionManager()
    layer_id = uuid4()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(layer_id, websocket, build_user_context()))
    asyncio.run(manager.disconnect(layer_id, websocket))
    asyncio.run(manager.disconnect(layer_id, websocket))

    assert manager.get_connection_count(layer_id) == 0


def test_broadcast_targets_only_requested_layer() -> None:
    manager = WebSocketConnectionManager()
    first_layer_id = uuid4()
    second_layer_id = uuid4()
    first_websocket = DummyWebSocket()
    second_websocket = DummyWebSocket()
    event = {"type": "connected"}

    asyncio.run(manager.connect(first_layer_id, first_websocket, build_user_context()))
    asyncio.run(manager.connect(second_layer_id, second_websocket, build_user_context()))
    asyncio.run(manager.broadcast_to_layer(first_layer_id, event))

    assert first_websocket.sent_json == [event]
    assert second_websocket.sent_json == []


def test_broadcast_removes_stale_connections() -> None:
    manager = WebSocketConnectionManager()
    layer_id = uuid4()
    stale_websocket = DummyWebSocket(fail_on_send=True)

    asyncio.run(manager.connect(layer_id, stale_websocket, build_user_context()))
    asyncio.run(manager.broadcast_to_layer(layer_id, {"type": "connected"}))

    assert manager.get_connection_count(layer_id) == 0
