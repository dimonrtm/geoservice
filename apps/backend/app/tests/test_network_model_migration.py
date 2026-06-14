import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.network_db_support import require_db_tests


APP_ROOT = Path(__file__).resolve().parent.parent
PREVIOUS_REVISION = "b82a5f2d91c3"
NETWORK_REVISION = "d3a01f4e9c21"
NETWORK_TABLES = {
    "aois",
    "feeders",
    "network_features",
    "network_associations",
}
NETWORK_SCHEMA = "utility_network"
REQUIRED_CONSTRAINTS = {
    "fk_network_features_feeder",
    "uq_network_features_feeder_asset_code",
    "fk_network_associations_from_feature",
    "fk_network_associations_to_feature",
    "uq_network_associations_directed_edge",
    "ck_network_associations_no_self_reference",
}
REQUIRED_INDEXES = {
    "ix_aois_geometry",
    "ix_network_features_geometry",
}
EXPECTED_SPATIAL_INDEXES = {
    ("aois", "geometry"): "ix_aois_geometry",
    ("network_features", "geometry"): "ix_network_features_geometry",
}


def alembic_config() -> Config:
    return Config(str(APP_ROOT / "alembic.ini"))


def read_network_tables() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = :schema_name
                          AND tablename IN (
                              :aoi_table,
                              :feeder_table,
                              :feature_table,
                              :association_table
                          )
                        """
                    ),
                    {
                        "schema_name": NETWORK_SCHEMA,
                        "aoi_table": "aois",
                        "feeder_table": "feeders",
                        "feature_table": "network_features",
                        "association_table": "network_associations",
                    },
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def schema_exists() -> bool:
    async def read() -> bool:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                return bool(
                    await connection.scalar(
                        text(
                            """
                            SELECT EXISTS (
                                SELECT 1
                                FROM pg_namespace
                                WHERE nspname = :schema_name
                            )
                            """
                        ),
                        {"schema_name": NETWORK_SCHEMA},
                    )
                )
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_public_name_collisions() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = 'public'
                          AND tablename IN (
                              :aoi_table,
                              :feeder_table,
                              :feature_table,
                              :association_table
                          )
                        """
                    ),
                    {
                        "aoi_table": "aois",
                        "feeder_table": "feeders",
                        "feature_table": "network_features",
                        "association_table": "network_associations",
                    },
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_network_constraints() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT conname
                        FROM pg_constraint AS constraint_info
                        JOIN pg_class AS table_info
                          ON table_info.oid = constraint_info.conrelid
                        JOIN pg_namespace AS schema_info
                          ON schema_info.oid = table_info.relnamespace
                        WHERE schema_info.nspname = :schema_name
                        """
                    ),
                    {"schema_name": NETWORK_SCHEMA},
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_network_indexes() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT indexname
                        FROM pg_indexes
                        WHERE schemaname = :schema_name
                        """
                    ),
                    {"schema_name": NETWORK_SCHEMA},
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_geometry_gist_indexes() -> dict[tuple[str, str], list[str]]:
    async def read() -> dict[tuple[str, str], list[str]]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT
                            table_info.relname AS table_name,
                            attribute_info.attname AS column_name,
                            index_info.relname AS index_name
                        FROM pg_index AS index_metadata
                        JOIN pg_class AS table_info
                          ON table_info.oid = index_metadata.indrelid
                        JOIN pg_namespace AS schema_info
                          ON schema_info.oid = table_info.relnamespace
                        JOIN pg_class AS index_info
                          ON index_info.oid = index_metadata.indexrelid
                        JOIN pg_am AS access_method
                          ON access_method.oid = index_info.relam
                        JOIN LATERAL unnest(index_metadata.indkey)
                          WITH ORDINALITY AS indexed_column(attnum, position)
                          ON true
                        JOIN pg_attribute AS attribute_info
                          ON attribute_info.attrelid = table_info.oid
                         AND attribute_info.attnum = indexed_column.attnum
                        WHERE schema_info.nspname = :schema_name
                          AND access_method.amname = 'gist'
                          AND table_info.relname IN (
                              'aois',
                              'network_features'
                          )
                          AND attribute_info.attname = 'geometry'
                        ORDER BY table_info.relname, index_info.relname
                        """
                    ),
                    {"schema_name": NETWORK_SCHEMA},
                )
                indexes: dict[tuple[str, str], list[str]] = {}
                for table_name, column_name, index_name in result:
                    indexes.setdefault((table_name, column_name), []).append(index_name)
                return indexes
        finally:
            await engine.dispose()

    return asyncio.run(read())


def assert_exactly_one_geometry_gist_index() -> None:
    indexes = read_geometry_gist_indexes()
    assert set(indexes) == set(EXPECTED_SPATIAL_INDEXES)
    for target, expected_name in EXPECTED_SPATIAL_INDEXES.items():
        assert indexes[target] == [expected_name]


def read_search_path() -> str:
    async def read() -> str:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                return str(await connection.scalar(text("SHOW search_path")))
        finally:
            await engine.dispose()

    return asyncio.run(read())


def assert_network_schema_contract() -> None:
    assert schema_exists() is True
    assert read_network_tables() == NETWORK_TABLES
    assert read_public_name_collisions() == set()
    assert REQUIRED_CONSTRAINTS.issubset(read_network_constraints())
    assert REQUIRED_INDEXES.issubset(read_network_indexes())
    assert_exactly_one_geometry_gist_index()
    assert NETWORK_SCHEMA not in read_search_path()


def test_network_migration_upgrade_downgrade_upgrade_cycle() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.downgrade(config, PREVIOUS_REVISION)
        assert schema_exists() is False
        assert read_network_tables() == set()

        command.upgrade(config, NETWORK_REVISION)
        assert_network_schema_contract()

        command.downgrade(config, PREVIOUS_REVISION)
        assert schema_exists() is False
        assert read_network_tables() == set()

        command.upgrade(config, NETWORK_REVISION)
        assert_network_schema_contract()
    finally:
        command.upgrade(config, "head")
