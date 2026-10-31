from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import asyncio
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status


@dataclass(frozen=True)
class WebSocketUserContext:
    user_id: UUID
    email: str
    role: str
    session_id: UUID


SessionActivityChecker = Callable[[UUID], Awaitable[bool]]


class WebSocketConnectionManager:
    def __init__(
        self,
        is_session_active: SessionActivityChecker,
        *,
        close_timeout_seconds: float = 1.0,
    ) -> None:
        self._is_session_active = is_session_active
        self._close_timeout_seconds = close_timeout_seconds
        self._connections: dict[UUID, dict[WebSocket, WebSocketUserContext]] = defaultdict(dict)

    async def _session_active(self, session_id: UUID) -> bool:
        try:
            return await self._is_session_active(session_id)
        except Exception:
            return False

    async def connect(
        self, layer_id: UUID, websocket: WebSocket, user_context: WebSocketUserContext
    ) -> None:
        # Успешный свежий read — точка допуска. Уже допущенный connect может
        # завершиться, если logout commit случился во время accept.
        if not await self._session_active(user_context.session_id):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Сессия недействительна"
            )
        await websocket.accept()
        self._connections[layer_id][websocket] = user_context

    async def disconnect(self, layer_id: UUID, websocket: WebSocket) -> None:
        layer_connections = self._connections.get(layer_id)
        if not layer_connections:
            return

        layer_connections.pop(websocket, None)
        if not layer_connections:
            self._connections.pop(layer_id, None)

    async def broadcast_to_layer(self, layer_id: UUID, event: dict[str, object]) -> None:
        layer_connections = self._connections.get(layer_id)
        if not layer_connections:
            return

        for websocket in list(layer_connections):
            await self.send_to_connection(layer_id, websocket, event)

    async def send_to_connection(
        self, layer_id: UUID, websocket: WebSocket, event: dict[str, object]
    ) -> bool:
        context = self._connections.get(layer_id, {}).get(websocket)
        if context is None:
            return False
        if not await self._session_active(context.session_id):
            await self.disconnect_session(context.session_id)
            return False
        # Допуск отправки завершён. Её результат не отменяется задним числом.
        try:
            await websocket.send_json(event)
            return True
        except Exception:
            await self.disconnect(layer_id, websocket)
            return False

    async def disconnect_session(self, session_id: UUID) -> None:
        sockets = []
        for layer_id, connections in list(self._connections.items()):
            for websocket, context in list(connections.items()):
                if context.session_id == session_id:
                    await self.disconnect(layer_id, websocket)
                    sockets.append(websocket)
        if not sockets:
            return

        async def close(websocket):
            try:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION, reason="Сессия завершена"
                )
            except Exception:
                pass

        tasks = [asyncio.create_task(close(websocket)) for websocket in sockets]
        # Общий bound, включая случай подавления cancellation внутри transport.
        _, pending = await asyncio.wait(tasks, timeout=self._close_timeout_seconds)
        for task in pending:
            task.cancel()

    def get_connection_count(self, layer_id: UUID) -> int:
        return len(self._connections.get(layer_id, {}))
