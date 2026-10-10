import asyncio
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
)


def test_lock_requires_explicit_transaction():
    async def scenario():
        async with AsyncSession() as session:
            with pytest.raises(RepositoryProtocolError):
                await EditVersionRepository(session).lock_version(
                    work_order_id=uuid4(),
                    edit_version_id=uuid4(),
                )
            assert not session.in_transaction()

    asyncio.run(scenario())


def test_lock_rejects_active_savepoint_before_sql():
    async def scenario():
        async with AsyncSession() as session, session.begin():
            async with session.begin_nested():
                with pytest.raises(RepositoryProtocolError):
                    await EditVersionRepository(session).lock_version(
                        work_order_id=uuid4(),
                        edit_version_id=uuid4(),
                    )

    asyncio.run(scenario())
