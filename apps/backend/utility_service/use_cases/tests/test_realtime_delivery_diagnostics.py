import asyncio
import logging
from uuid import uuid4

import pytest

from utility_service.use_cases.dtos.realtime_diagnostics import (
    RealtimeEventContext,
    RealtimeFailureReason,
)
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.tests.test_realtime_connection_manager import (
    DummyWebSocket,
    active_session,
    build_user_context,
)
from utility_service.use_cases.tests.test_realtime_publication_diagnostics import diagnostic_records


class ControlledSocket(DummyWebSocket):
    def __init__(self, *, fail=False):
        super().__init__()
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.fail = fail

    async def send_json(self, payload):
        if payload["type"] != "connected":
            self.entered.set()
            await self.release.wait()
            if self.fail:
                raise OSError("SECRET")
        await super().send_json(payload)


def publish_change(manager, layer, number, padding=""):
    context = RealtimeEventContext(f"evt_{number}", "feature_updated", layer, uuid4(), number)
    manager.publish_event(
        context,
        lambda: {
            "type": "feature_updated",
            "eventId": context.event_id,
            "padding": padding,
        },
    )


def delivery_records(caplog):
    return [
        item for item in diagnostic_records(caplog) if item["event"] == "realtime_delivery_failed"
    ]


@pytest.mark.parametrize(
    "reason",
    [
        "send_error",
        "send_timeout",
        "frame_too_large",
        "queue_frames_exceeded",
        "queue_bytes_exceeded",
    ],
)
def test_retire_reports_exact_failed_pairs(caplog, reason):
    async def scenario():
        manager = WebSocketConnectionManager(
            active_session,
            max_pending_frames=2,
            max_pending_bytes=200,
            send_timeout_seconds=0.03 if reason == "send_timeout" else 5,
        )
        layer, socket, fast = (
            uuid4(),
            ControlledSocket(fail=reason == "send_error"),
            DummyWebSocket(),
        )
        for subscriber in (socket, fast):
            await manager.connect(layer, subscriber, build_user_context())
            await subscriber.next_event()
        publish_change(manager, layer, 1)
        await asyncio.wait_for(socket.entered.wait(), 1)
        assert (await fast.next_event())["eventId"] == "evt_1"
        publish_change(manager, layer, 2)
        await fast.next_event()
        expected_ids = {"evt_1", "evt_2"}
        if reason == "queue_frames_exceeded":
            publish_change(manager, layer, 3)
            await fast.next_event()
            publish_change(manager, layer, 4)
            await fast.next_event()
            expected_ids |= {"evt_3", "evt_4"}
        elif reason == "frame_too_large":
            publish_change(manager, layer, 3, "ж" * 200)
            expected_ids.add("evt_3")
        elif reason == "queue_bytes_exceeded":
            publish_change(manager, layer, 3, "ж" * 50)
            expected_ids.add("evt_3")
            await fast.next_event()
        elif reason == "send_error":
            socket.release.set()
        await asyncio.wait_for(socket.close_event.wait(), 1)
        records = delivery_records(caplog)
        # An oversized frame is rejected for both sockets; other failures affect only the slow one.
        fast_connection = manager._connections.get(layer, {}).get(fast)
        if reason == "frame_too_large":
            assert len(records) == len(expected_ids) + 1
            groups = {}
            for item in records:
                groups.setdefault(item["connectionId"], []).append(item)
            slow_records = next(group for group in groups.values() if len(group) > 1)
        else:
            assert fast_connection is not None
            assert len(records) == len(expected_ids)
            slow_records = records
            assert all(
                item["connectionId"] != str(fast_connection.connection_id) for item in records
            )
        assert {item["eventId"] for item in slow_records} == expected_ids
        assert {item["reason"] for item in slow_records} == {reason}
        assert (
            next(item for item in slow_records if item["eventId"] == "evt_1")["outcome"]
            == "send_unconfirmed"
        )
        assert all(
            item["outcome"] == "not_sent" for item in slow_records if item["eventId"] != "evt_1"
        )
        assert "SECRET" not in caplog.text
        assert socket.close_code == 1013
        await manager.shutdown()

    asyncio.run(scenario())


