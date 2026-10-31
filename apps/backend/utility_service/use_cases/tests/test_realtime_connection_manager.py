import asyncio
from uuid import uuid4

import pytest
from fastapi import WebSocketException

from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
    WebSocketUserContext,
)


class DummyWebSocket:
    def __init__(self, fail_on_send: bool = False) -> None:
        self.accepted = False
        self.sent_json: list[dict[str, object]] = []
        self.fail_on_send = fail_on_send
        self.closed = False

    async def close(self, code=1000, reason=None):
        self.closed = True

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict[str, object]) -> None:
        if self.fail_on_send:
            raise RuntimeError("connection lost")
        self.sent_json.append(payload)


def build_user_context() -> WebSocketUserContext:
    return WebSocketUserContext(
        session_id=uuid4(),
        user_id=uuid4(),
        email="marina.reviewer@example.local",
        role="reviewer",
    )


async def active_session(session_id):
    return True


def test_logout_between_consume_and_connect_is_rechecked():
    async def scenario():
        async def revoked(session_id):
            return False

        manager = WebSocketConnectionManager(revoked)
        socket = DummyWebSocket()
        with pytest.raises(WebSocketException) as error:
            await manager.connect(uuid4(), socket, build_user_context())
        assert error.value.code == 1008
        assert not socket.accepted

    asyncio.run(scenario())


def test_disconnect_session_preserves_other_browser():
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        layer = uuid4()
        first, other = DummyWebSocket(), DummyWebSocket()
        context = build_user_context()
        other_context = WebSocketUserContext(
            user_id=context.user_id, email=context.email, role=context.role, session_id=uuid4()
        )
        await manager.connect(layer, first, context)
        await manager.connect(layer, other, other_context)
        await manager.disconnect_session(context.session_id)
        assert first.closed
        assert not other.closed
        assert manager.get_connection_count(layer) == 1
        await manager.broadcast_to_layer(layer, {"type": "event"})
        assert first.sent_json == []
        assert other.sent_json == [{"type": "event"}]

    asyncio.run(scenario())


@pytest.mark.parametrize("read_error", [False, True])
def test_revoked_session_receives_no_new_admitted_event(read_error):
    async def scenario():
        active = True

        async def check(session_id):
            if not active and read_error:
                raise RuntimeError("База недоступна")
            return active

        manager = WebSocketConnectionManager(check)
        layer, socket = uuid4(), DummyWebSocket()
        await manager.connect(layer, socket, build_user_context())
        await manager.broadcast_to_layer(layer, {"type": "before"})
        active = False
        await manager.broadcast_to_layer(layer, {"type": "after"})
        assert socket.sent_json == [{"type": "before"}]
        assert manager.get_connection_count(layer) == 0
        assert socket.closed

    asyncio.run(scenario())


def test_disconnect_session_is_bounded_and_removes_before_close():
    async def scenario():
        class HangingSocket(DummyWebSocket):
            async def close(self, code=1000, reason=None):
                await asyncio.Event().wait()

        manager = WebSocketConnectionManager(active_session, close_timeout_seconds=0.01)
        layer, context = uuid4(), build_user_context()
        await manager.connect(layer, HangingSocket(), context)
        await asyncio.wait_for(manager.disconnect_session(context.session_id), 0.2)
        assert manager.get_connection_count(layer) == 0

    asyncio.run(scenario())


def test_connect_registers_connection_for_layer() -> None:
    manager = WebSocketConnectionManager(active_session)
    layer_id = uuid4()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(layer_id, websocket, build_user_context()))

    assert websocket.accepted is True
    assert manager.get_connection_count(layer_id) == 1


def test_disconnect_removes_connection_for_layer() -> None:
    manager = WebSocketConnectionManager(active_session)
    layer_id = uuid4()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(layer_id, websocket, build_user_context()))
    asyncio.run(manager.disconnect(layer_id, websocket))

    assert manager.get_connection_count(layer_id) == 0


def test_disconnect_is_idempotent() -> None:
    manager = WebSocketConnectionManager(active_session)
    layer_id = uuid4()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(layer_id, websocket, build_user_context()))
    asyncio.run(manager.disconnect(layer_id, websocket))
    asyncio.run(manager.disconnect(layer_id, websocket))

    assert manager.get_connection_count(layer_id) == 0


def test_broadcast_targets_only_requested_layer() -> None:
    manager = WebSocketConnectionManager(active_session)
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
    manager = WebSocketConnectionManager(active_session)
    layer_id = uuid4()
    stale_websocket = DummyWebSocket(fail_on_send=True)

    asyncio.run(manager.connect(layer_id, stale_websocket, build_user_context()))
    asyncio.run(manager.broadcast_to_layer(layer_id, {"type": "connected"}))

    assert manager.get_connection_count(layer_id) == 0
