import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.integration_tests.network_db_support import require_db_tests


APP_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_REVISION = "7f4dbcd151ee"
USER_ROLE_REVISION = "b82a5f2d91c3"
USER_SCHEMA = "user"


def alembic_config() -> Config:
    return Config(str(APP_ROOT / "alembic.ini"))


async def scalar_set(sql: str, params: dict | None = None) -> set[str]:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text(sql), params or {})
            return set(result.scalars())
    finally:
        await engine.dispose()


async def row_mapping(sql: str, params: dict | None = None) -> dict[str, tuple[str, str]]:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text(sql), params or {})
            return {row.column_name: (row.is_nullable, row.column_default or "") for row in result}
    finally:
        await engine.dispose()


def schema_exists(schema_name: str) -> bool:
    return (
        asyncio.run(
            scalar_set(
                """
                SELECT nspname
                FROM pg_namespace
                WHERE nspname = :schema_name
                """,
                {"schema_name": schema_name},
            )
        )
        == {schema_name}
    )


def read_user_columns() -> dict[str, tuple[str, str]]:
    return asyncio.run(
        row_mapping(
            """
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'user'
              AND table_name = 'users'
              AND column_name IN ('id', 'email', 'password_hash', 'role', 'is_active')
            """,
        )
    )


def read_user_constraints() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT pg_get_constraintdef(constraint_info.oid)
            FROM pg_constraint AS constraint_info
            JOIN pg_class AS table_info
              ON table_info.oid = constraint_info.conrelid
            JOIN pg_namespace AS schema_info
              ON schema_info.oid = table_info.relnamespace
            WHERE schema_info.nspname = 'user'
              AND table_info.relname = 'users'
            """,
        )
    )


def test_user_role_migration_creates_production_like_role_baseline() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.downgrade(config, PREVIOUS_REVISION)
        assert schema_exists(USER_SCHEMA) is False

        command.upgrade(config, USER_ROLE_REVISION)

        columns = read_user_columns()
        assert set(columns) == {"id", "email", "password_hash", "role", "is_active"}
        assert columns["role"][0] == "NO"
        assert columns["is_active"][0] == "NO"
        assert "true" in columns["is_active"][1].lower()

        constraint_text = "\n".join(read_user_constraints()).lower()
        assert "editor" in constraint_text
        assert "reviewer" in constraint_text
        assert "'viewer'" not in constraint_text
    finally:
        command.upgrade(config, "head")
