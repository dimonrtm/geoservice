from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.test_browser_auth_session_races import browser_context, issue, refresh
from tests.integration_tests.workspace_api_support import build_workspace_api
from utility_service.infrastructure.postgresql.models.browser_auth_session import BrowserAuthSession
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.use_cases.deps import get_auth_session_access_service
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.utils.settings import settings
from utility_service.web_api.api.auth import create_access_token
from utility_service.web_api.api.secure_router import secure_router


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_all_access_tokens_rejected_after_logout_commit():
    async def scenario(engine):
        async with browser_context(engine) as user:
            first = await issue(
                engine,
                user,
            )
            other = await issue(
                engine,
                user,
            )
            tokens = [
                create_access_token(
                    str(user.id),
                    user.role,
                    first.session_id,
                )
                for _ in range(2)
            ]
            other_token = create_access_token(
                str(user.id),
                user.role,
                other.session_id,
            )
            app = build_workspace_api(engine)
            app.include_router(secure_router)
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                assert (
                    await client.get(
                        "/api/v1/secure/ping",
                        headers=headers(tokens[0]),
                    )
                ).status_code == 200
                result = await client.post(
                    "/api/v1/auth/logout",
                    headers=headers(tokens[0]),
                    json={
                        "session_id": str(first.session_id),
                    },
                )
                assert result.status_code == 200
                assert "set-cookie" not in result.headers
                for token in tokens:
                    response = await client.get(
                        "/api/v1/secure/ping",
                        headers=headers(token),
                    )
                    assert response.status_code == 401
                status = await client.post(
                    "/api/v1/auth/session/status",
                    headers=headers(tokens[0]),
                    json={
                        "session_id": str(first.session_id),
                    },
                )
                assert status.json() == {
                    "session_id": str(first.session_id),
                    "state": "ended",
                }
                assert (
                    await client.get(
                        "/api/v1/secure/ping",
                        headers=headers(other_token),
                    )
                ).status_code == 200
                assert (
                    await refresh(
                        engine,
                        other.token,
                    )
                ).session_id == other.session_id
                with pytest.raises(AuthApiError):
                    await refresh(
                        engine,
                        first.token,
                    )

    run_committed_scenario(scenario)


def test_cookie_proof_is_scoped_to_sid_and_accepts_rotation_history():
    async def scenario(engine):
        async with browser_context(engine) as user:
            first = await issue(
                engine,
                user,
            )
            other = await issue(
                engine,
                user,
            )
            rotated = await refresh(
                engine,
                first.token,
            )
            app = build_workspace_api(engine)
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                cookies={
                    settings.auth_session_cookie_name: other.token,
                },
            ) as client:
                for path in ("logout", "session/status"):
                    response = await client.post(
                        f"/api/v1/auth/{path}",
                        json={
                            "session_id": str(first.session_id),
                        },
                    )
                    assert response.status_code == 401
                client.cookies.set(
                    settings.auth_session_cookie_name,
                    first.token,
                )
                response = await client.post(
                    "/api/v1/auth/session/status",
                    json={
                        "session_id": str(first.session_id),
                    },
                )
                assert response.json()["state"] == "active"
                for _ in range(2):
                    response = await client.post(
                        "/api/v1/auth/logout",
                        json={
                            "session_id": str(first.session_id),
                        },
                    )
                    assert response.status_code == 200
                    assert "set-cookie" not in response.headers
                with pytest.raises(AuthApiError):
                    await refresh(
                        engine,
                        rotated.token,
                    )
                assert (
                    await refresh(
                        engine,
                        other.token,
                    )
                ).session_id == other.session_id

    run_committed_scenario(scenario)


