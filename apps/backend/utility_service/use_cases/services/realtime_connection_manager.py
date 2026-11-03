from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status


@dataclass(frozen=True)
class WebSocketUserContext:
    user_id: UUID
    email: str
    role: str
    session_id: UUID


SessionActivityChecker = Callable[[UUID], Awaitable[bool]]


@dataclass(eq=False)
class LayerSubscription:
    layer_id: UUID
    socket: WebSocket
    context: WebSocketUserContext
    queue: asyncio.Queue[tuple[str, int]]
    pending_bytes: int = 0
    writer: asyncio.Task | None = None


class WebSocketConnectionManager:
    def __init__(
        self,
        is_session_active: SessionActivityChecker,
        *,
        close_timeout_seconds: float = 1.0,
        send_timeout_seconds: float = 5.0,
        max_pending_frames: int = 32,
        max_pending_bytes: int = 1024 * 1024,
    ) -> None:
        self._is_session_active = is_session_active
        self._close_timeout_seconds = close_timeout_seconds
        self._send_timeout_seconds = send_timeout_seconds
        self._max_pending_frames = max_pending_frames
        self._max_pending_bytes = max_pending_bytes
        self._connections: dict[UUID, dict[WebSocket, LayerSubscription]] = defaultdict(dict)
        self._tasks: set[asyncio.Task] = set()

    async def _session_active(self, session_id: UUID) -> bool:
        try:
            return await self._is_session_active(session_id)
        except Exception:
            return False

    def _track(self, coroutine):
        task = asyncio.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._task_finished)
        return task

    def _task_finished(self, task):
        self._tasks.discard(task)
        if not task.cancelled():
            task.exception()

    async def connect(
        self, layer_id: UUID, websocket: WebSocket, user_context: WebSocketUserContext
    ) -> None:
        if not await self._session_active(user_context.session_id):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Сессия недействительна"
            )
        await websocket.accept()
        subscription = LayerSubscription(
            layer_id, websocket, user_context, asyncio.Queue(self._max_pending_frames)
        )
        self._connections[layer_id][websocket] = subscription
        self._publish((subscription,), {"type": "connected", "layerId": str(layer_id)})
        if websocket in self._connections.get(layer_id, {}):
            subscription.writer = self._track(self._write(subscription))

    async def _write(self, subscription: LayerSubscription) -> None:
        while True:
            text, size = await subscription.queue.get()
            subscription.pending_bytes -= size
            if not await self._session_active(subscription.context.session_id):
                await self.disconnect_session(subscription.context.session_id)
                return
            if (
                self._connections.get(subscription.layer_id, {}).get(subscription.socket)
                is not subscription
            ):
                return
            try:
                sending = self._track(subscription.socket.send_text(text))
                try:
                    done, _ = await asyncio.wait([sending], timeout=self._send_timeout_seconds)
                    if not done:
                        self._retire(subscription, 1013)
                        return
                    sending.result()
                finally:
                    if not sending.done():
                        sending.cancel()
            except Exception:
                self._retire(subscription, 1013)
                return

    async def broadcast_to_layer(self, layer_id: UUID, event: dict[str, object]) -> None:
        connections = self._connections.get(layer_id)
        if connections:
            self._publish(tuple(connections.values()), event)

    def _publish(self, subscriptions, event):
        text = json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        size = len(text.encode("utf-8"))
        for subscription in subscriptions:
            if (
                subscription.queue.full()
                or subscription.pending_bytes + size > self._max_pending_bytes
            ):
                self._retire(subscription, 1013)
            else:
                subscription.queue.put_nowait((text, size))
                subscription.pending_bytes += size

    def _retire(self, subscription, code=None):
        connections = self._connections.get(subscription.layer_id)
        if not connections or connections.pop(subscription.socket, None) is None:
            return None
        if not connections:
            del self._connections[subscription.layer_id]
        while not subscription.queue.empty():
            subscription.queue.get_nowait()
        subscription.pending_bytes = 0
        if subscription.writer and subscription.writer is not asyncio.current_task():
            subscription.writer.cancel()
        if code is not None:
            return self._track(self._close(subscription.socket, code))
        return None

    async def _close(self, websocket, code):
        async def close_transport():
            try:
                await websocket.close(code=code)
            except Exception:
                pass

        task = self._track(close_transport())
        try:
            await asyncio.wait([task], timeout=self._close_timeout_seconds)
        finally:
            if not task.done():
                task.cancel()

    async def disconnect(self, layer_id: UUID, websocket: WebSocket) -> None:
        subscription = self._connections.get(layer_id, {}).get(websocket)
        if subscription:
            self._retire(subscription)

    async def disconnect_session(self, session_id: UUID) -> None:
        subscriptions = [
            subscription
            for connections in self._connections.values()
            for subscription in connections.values()
            if subscription.context.session_id == session_id
        ]
        closing = [self._retire(subscription, 1008) for subscription in subscriptions]
        if closing:
            await asyncio.gather(*closing)

    async def shutdown(self) -> None:
        for connections in tuple(self._connections.values()):
            for subscription in tuple(connections.values()):
                self._retire(subscription, 1001)
        if self._tasks:
            _, pending = await asyncio.wait(tuple(self._tasks), timeout=self._close_timeout_seconds)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.wait(pending, timeout=self._close_timeout_seconds)

    def get_connection_count(self, layer_id: UUID) -> int:
        return len(self._connections.get(layer_id, {}))