def test_successful_send_racing_retire_is_not_failure(caplog):
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        layer, socket = uuid4(), DummyWebSocket()
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        publish_change(manager, layer, 1)
        # next_event wakes after send_text returns, before writer necessarily resumes.
        await socket.next_event()
        await manager.disconnect(
            layer, socket, failure_reason=RealtimeFailureReason.ABNORMAL_DISCONNECT
        )
        assert delivery_records(caplog) == []
        await manager.shutdown()

    asyncio.run(scenario())


def test_multiple_retire_paths_do_not_duplicate(caplog):
    async def scenario():
        layer, socket = uuid4(), ControlledSocket(fail=True)
        manager = WebSocketConnectionManager(active_session)
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()
        publish_change(manager, layer, 2)
        await manager.disconnect(
            layer, socket, failure_reason=RealtimeFailureReason.ABNORMAL_DISCONNECT
        )
        socket.release.set()
        await manager.disconnect(layer, socket, failure_reason=RealtimeFailureReason.SEND_ERROR)
        await manager.shutdown()
        records = delivery_records(caplog)
        assert len(records) == 2
        assert {item["eventId"] for item in records} == {"evt_1", "evt_2"}
        assert {item["reason"] for item in records} == {"abnormal_disconnect"}

    asyncio.run(scenario())


@pytest.mark.parametrize("operation", ["disconnect", "logout", "shutdown"])
def test_expected_cancellation_is_silent(caplog, operation):
    async def scenario():
        layer, socket, user = uuid4(), ControlledSocket(), build_user_context()
        manager = WebSocketConnectionManager(active_session)
        await manager.connect(layer, socket, user)
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()
        publish_change(manager, layer, 2)
        if operation == "disconnect":
            await manager.disconnect(layer, socket)
        elif operation == "logout":
            await manager.disconnect_session(user.session_id)
        await manager.shutdown()
        assert diagnostic_records(caplog) == []

    asyncio.run(scenario())


@pytest.mark.parametrize("technical_error", [False, True])
def test_session_check_error_reports_all_affected_subscriptions(caplog, technical_error):
    async def scenario():
        user, other_user = build_user_context(), build_user_context()
        failed = False

        async def checker(sid):
            if failed and sid == user.session_id:
                if technical_error:
                    raise OSError("SECRET session database")
                return False
            return True

        manager = WebSocketConnectionManager(checker)
        layer = uuid4()
        sockets = [DummyWebSocket(), DummyWebSocket(), DummyWebSocket()]
        for socket, context in zip(sockets, [user, user, other_user]):
            await manager.connect(layer, socket, context)
            await socket.next_event()
        failed = True
        publish_change(manager, layer, 1)
        publish_change(manager, layer, 2)
        for socket in sockets[:2]:
            await asyncio.wait_for(socket.close_event.wait(), 1)
            assert socket.close_code == 1008
        assert (await sockets[2].next_event())["eventId"] == "evt_1"
        assert (await sockets[2].next_event())["eventId"] == "evt_2"
        records = delivery_records(caplog)
        assert len(records) == (4 if technical_error else 0)
        if technical_error:
            assert len({(item["eventId"], item["connectionId"]) for item in records}) == 4
            assert {item["reason"] for item in records} == {"session_check_failed"}
            assert {item["outcome"] for item in records} == {"not_sent"}
        await manager.shutdown()

    asyncio.run(scenario())