def test_expired_jwt_can_only_read_own_status():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            other = await issue(
                engine,
                user,
            )
            claims = jwt.get_unverified_claims(
                create_access_token(
                    str(user.id),
                    user.role,
                    issued.session_id,
                )
            )
            claims["exp"] = int((datetime.now(timezone.utc) - timedelta(seconds=1)).timestamp())
            token = jwt.encode(
                claims,
                settings.jwt_secret,
                algorithm=settings.jwt_alg,
            )
            app = build_workspace_api(engine)
            app.include_router(secure_router)
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers=headers(token),
            ) as client:
                status = await client.post(
                    "/api/v1/auth/session/status",
                    json={
                        "session_id": str(issued.session_id),
                    },
                )
                assert status.json()["state"] == "active"
                assert (await client.get("/api/v1/secure/ping")).status_code == 401
                assert (
                    await client.post(
                        "/api/v1/auth/logout",
                        json={
                            "session_id": str(issued.session_id),
                        },
                    )
                ).status_code == 401
                assert (
                    await client.post(
                        "/api/v1/auth/session/status",
                        json={
                            "session_id": str(uuid4()),
                        },
                    )
                ).status_code == 401
                client.cookies.set(settings.auth_session_cookie_name, other.token)
                assert (
                    await client.post(
                        "/api/v1/auth/logout",
                        json={"session_id": str(issued.session_id)},
                    )
                ).status_code == 401
                client.cookies.set(settings.auth_session_cookie_name, issued.token)
                logout_response = await client.post(
                    "/api/v1/auth/logout",
                    json={"session_id": str(issued.session_id)},
                )
                assert logout_response.status_code == 200
                assert "set-cookie" not in logout_response.headers

    run_committed_scenario(scenario)


def test_auth_read_finishes_before_protected_business_transaction():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            token = create_access_token(
                str(user.id),
                user.role,
                issued.session_id,
            )
            app = build_workspace_api(engine)
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers=headers(token),
            ) as client:
                # Реальный open_for_work_order начинает transaction до поиска WorkOrder.
                response = await client.post(f"/api/v1/work-orders/{uuid4()}/edit-versions")
                assert response.status_code == 404, response.text
                assert response.json()["code"] == "WORK_ORDER_NOT_FOUND"

    run_committed_scenario(scenario)


def test_sid_read_refreshes_retained_parent_after_other_connection_logout():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            token = create_access_token(
                str(user.id),
                user.role,
                issued.session_id,
            )
            async with AsyncSession(
                engine,
                expire_on_commit=False,
            ) as reading:
                async with reading.begin():
                    retained = await reading.get(
                        BrowserAuthSession,
                        issued.session_id,
                    )
                service = get_auth_session_access_service(reading)
                assert await service.is_session_active(issued.session_id) is True
                assert not reading.in_transaction()
                async with AsyncSession(engine) as writing:
                    await get_auth_session_access_service(writing).logout(
                        issued.session_id,
                        token,
                        None,
                    )
                assert retained.revoked_at is None
                assert await service.is_session_active(issued.session_id) is False
                assert not reading.in_transaction()
                assert retained.revoked_at is not None

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "state",
    ["expired", "inactive", "deleted"],
)
def test_status_reports_ended_for_unavailable_parent_or_owner(state):
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            token = create_access_token(
                str(user.id),
                user.role,
                issued.session_id,
            )
            async with AsyncSession(engine) as session, session.begin():
                if state == "expired":
                    await session.execute(
                        update(BrowserAuthSession)
                        .where(BrowserAuthSession.id == issued.session_id)
                        .values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
                    )
                elif state == "inactive":
                    await session.execute(
                        update(User).where(User.id == user.id).values(is_active=False)
                    )
                else:
                    await session.execute(delete(User).where(User.id == user.id))
            async with AsyncSession(engine) as session:
                service = get_auth_session_access_service(session)
                assert (
                    await service.status(
                        issued.session_id,
                        token,
                        None,
                    )
                    == "ended"
                )
                with pytest.raises(AuthApiError):
                    await service.authenticate(token)

    run_committed_scenario(scenario)
