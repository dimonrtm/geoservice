from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status

from utility_service.use_cases.deps import (
    get_layer_service,
    get_websocket_connection_manager,
    get_websocket_ticket_service,
)
from utility_service.web_api.api.auth import get_current_user
from utility_service.utils.websocket_ticket_auth import authenticate_websocket_ticket
from utility_service.use_cases.schemas.realtime import WebSocketTicketOut
from utility_service.use_cases.services.layer_service import LayerService
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.services.websocket_ticket_service import WebSocketTicketService

ws_layers_router = APIRouter(tags=["realtime"])


def _websocket_route_error(reason: str) -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=reason)


@ws_layers_router.post(
    "/api/v1/ws/layers/{layer_id}/ticket",
    response_model=WebSocketTicketOut,
)
async def issue_layer_websocket_ticket(
    layer_id: UUID,
    user: Any = Depends(get_current_user),
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
) -> WebSocketTicketOut:
    return await ticket_service.issue_ticket(user, layer_id)


@ws_layers_router.websocket("/api/v1/ws/layers/{layer_id}")
async def subscribe_to_layer_updates(
    websocket: WebSocket,
    layer_id: UUID,
    layer_service: LayerService = Depends(get_layer_service),
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
    connection_manager: WebSocketConnectionManager = Depends(get_websocket_connection_manager),
) -> None:
    ticket = websocket.query_params.get("ticket")
    user_context = await authenticate_websocket_ticket(ticket, layer_id, ticket_service)

    layer = await layer_service.get_layer_by_id(layer_id)
    if layer is None:
        raise _websocket_route_error("Слой не найден")

    await connection_manager.connect(layer_id, websocket, user_context)
    try:
        await websocket.send_json({"type": "connected", "layerId": str(layer_id)})
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect(layer_id, websocket)
