from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status

from api.deps import get_auth_service, get_layer_service, get_websocket_connection_manager
from api.websocket_auth import authenticate_websocket_token
from services.auth_service import AuthService
from services.layer_service import LayerService
from services.realtime_connection_manager import WebSocketConnectionManager

ws_layers_router = APIRouter(tags=["realtime"])


def _websocket_route_error(reason: str) -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=reason)


@ws_layers_router.websocket("/api/v1/ws/layers/{layer_id}")
async def subscribe_to_layer_updates(
    websocket: WebSocket,
    layer_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    layer_service: LayerService = Depends(get_layer_service),
    connection_manager: WebSocketConnectionManager = Depends(get_websocket_connection_manager),
) -> None:
    token = websocket.query_params.get("token")
    user_context = await authenticate_websocket_token(token, auth_service)

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
