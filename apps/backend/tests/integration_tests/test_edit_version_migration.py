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
SCHEMA_REPAIR_REVISION = "c9d0e1f2a3b4"
NETWORK_SCHEMA = "utility_network"
WORK_ORDER_SCHEMA = "work_order"
UTILITY_BASELINE_TABLES = {
    "network_states",
    "default_states",
    "default_state_features",
    "default_state_associations",
}
EDIT_VERSION_TABLES = {
    "edit_versions",
    "edit_version_features",
    "edit_version_associations",
}
WORK_ORDER_BASELINE_TABLES = {"aois", "work_orders"}
WORK_ORDER_TABLES = {"aois", "work_orders", *EDIT_VERSION_TABLES}
REQUIRED_CONSTRAINTS = {
    "uq_network_states_name",
    "ck_network_states_current_revision_positive",
    "uq_default_states_work_order",
    "ck_default_states_base_network_revision_positive",
    "fk_default_states_network_state",
    "ck_aois_geometry_not_empty",
    "ck_aois_geometry_valid",
    "ck_aois_geometry_srid",
    "ck_aois_geometry_type",
    "fk_work_orders_aoi",
    "fk_edit_versions_work_order",
    "ck_edit_versions_base_network_revision_positive",
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


def read_tables(schema_name: str, table_names: set[str]) -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :schema_name
              AND tablename = ANY(:table_names)
            """,
            {"schema_name": schema_name, "table_names": list(table_names)},
        )
    )


def read_constraints(schema_name: str) -> set[str]:
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
            {"schema_name": schema_name},
        )
    )


def read_indexes(schema_name: str) -> set[str]:
    return asyncio.run(
        scalar_set(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = :schema_name
            """,
            {"schema_name": schema_name},
        )
    )


def column_exists(schema_name: str, table_name: str, column_name: str) -> bool:
    return (
        asyncio.run(
            scalar_set(
                """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema_name
              AND table_name = :table_name
              AND column_name = :column_name
            """,
                {
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "column_name": column_name,
                },
            )
        )
        == {column_name}
    )


def utility_network_aoi_exists() -> bool:
    return (
        asyncio.run(
            scalar_set(
                """
            SELECT to_regclass('utility_network.aois')::text
            """
            )
        )
        != {None}
    )


def assert_edit_version_schema_contract() -> None:
    assert read_tables(NETWORK_SCHEMA, UTILITY_BASELINE_TABLES) == UTILITY_BASELINE_TABLES
    assert read_tables(WORK_ORDER_SCHEMA, WORK_ORDER_TABLES) == WORK_ORDER_TABLES
    assert column_exists(WORK_ORDER_SCHEMA, "work_orders", "aoi_id") is True
    constraints = read_constraints(NETWORK_SCHEMA) | read_constraints(WORK_ORDER_SCHEMA)
    assert REQUIRED_CONSTRAINTS.issubset(constraints)
    assert REQUIRED_INDEXES.issubset(read_indexes(WORK_ORDER_SCHEMA))
    assert utility_network_aoi_exists() is False


def assert_edit_version_schema_absent() -> None:
    assert read_tables(NETWORK_SCHEMA, UTILITY_BASELINE_TABLES) == set()
    assert read_tables(WORK_ORDER_SCHEMA, EDIT_VERSION_TABLES) == set()
    assert read_tables(WORK_ORDER_SCHEMA, WORK_ORDER_BASELINE_TABLES) == WORK_ORDER_BASELINE_TABLES
    assert column_exists(WORK_ORDER_SCHEMA, "work_orders", "aoi_id") is True
    assert utility_network_aoi_exists() is False


def test_edit_version_migration_upgrade_downgrade_upgrade_cycle() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.upgrade(config, SCHEMA_REPAIR_REVISION)
        assert_edit_version_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert_edit_version_schema_absent()

        command.upgrade(config, SCHEMA_REPAIR_REVISION)
        assert_edit_version_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert_edit_version_schema_absent()

        command.upgrade(config, SCHEMA_REPAIR_REVISION)
        assert_edit_version_schema_contract()
    finally:
        command.upgrade(config, "head")


OPEN_VERSION_DUPLICATE_SQL = """
WITH demo_work_order AS (
    INSERT INTO work_order.work_orders (
        id,
        code,
        title,
        status,
        aoi_id,
        assignee_user_id,
        created_by_user_id
    )
    VALUES (
        '55555555-5555-4555-8555-555555555555',
        'WO-EDIT-VERSION-CONCURRENCY',
        'EditVersion uniqueness check',
        'assigned',
        '55555555-5555-4555-8555-555555555554',
        '22222222-2222-4222-8222-222222222222',
        '22222222-2222-4222-8222-222222222222'
    )
    ON CONFLICT (code) DO UPDATE SET status = excluded.status
    RETURNING id
)
INSERT INTO work_order.edit_versions (
    id,
    work_order_id,
    default_state_id,
    owner_user_id,
    base_network_revision,
    status
)
VALUES
    (
        '66666666-6666-4666-8666-666666666661',
        '55555555-5555-4555-8555-555555555555',
        '77777777-7777-4777-8777-777777777777',
        '22222222-2222-4222-8222-222222222222',
        1,
        'open'
    ),
    (
        '66666666-6666-4666-8666-666666666662',
        '55555555-5555-4555-8555-555555555555',
        '77777777-7777-4777-8777-777777777777',
        '22222222-2222-4222-8222-222222222222',
        1,
        'open'
    )
"""

OPEN_VERSION_AOI_SQL = """
INSERT INTO work_order.aois (
    id,
    name,
    geometry
)
VALUES (
    '55555555-5555-4555-8555-555555555554',
    'EditVersion uniqueness AOI',
    ST_GeomFromText(
        'POLYGON ((65.495 44.795, 65.545 44.795, 65.545 44.835, 65.495 44.835, 65.495 44.795))',
        4326
    )
)
ON CONFLICT (id) DO NOTHING
"""


def test_open_edit_version_partial_unique_index_blocks_duplicates() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.downgrade(config, PREVIOUS_REVISION)
        command.upgrade(config, SCHEMA_REPAIR_REVISION)

        async def insert_duplicates() -> str:
            engine = create_async_engine(os.environ["DATABASE_URL"])
            try:
                try:
                    async with engine.begin() as connection:
                        await connection.execute(text(OPEN_VERSION_AOI_SQL))
                        await connection.execute(text(OPEN_VERSION_DUPLICATE_SQL))
                except Exception as exc:
                    return str(exc)
                return ""
            finally:
                await engine.dispose()

        message = asyncio.run(insert_duplicates())

        assert "uq_edit_versions_open_work_order" in message
    finally:
        command.upgrade(config, "head")
