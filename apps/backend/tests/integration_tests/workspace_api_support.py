from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from utility_service.infrastructure.postgresql.session import get_session
from utility_service.web_api.api.auth import auth_router, create_access_token
from utility_service.web_api.api.exception_handlers import install_exception_handlers
from utility_service.web_api.api.work_orders import work_orders_router
from utility_service.web_api.middleware.correlation_id import CorrelationIdMiddleware


def build_workspace_api(engine: AsyncEngine) -> FastAPI:
    app = FastAPI()
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


def client_for(
    app,
    ids,
    *,
    authenticated=True,
):
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=(
            {
                "Authorization": f"Bearer {create_access_token(str(ids['actor_user_id']), 'editor',)}",
            }
            if authenticated
            else {}
        ),
    )


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
