import asyncio
import os
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


DB_TESTS_ENABLED = os.getenv("RUN_DB_TESTS") == "1"


def require_db_tests() -> None:
    if not DB_TESTS_ENABLED:
        pytest.skip("Set RUN_DB_TESTS=1 to run PostgreSQL/PostGIS tests.")


def run_in_rollback_transaction(
    scenario: Callable[[AsyncSession], Awaitable[None]],
) -> None:
    require_db_tests()

    async def run() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    # Service rollback must not erase fixture setup inside the outer test transaction.
                    join_transaction_mode="create_savepoint",
                )
                try:
                    await scenario(session)
                finally:
                    if session.in_transaction():
                        await session.rollback()
                    await session.close()
                    if transaction.is_active:
                        await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
