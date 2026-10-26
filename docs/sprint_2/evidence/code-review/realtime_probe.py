"""Детерминированная проверка последовательного fanout без сети и БД."""

import asyncio
import json
from uuid import uuid4

from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
    WebSocketUserContext,
)


async def main():
    entered = asyncio.Event()
    release = asyncio.Event()
    received = []

    class Socket:
        def __init__(self, slow):
            self.slow = slow

        async def accept(self):
            pass

        async def send_json(self, event):
            if self.slow:
                entered.set()
                await release.wait()
            received.append(self.slow)

    manager = WebSocketConnectionManager()
    layer = uuid4()
    user = WebSocketUserContext(uuid4(), "probe@example.invalid", "editor")
    await manager.connect(layer, Socket(True), user)
    await manager.connect(layer, Socket(False), user)
    task = asyncio.create_task(manager.broadcast_to_layer(layer, {"type": "probe"}))
    await asyncio.wait_for(entered.wait(), 1)
    assert received == [] and not task.done()
    release.set()
    await asyncio.wait_for(task, 1)
    assert received == [True, False]
    print(json.dumps({"slow_socket_blocks_fast_socket": True, "network_used": False}))


asyncio.run(main())
