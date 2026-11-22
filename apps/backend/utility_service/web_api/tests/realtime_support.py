import asyncio
import json
from uuid import uuid4

from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
from utility_service.use_cases.dtos.websocket_user_context import WebSocketUserContext
from utility_service.use_cases.tests.test_realtime_publication_diagnostics import diagnostic_records


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
