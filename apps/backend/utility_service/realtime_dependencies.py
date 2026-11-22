from collections.abc import AsyncIterator
from functools import partial

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection

from utility_service.infrastructure.postgresql.feature_registry import UnknownStorageTableError
from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.infrastructure.postgresql.session import get_session
from utility_service.use_cases.domain.exceptions.business_validation_exception import (
    BusinessValidationException,
)
from utility_service.use_cases.services.feature_realtime_publisher import FeatureRealtimePublisher
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.web_api.realtime.realtime_connection_manager import WebSocketConnectionManager
from utility_service.web_api.realtime.feature_events import publish_feature_change


def get_websocket_connection_manager(connection: HTTPConnection) -> WebSocketConnectionManager:
    return connection.app.state.websocket_connection_manager


def get_feature_realtime_publisher(
    manager: WebSocketConnectionManager = Depends(get_websocket_connection_manager),
) -> FeatureRealtimePublisher:
    return FeatureRealtimePublisher(partial(publish_feature_change, manager))


async def get_feature_service(
    session: AsyncSession = Depends(get_session),
    realtime_publisher: FeatureRealtimePublisher = Depends(get_feature_realtime_publisher),
) -> AsyncIterator[FeatureService]:
    service = FeatureService(session, LayerRepository(session), realtime_publisher)
    try:
        yield service
    except UnknownStorageTableError as error:
        raise BusinessValidationException(str(error)) from error
