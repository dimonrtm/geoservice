from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, WebSocketException, status

from api.auth import decode_token
from services.auth_service import AuthService
from services.realtime_connection_manager import WebSocketUserContext

ALLOWED_REALTIME_ROLES = {"editor", "reviewer"}


def _websocket_auth_error(reason: str) -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=reason)


async def authenticate_websocket_token(
    token: str | None, auth_service: AuthService
) -> WebSocketUserContext:
    if token is None or not token.strip():
        raise _websocket_auth_error("Токен отсутствует")

    try:
        payload = decode_token(token)
    except HTTPException as exc:
        raise _websocket_auth_error(str(exc.detail)) from exc

    if "sub" not in payload or payload.get("role") not in ALLOWED_REALTIME_ROLES:
        raise _websocket_auth_error("Некорректное содержимое токена")

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError as exc:
        raise _websocket_auth_error("Токен недействителен или срок его действия истёк") from exc

    current_user = await auth_service.get_user_by_id(user_id)
    if current_user is None:
        raise _websocket_auth_error("Токен недействителен или срок его действия истёк")

    if not current_user.is_active:
        raise _websocket_auth_error("Учетная запись отключена.")

    if current_user.role.value not in ALLOWED_REALTIME_ROLES:
        raise _websocket_auth_error("Подписка на realtime недоступна для этой роли")

    return WebSocketUserContext(
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
    )
