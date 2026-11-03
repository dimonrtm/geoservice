"""Стенд для однопроцессной приёмки в отдельном Compose с временной PostGIS."""

# Импорт session создаёт engine из DATABASE_URL, поэтому сначала настраиваем тестовую БД.
# ruff: noqa: E402

import os
from contextlib import asynccontextmanager
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from tests.db_test_isolation import configure_db_test_environment

configure_db_test_environment(os.environ)
if os.environ.get("RUN_DB_TESTS") != "1":
    raise RuntimeError("Требуется изолированная тестовая БД")

from utility_service.infrastructure.postgresql.models.layer import Layer
from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.repositories.user_repository import (
    UserRepository,
)
from utility_service.infrastructure.postgresql.session import engine
from utility_service.use_cases.deps import get_realtime_session_checker
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.utils.passwords import hash_password
from utility_service.web_api.main import api

production_lifespan = api.router.lifespan_context


@asynccontextmanager
async def fixture_lifespan(app):
    async with production_lifespan(app):
        async with AsyncSession(engine) as session, session.begin():
            await UserRepository(session).create_user(
                email=os.environ["AR02_EDITOR_EMAIL"],
                role=UserRole.EDITOR,
                password_hash=hash_password(os.environ["AR02_EDITOR_PASSWORD"]),
                user_id=uuid4(),
            )
            session.add(
                Layer(
                    id=uuid4(),
                    name="ar02-browser",
                    title="AR-02 browser",
                    geometry_type="Polygon",
                    storage_table="feature_polygons",
                )
            )
        app.state.websocket_connection_manager = WebSocketConnectionManager(
            get_realtime_session_checker(), max_pending_bytes=2048
        )
        yield


api.router.lifespan_context = fixture_lifespan
