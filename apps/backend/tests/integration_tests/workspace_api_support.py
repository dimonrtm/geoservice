from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from utility_service.infrastructure.postgresql.session import get_session
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.deps import get_auth_session_service, get_realtime_session_checker
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.mappers import to_auth_user_dto
from utility_service.web_api.api.auth import auth_router, create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.work_orders import work_orders_router
from utility_service.web_api.middleware.correlation_id import CorrelationIdMiddleware


def build_workspace_api(engine: AsyncEngine) -> FastAPI:
    app = FastAPI()
    app.state.test_engine = engine
    app.state.websocket_connection_manager = WebSocketConnectionManager(
        get_realtime_session_checker(async_sessionmaker(engine, expire_on_commit=False))
    )
    app.add_middleware(CorrelationIdMiddleware)
    install_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(work_orders_router)

    async def fresh_session():
        async with AsyncSession(
            engine,
            expire_on_commit=False,
        ) as session:
            yield session

    app.dependency_overrides[get_session] = fresh_session
    return app


@asynccontextmanager
async def client_for(
    app,
    ids,
    *,
    authenticated=True,
):
    headers = {}
    if authenticated:
        async with AsyncSession(app.state.test_engine) as session:
            async with session.begin():
                user = await UserRepository(session).get_by_id(ids["actor_user_id"])
                dto = to_auth_user_dto(user)
            issued = await get_auth_session_service(session).issue_session(dto)
        token = create_access_token(
            str(dto.id),
            dto.role,
            issued.session_id,
        )
        headers["Authorization"] = f"Bearer {token}"
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client


def version_path(ids):
    return f"/api/v1/work-orders/{ids['work_order_id']}/edit-versions/{ids['edit_version_id']}"


def geometry_path(ids):
    return f"{version_path(ids)}/features/{ids['feature_id']}/geometry"


async def read_workspace(
    client,
    ids,
):
    response = await client.get(f"{version_path(ids)}/workspace")
    assert response.status_code == 200, response.text
    return response.json()["workOrder"]["editVersion"]


def current_geometry(
    workspace,
    ids,
):
    return next(
        f["geometry"]
        for f in workspace["features"]["features"]
        if f["id"] == str(ids["feature_id"])
    )


def assert_error(
    response,
    status,
    code,
):
    assert response.status_code == status, response.text
    payload = response.json()
    assert set(payload) == {"code", "message", "correlationId"}
    assert payload["code"] == code
    assert payload["correlationId"] == response.headers["X-Correlation-ID"]
