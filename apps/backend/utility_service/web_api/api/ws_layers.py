from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from utility_service.use_cases.deps import (
    get_layer_service,
    get_session_factory,
    get_websocket_connection_manager,
    get_websocket_ticket_service,
)
from utility_service.use_cases.dtos import AuthUserDTO, AuthenticatedSession
from utility_service.web_api.api.auth import get_auth_context, require_legacy_gis_editor
from utility_service.utils.websocket_ticket_auth import authenticate_websocket_ticket
from utility_service.use_cases.schemas.realtime import WebSocketTicketOut
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
    WebSocketUserContext,
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
    user: AuthUserDTO = Depends(require_legacy_gis_editor),
    context: AuthenticatedSession = Depends(get_auth_context),
    ticket_service: WebSocketTicketService = Depends(get_websocket_ticket_service),
) -> WebSocketTicketOut:
    return await ticket_service.issue_ticket(user, layer_id, context.session_id)


async def get_layer_subscription_context(
    websocket: WebSocket,
    layer_id: UUID,
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> WebSocketUserContext:
    ticket = websocket.query_params.get("ticket")
    async with session_factory() as session:
        user_context = await authenticate_websocket_ticket(
            ticket, layer_id, get_websocket_ticket_service(session)
        )
        layer = await get_layer_service(session).get_layer_by_id(layer_id)
        if layer is None:
            raise _websocket_route_error("Слой не найден")
    return user_context


@ws_layers_router.websocket("/api/v1/ws/layers/{layer_id}")
async def subscribe_to_layer_updates(
    websocket: WebSocket,
    layer_id: UUID,
    user_context: WebSocketUserContext = Depends(get_layer_subscription_context),
    connection_manager: WebSocketConnectionManager = Depends(get_websocket_connection_manager),
) -> None:
    await connection_manager.connect(layer_id, websocket, user_context)
    try:
        if not await connection_manager.send_to_connection(
            layer_id, websocket, {"type": "connected", "layerId": str(layer_id)}
        ):
            return
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect(layer_id, websocket)
