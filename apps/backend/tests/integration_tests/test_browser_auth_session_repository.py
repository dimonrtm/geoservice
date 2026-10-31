from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario


def repository(session):
    from utility_service.infrastructure.postgresql.repositories.browser_auth_session_repository import (
        BrowserAuthSessionRepository,
    )

    return BrowserAuthSessionRepository(session)


def test_parent_lifecycle_is_transactional_and_revocation_is_final():
    async def scenario(engine):
        owner = uuid4()
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=1)
        extended = expires + timedelta(hours=2)
        async with AsyncSession(engine) as session:
            async with session.begin():
                parent = await repository(session).create_session(
                    user_id=owner,
                    expires_at=expires,
                )
                parent_id = parent.id
                assert parent.user_id == owner
                assert parent.created_at is not None
                assert parent.revoked_at is None
            async with session.begin():
                await repository(session).extend_session(
                    parent_id,
                    expires_at=extended,
                )
            async with session.begin():
                row = await repository(session).get_session(parent_id)
                assert row.expires_at == extended
                assert await repository(session).get_session(uuid4()) is None
                await repository(session).revoke_session(
                    parent_id,
                    now=now,
                )
            async with session.begin():
                await repository(session).revoke_session(
                    parent_id,
                    now=now + timedelta(seconds=1),
                )
                await repository(session).extend_session(
                    parent_id,
                    expires_at=extended + timedelta(days=1),
                )
                row = await repository(session).get_session(parent_id)
                assert row.revoked_at == now
                assert row.expires_at == extended
            async with session.begin():
                rolled_back = await repository(session).create_session(
                    user_id=owner,
                    expires_at=expires,
                )
                rolled_back_id = rolled_back.id
                await session.rollback()
            async with session.begin():
                assert await repository(session).get_session(rolled_back_id) is None

    run_committed_scenario(scenario)


def test_parent_lock_serializes_competing_writers():
    async def scenario(engine):
        now = datetime.now(timezone.utc)
        async with AsyncSession(engine) as setup, setup.begin():
            parent = await repository(setup).create_session(
                user_id=uuid4(),
                expires_at=now + timedelta(days=1),
            )
            parent_id = parent.id
        async with AsyncSession(engine) as first, AsyncSession(engine) as second:
            async with first.begin():
                assert (
                    await repository(first).get_session(
                        parent_id,
                        for_update=True,
                    )
                    is not None
                )
                with pytest.raises(DBAPIError) as error:
                    async with second.begin():
                        await second.execute(text("SET LOCAL lock_timeout = '100ms'"))
                        await repository(second).get_session(
                            parent_id,
                            for_update=True,
                        )
                assert error.value.orig.sqlstate == "55P03"
                await repository(first).revoke_session(
                    parent_id,
                    now=now,
                )
            async with second.begin():
                row = await repository(second).get_session(
                    parent_id,
                    for_update=True,
                )
                assert row.revoked_at == now

    run_committed_scenario(scenario)
