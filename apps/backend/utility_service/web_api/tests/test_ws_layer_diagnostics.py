import asyncio

import pytest
from fastapi import WebSocketDisconnect
from uuid import uuid4

from utility_service.web_api.api.ws_layers import subscribe_to_layer_updates
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.tests.test_realtime_connection_manager import (
    active_session,
    build_user_context,
)
from utility_service.use_cases.tests.test_realtime_delivery_diagnostics import (
    ControlledSocket,
    publish_change,
    delivery_records,
)


@pytest.mark.parametrize(
    "code,reason",
    [
        (1000, None),
        (1001, None),
        (1005, None),
        (1006, "abnormal_disconnect"),
        (1002, "abnormal_disconnect"),
        (None, "disconnect_unknown"),
    ],
)
@pytest.mark.parametrize("as_exception", [False, True])
def test_disconnect_classification_reaches_manager(caplog, code, reason, as_exception):
    async def scenario():
        trigger = asyncio.Event()

        class RouteSocket(ControlledSocket):
            async def receive(self):
                await trigger.wait()
                if as_exception:
                    raise WebSocketDisconnect(code=code, reason="SECRET")
                return {"type": "websocket.disconnect", "code": code, "reason": "SECRET"}

        socket, layer = RouteSocket(), uuid4()
        manager = WebSocketConnectionManager(active_session)
        route = asyncio.create_task(
            subscribe_to_layer_updates(socket, layer, build_user_context(), manager)
        )
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()
        publish_change(manager, layer, 2)
        trigger.set()
        await asyncio.wait_for(route, 1)
        await manager.shutdown()
        records = delivery_records(caplog)
        if reason is None:
            assert records == []
        else:
            assert len(records) == 2
            assert {item["reason"] for item in records} == {reason}
            assert {item["eventId"] for item in records} == {"evt_1", "evt_2"}
            if code is not None:
                assert {item["closeCode"] for item in records} == {code}
        assert "SECRET" not in caplog.text

    asyncio.run(scenario())


def test_receive_error_and_writer_error_log_once(caplog):
    async def scenario():
        class RouteSocket(ControlledSocket):
            async def receive(self):
                await self.close_event.wait()
                raise OSError("SECRET transport")

        socket, layer = RouteSocket(fail=True), uuid4()
        manager = WebSocketConnectionManager(active_session)
        route = asyncio.create_task(
            subscribe_to_layer_updates(socket, layer, build_user_context(), manager)
        )
        await socket.next_event()
        publish_change(manager, layer, 1)
        await socket.entered.wait()
        publish_change(manager, layer, 2)
        socket.release.set()
        await asyncio.wait_for(route, 1)
        await manager.shutdown()
        records = delivery_records(caplog)
        assert len(records) == 2
        assert {item["reason"] for item in records} == {"send_error"}
        assert "SECRET" not in caplog.text

    asyncio.run(scenario())