@pytest.mark.parametrize("hang", [False, True])
def test_cleanup_failure_does_not_repeat_delivery_records(caplog, hang):
    async def scenario():
        class BrokenClose(ControlledSocket):
            async def close(self, code=1000, reason=None):
                if hang:
                    await asyncio.Event().wait()
                raise OSError("SECRET close")

        manager = WebSocketConnectionManager(active_session, close_timeout_seconds=0.01)
        socket, layer = BrokenClose(fail=True), uuid4()
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()
        socket.release.set()
        # Wait for retirement rather than arbitrary scheduling sleeps.
        while manager.get_connection_count(layer):
            await asyncio.sleep(0)
        await manager.shutdown()
        records = diagnostic_records(caplog)
        assert len(delivery_records(caplog)) == 1
        cleanup = [item for item in records if item["event"] == "realtime_cleanup_failed"]
        assert len(cleanup) == 1
        assert cleanup[0]["reason"] == ("close_timeout" if hang else "close_error")
        assert "SECRET" not in caplog.text

    asyncio.run(asyncio.wait_for(scenario(), 2))


def test_connected_failure_has_no_fictitious_feature(caplog):
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        socket = DummyWebSocket(fail_on_send=True)
        await manager.connect(uuid4(), socket, build_user_context())
        await asyncio.wait_for(socket.close_event.wait(), 1)
        records = diagnostic_records(caplog)
        assert len(records) == 1
        assert records[0]["event"] == "realtime_connection_failed"
        assert "eventId" not in records[0] and "featureId" not in records[0]
        assert records[0]["connectionId"]
        await manager.shutdown()

    asyncio.run(scenario())


def test_unexpected_writer_failure_retires_pending_frames(caplog, monkeypatch):
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        socket, layer = ControlledSocket(), uuid4()
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        subscription = manager._connections[layer][socket]
        publish_change(manager, layer, 1)
        await socket.entered.wait()

        async def broken_get():
            raise RuntimeError("SECRET writer")

        monkeypatch.setattr(subscription.queue, "get", broken_get)
        publish_change(manager, layer, 2)
        socket.release.set()
        await socket.next_event()
        await asyncio.wait_for(socket.close_event.wait(), 1)
        records = delivery_records(caplog)
        assert [item["eventId"] for item in records] == ["evt_2"]
        assert records[0]["reason"] == "writer_failed"
        await manager.shutdown()

    asyncio.run(scenario())


def test_idle_writer_failure_is_diagnosed_without_fictitious_change(caplog, monkeypatch):
    async def scenario():
        manager = WebSocketConnectionManager(active_session)
        socket, layer = ControlledSocket(), uuid4()
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()

        async def broken_get():
            raise RuntimeError("SECRET idle writer")

        monkeypatch.setattr(manager._connections[layer][socket].queue, "get", broken_get)
        socket.release.set()
        await socket.next_event()
        await asyncio.wait_for(socket.close_event.wait(), 1)
        records = diagnostic_records(caplog)
        assert len(records) == 1
        assert records[0]["event"] == "realtime_connection_failed"
        assert records[0]["reason"] == "writer_failed"
        assert "eventId" not in records[0] and "outcome" not in records[0]
        assert socket.close_code == 1013
        await manager.shutdown()

    asyncio.run(scenario())


def test_handler_failure_does_not_interrupt_emergency_cleanup():
    class FailingHandler(logging.Handler):
        def emit(self, record):
            raise OSError("sink unavailable")

    async def scenario():
        socket, layer = ControlledSocket(fail=True), uuid4()
        manager = WebSocketConnectionManager(active_session)
        await manager.connect(layer, socket, build_user_context())
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()
        publish_change(manager, layer, 2)
        subscription = manager._connections[layer][socket]
        socket.release.set()
        await asyncio.wait_for(socket.close_event.wait(), 1)
        await manager.shutdown()
        assert manager.get_connection_count(layer) == 0
        assert subscription.queue.empty()
        assert subscription.current_frame is None
        assert subscription.pending_bytes == 0
        assert socket.close_code == 1013
        assert all(task.done() for task in manager._tasks)

    logger = logging.getLogger("utility_service.realtime")
    handler = FailingHandler()
    logger.addHandler(handler)
    try:
        asyncio.run(scenario())
    finally:
        logger.removeHandler(handler)
