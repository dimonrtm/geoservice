# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 12:15:56 2026

@author: dimon
"""

from fastapi import Depends, Request, WebSocket
from db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import AuthService
from services.feature_realtime_publisher import FeatureRealtimePublisher
from services.feature_service import FeatureService
from services.layer_service import LayerService
from services.realtime_connection_manager import WebSocketConnectionManager
from services.utility_network_service import UtilityNetworkService
from repositories.user_repository import UserRepository
from repositories.layer_repository import LayerRepository
from repositories.utility_network_repository import UtilityNetworkRepository


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
