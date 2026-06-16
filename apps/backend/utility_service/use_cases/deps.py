from __future__ import annotations

from fastapi import Depends, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.utility_network_repository import (
    UtilityNetworkRepository,
)
from utility_service.infrastructure.postgresql.session import engine, get_session
from utility_service.use_cases.services.auth_service import AuthService
from utility_service.use_cases.services.feature_realtime_publisher import FeatureRealtimePublisher
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.services.layer_service import LayerService
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.services.utility_network_service import UtilityNetworkService


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session, UserRepository(session))


def get_feature_realtime_publisher(request: Request) -> FeatureRealtimePublisher:
    connection_manager = request.app.state.websocket_connection_manager
    return FeatureRealtimePublisher(connection_manager)


def get_feature_service(
    session: AsyncSession = Depends(get_session),
    realtime_publisher: FeatureRealtimePublisher = Depends(get_feature_realtime_publisher),
) -> FeatureService:
    return FeatureService(session, LayerRepository(session), realtime_publisher)


def get_layer_service(session: AsyncSession = Depends(get_session)) -> LayerService:
    return LayerService(session, LayerRepository(session))


def get_utility_network_service(
    session: AsyncSession = Depends(get_session),
) -> UtilityNetworkService:
    return UtilityNetworkService(
        session,
        UtilityNetworkRepository(session),
    )


def get_websocket_connection_manager(websocket: WebSocket) -> WebSocketConnectionManager:
    return websocket.app.state.websocket_connection_manager


async def close_runtime_resources() -> None:
    await engine.dispose()
