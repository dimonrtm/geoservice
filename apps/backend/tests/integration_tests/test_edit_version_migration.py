import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.integration_tests.network_db_support import require_db_tests


APP_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_REVISION = "e4b7a9c2d5f8"
EDIT_VERSION_REVISION = "a8c1f2d3e4b5"
NETWORK_SCHEMA = "utility_network"
EDIT_VERSION_TABLES = {"default_states", "edit_versions"}
REQUIRED_CONSTRAINTS = {
    "uq_default_states_name",
    "ck_default_states_current_revision_positive",
    "fk_edit_versions_work_order",
    "fk_edit_versions_owner",
    "ck_edit_versions_base_revision_positive",
    "ck_edit_versions_status",
}
REQUIRED_INDEXES = {"uq_edit_versions_open_work_order"}


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


def read_edit_version_tables() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :schema_name
              AND tablename IN ('default_states', 'edit_versions')
            """,
            {"schema_name": NETWORK_SCHEMA},
        )
    )


def read_constraints() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT conname
            FROM pg_constraint AS constraint_info
            JOIN pg_class AS table_info
              ON table_info.oid = constraint_info.conrelid
            JOIN pg_namespace AS schema_info
              ON schema_info.oid = table_info.relnamespace
            WHERE schema_info.nspname = :schema_name
            """,
            {"schema_name": NETWORK_SCHEMA},
        )
    )


def read_indexes() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = :schema_name
            """,
            {"schema_name": NETWORK_SCHEMA},
        )
    )


def read_default_state_rows() -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT name || ':' || current_revision::text
            FROM utility_network.default_states
            """
        )
    )


def assert_edit_version_schema_contract() -> None:
    assert read_edit_version_tables() == EDIT_VERSION_TABLES
    assert REQUIRED_CONSTRAINTS.issubset(read_constraints())
    assert REQUIRED_INDEXES.issubset(read_indexes())
    assert read_default_state_rows() == {"default:1"}


def test_edit_version_migration_upgrade_downgrade_upgrade_cycle() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.upgrade(config, EDIT_VERSION_REVISION)
        assert_edit_version_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert read_edit_version_tables() == set()

        command.upgrade(config, EDIT_VERSION_REVISION)
        assert_edit_version_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert read_edit_version_tables() == set()

        command.upgrade(config, EDIT_VERSION_REVISION)
        assert_edit_version_schema_contract()
    finally:
        command.upgrade(config, "head")


OPEN_VERSION_DUPLICATE_SQL = """
WITH demo_user AS (
    INSERT INTO users (id, email, password_hash, role, is_active)
    VALUES (
        '22222222-2222-4222-8222-222222222222',
        'edit-version-concurrency@example.local',
        'hash',
        'editor',
        true
    )
    ON CONFLICT (email) DO UPDATE SET is_active = excluded.is_active
    RETURNING id
),
demo_aoi AS (
    INSERT INTO utility_network.aois (id, name, geometry)
    VALUES (
        '33333333-3333-4333-8333-333333333333',
        'AOI для проверки EditVersion',
        ST_GeomFromText(
            'POLYGON((65.50 44.80,65.54 44.80,65.54 44.84,65.50 44.84,65.50 44.80))',
            4326
        )
    )
    ON CONFLICT (id) DO UPDATE SET name = excluded.name
    RETURNING id
),
demo_feeder AS (
    INSERT INTO utility_network.feeders (id, code, name, is_active)
    VALUES (
        '44444444-4444-4444-8444-444444444444',
        'edit_version_concurrency_feeder',
        'Фидер для проверки EditVersion',
        true
    )
    ON CONFLICT (code) DO UPDATE SET name = excluded.name
    RETURNING id
),
demo_work_order AS (
    INSERT INTO utility_network.work_orders (
        id,
        code,
        title,
        status,
        assignee_id,
        aoi_id,
        feeder_id
    )
    VALUES (
        '55555555-5555-4555-8555-555555555555',
        'WO-EDIT-VERSION-CONCURRENCY',
        'Проверка уникальности EditVersion',
        'assigned',
        '22222222-2222-4222-8222-222222222222',
        '33333333-3333-4333-8333-333333333333',
        '44444444-4444-4444-8444-444444444444'
    )
    ON CONFLICT (code) DO UPDATE SET status = excluded.status
    RETURNING id
)
INSERT INTO utility_network.edit_versions (
    id,
    work_order_id,
    owner_id,
    base_revision,
    status
)
VALUES
    (
        '66666666-6666-4666-8666-666666666661',
        '55555555-5555-4555-8555-555555555555',
        '22222222-2222-4222-8222-222222222222',
        1,
        'open'
    ),
    (
        '66666666-6666-4666-8666-666666666662',
        '55555555-5555-4555-8555-555555555555',
        '22222222-2222-4222-8222-222222222222',
        1,
        'open'
    )
"""


def test_open_edit_version_partial_unique_index_blocks_duplicates() -> None:
    require_db_tests()
    config = alembic_config()
    command.upgrade(config, EDIT_VERSION_REVISION)

    async def insert_duplicates() -> str:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            try:
                async with engine.begin() as connection:
                    await connection.execute(text(OPEN_VERSION_DUPLICATE_SQL))
            except Exception as exc:
                return str(exc)
            return ""
        finally:
            await engine.dispose()

    message = asyncio.run(insert_duplicates())

    assert "uq_edit_versions_open_work_order" in message
