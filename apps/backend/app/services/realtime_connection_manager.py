from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from fastapi import WebSocket


@dataclass(frozen=True)
class WebSocketUserContext:
    user_id: UUID
    email: str
    role: str


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, dict[WebSocket, WebSocketUserContext]] = defaultdict(dict)

    async def connect(
        self, layer_id: UUID, websocket: WebSocket, user_context: WebSocketUserContext
    ) -> None:
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

        stale_connections: list[WebSocket] = []
        for websocket in list(layer_connections):
            try:
                await websocket.send_json(event)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            await self.disconnect(layer_id, websocket)

    def get_connection_count(self, layer_id: UUID) -> int:
        return len(self._connections.get(layer_id, {}))
