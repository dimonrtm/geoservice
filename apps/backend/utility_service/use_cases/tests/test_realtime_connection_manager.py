import asyncio
import json
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
        self.received = asyncio.Queue()
        self.close_event = asyncio.Event()
        self.close_code = None

    async def close(self, code=1000, reason=None):
        self.closed = True
        self.close_code = code
        self.close_event.set()

    async def next_event(self):
        return await asyncio.wait_for(self.received.get(), 2)

    async def send_text(self, text):
        await self.send_json(json.loads(text))

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict[str, object]) -> None:
        if self.fail_on_send:
            raise RuntimeError("connection lost")
        self.sent_json.append(payload)
        self.received.put_nowait(payload)


def build_user_context() -> WebSocketUserContext:
    return WebSocketUserContext(
        session_id=uuid4(),
        user_id=uuid4(),
        email="marina.reviewer@example.local",
        role="reviewer",
    )


async def active_session(session_id):
    return True


def test_slow_socket_does_not_block_fast_subscriber_or_publisher():
    async def scenario():
        slow_entered, release, fast_received = (
            asyncio.Event(),
            asyncio.Event(),
            asyncio.Event(),
        )

        class Subscriber(DummyWebSocket):
            async def send_text(self, text):
                await self.send_json(json.loads(text))

            async def send_json(self, payload):
                if payload["type"] == "update":
                    if self is slow:
                        slow_entered.set()
                        await release.wait()
                    else:
                        fast_received.set()

        slow, fast = Subscriber(), Subscriber()
        manager, layer = WebSocketConnectionManager(active_session), uuid4()
        for subscriber in [slow, fast]:
            await manager.connect(layer, subscriber, build_user_context())
        publication = asyncio.create_task(
            manager.broadcast_to_layer(layer, {"type": "update"})
        )
        try:
            await asyncio.wait_for(slow_entered.wait(), 1)
            await asyncio.wait_for(fast_received.wait(), 1)
            assert publication.done()
        finally:
            release.set()
            await publication
            for subscriber in [slow, fast]:
                await manager.disconnect(layer, subscriber)

    asyncio.run(scenario())


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
            user_id=context.user_id,
            email=context.email,
            role=context.role,
            session_id=uuid4(),
        )
        await manager.connect(layer, first, context)
        await manager.connect(layer, other, other_context)
        await manager.disconnect_session(context.session_id)
        assert first.closed
        assert not other.closed
        assert manager.get_connection_count(layer) == 1
        await manager.broadcast_to_layer(layer, {"type": "event"})
        assert not any(item["type"] == "event" for item in first.sent_json)
        assert (await other.next_event())["type"] == "connected"
        assert await other.next_event() == {"type": "event"}

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
        assert (await socket.next_event())["type"] == "connected"
        assert await socket.next_event() == {"type": "before"}
        active = False
        await manager.broadcast_to_layer(layer, {"type": "after"})
        await asyncio.wait_for(socket.close_event.wait(), 2)
        assert len(socket.sent_json) == 2
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


def test_broadcast_targets_only_requested_layer():
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        layer, other_layer = uuid4(), uuid4()
        first, other = DummyWebSocket(), DummyWebSocket()
        await manager.connect(layer, first, build_user_context())
        await manager.connect(other_layer, other, build_user_context())
        await manager.broadcast_to_layer(layer, {"type": "update"})
        assert (await first.next_event())["type"] == "connected"
        assert (await first.next_event())["type"] == "update"
        assert (await other.next_event())["type"] == "connected"
        await manager.shutdown()
        assert other.received.empty()

    asyncio.run(scenario())


def test_broadcast_removes_stale_connections():
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        layer, socket = uuid4(), DummyWebSocket(fail_on_send=True)
        await manager.connect(layer, socket, build_user_context())
        await asyncio.wait_for(socket.close_event.wait(), 2)
        assert manager.get_connection_count(layer) == 0

    asyncio.run(scenario())


def test_utf8_byte_budget_allows_exact_size_and_closes_on_one_extra_byte():
    async def scenario():
        event = {"type": "изменение", "name": "ж" * 50}
        size = len(
            json.dumps(event, separators=(",", ":"), ensure_ascii=False).encode()
        )
        manager = WebSocketConnectionManager(active_session, max_pending_bytes=size)
        layer, socket = uuid4(), DummyWebSocket()
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        await manager.broadcast_to_layer(layer, event)
        assert await socket.next_event() == event
        await manager.broadcast_to_layer(layer, {**event, "name": event["name"] + "x"})
        await asyncio.wait_for(socket.close_event.wait(), 2)
        assert socket.close_code == 1013
        await manager.shutdown()

    asyncio.run(scenario())


@pytest.mark.parametrize("overflow", [False, True])
def test_slow_send_is_retired_on_deadline_or_queue_overflow(overflow):
    async def scenario():
        entered = asyncio.Event()

        class Stalled(DummyWebSocket):
            async def send_json(self, payload):
                if payload["type"] == "update":
                    entered.set()
                    await asyncio.Event().wait()
                await super().send_json(payload)

        manager = WebSocketConnectionManager(
            active_session, send_timeout_seconds=5 if overflow else 0.02
        )
        layer, socket = uuid4(), Stalled()
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        event = {"type": "update"}
        await manager.broadcast_to_layer(layer, event)
        await asyncio.wait_for(entered.wait(), 1)
        if overflow:
            for _ in range(32):
                await manager.broadcast_to_layer(layer, event)
            assert manager.get_connection_count(layer) == 1
            await manager.broadcast_to_layer(layer, event)
        await asyncio.wait_for(socket.close_event.wait(), 1)
        assert socket.close_code == 1013
        assert manager.get_connection_count(layer) == 0
        await manager.shutdown()

    asyncio.run(scenario())


def test_shutdown_cancels_stalled_transport_close():
    async def scenario():
        finished = asyncio.Event()

        class Socket(DummyWebSocket):
            async def close(self, code=1000, reason=None):
                try:
                    await asyncio.Event().wait()
                finally:
                    finished.set()

        manager = WebSocketConnectionManager(active_session, close_timeout_seconds=0.02)
        socket = Socket()
        await manager.connect(uuid4(), socket, build_user_context())
        await socket.next_event()
        await asyncio.wait_for(manager.shutdown(), 1)
        await asyncio.wait_for(finished.wait(), 1)

    asyncio.run(scenario())


def test_slow_session_read_is_isolated_and_logout_discards_queued_frames():
    async def scenario():
        slow_context = build_user_context()
        entered, release = asyncio.Event(), asyncio.Event()
        check_delivery = False

        async def check(sid):
            if sid == slow_context.session_id and check_delivery:
                entered.set()
                await release.wait()
            return True

        manager = WebSocketConnectionManager(check)
        layer, slow, fast = uuid4(), DummyWebSocket(), DummyWebSocket()
        await manager.connect(layer, slow, slow_context)
        await manager.connect(layer, fast, build_user_context())
        await slow.next_event()
        await fast.next_event()
        check_delivery = True
        for number in range(2):
            await manager.broadcast_to_layer(layer, {"number": number})
        await asyncio.wait_for(entered.wait(), 1)
        assert await fast.next_event() == {"number": 0}
        assert await fast.next_event() == {"number": 1}
        await manager.disconnect_session(slow_context.session_id)
        release.set()
        assert slow.close_code == 1008 and slow.received.empty()
        await manager.shutdown()

    asyncio.run(scenario())
