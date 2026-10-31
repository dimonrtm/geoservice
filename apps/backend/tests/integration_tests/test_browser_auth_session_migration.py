import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.integration_tests.first_save_schema_support import (
    persist_sql_change,
    run_scenario,
    seed_context,
)
from tests.integration_tests.network_db_support import require_db_tests


PREVIOUS_REVISION = "c8e3f0a5b7d9"
APP_ROOT = Path(__file__).resolve().parents[2]
OLD_REVOCATION = datetime(
    2020,
    1,
    1,
    tzinfo=timezone.utc,
)


def run_database(scenario):
    async def run():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.begin() as connection:
                return await scenario(connection)
        finally:
            await engine.dispose()

    return asyncio.run(run())


async def seed_legacy(connection):
    owner = uuid4()
    orphan_owner = uuid4()
    for revoked_at in (None, OLD_REVOCATION):
        await connection.execute(
            text(
                """
                INSERT INTO "user".auth_sessions (
                    id,
                    session_token_hash,
                    user_id,
                    expires_at,
                    revoked_at
                )
                VALUES (
                    :id,
                    :hash,
                    :owner,
                    now() + interval '1 day',
                    :revoked_at
                )
                """
            ),
            {
                "id": uuid4(),
                "hash": uuid4().hex,
                "owner": owner,
                "revoked_at": revoked_at,
            },
        )
    for user_id in (owner, orphan_owner):
        await connection.execute(
            text(
                """
                INSERT INTO "user".websocket_tickets (
                    id,
                    ticket_hash,
                    user_id,
                    layer_id,
                    expires_at
                )
                VALUES (
                    :id,
                    :hash,
                    :owner,
                    :layer,
                    now() + interval '1 day'
                )
                """
            ),
            {
                "id": uuid4(),
                "hash": uuid4().hex,
                "owner": user_id,
                "layer": uuid4(),
            },
        )
    ids = await seed_context(connection)
    await persist_sql_change(
        connection,
        ids,
        uuid4(),
    )
    return ids


async def business_snapshot(connection):
    rows = {}
    for table in (
        "work_order.aois",
        "work_order.work_orders",
        "work_order.edit_versions",
        "work_order.edit_version_features",
        "work_order.edit_version_associations",
        "work_order.edit_version_commands",
        "work_order.edit_version_change_events",
        "utility_network.network_states",
        "utility_network.default_states",
        "utility_network.default_state_features",
        "utility_network.default_state_associations",
    ):
        rows[table] = (
            (
                await connection.execute(
                    text(
                        f"""
                        SELECT to_jsonb(t)
                        FROM {table} t
                        ORDER BY to_jsonb(t)::text
                        """
                    )
                )
            )
            .scalars()
            .all()
        )
    return rows


@pytest.fixture
def migration_database(monkeypatch):
    require_db_tests()
    source_url = make_url(os.environ["TEST_DATABASE_URL"])
    assert source_url.database.endswith("_test")
    database_name = f"ar01_migration_{uuid4().hex}_test"
    owned_database = source_url.set(database=database_name)

    async def execute_admin(statement):
        engine = create_async_engine(
            source_url,
            isolation_level="AUTOCOMMIT",
        )
        try:
            async with engine.connect() as connection:
                await connection.execute(text(statement))
        finally:
            await engine.dispose()

    asyncio.run(execute_admin(f'CREATE DATABASE "{database_name}"'))
    try:
        monkeypatch.setenv(
            "DATABASE_URL",
            owned_database.render_as_string(hide_password=False),
        )
        run_database(
            lambda connection: connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        )
        command.upgrade(
            Config(str(APP_ROOT / "alembic.ini")),
            "head",
        )
        yield
    finally:
        # Удаляется только БД с UUID, созданная этой fixture на test server.
        assert owned_database.database == database_name
        assert database_name.startswith("ar01_migration_")
        assert database_name.endswith("_test")
        assert database_name != source_url.database
        asyncio.run(execute_admin(f'DROP DATABASE "{database_name}"'))


def test_models_register_parent_and_match_migrated_schema():
    async def scenario(connection):
        from utility_service.infrastructure.postgresql.models.base import Base

        def verify(sync_connection):
            database = inspect(sync_connection)
            for table in ("browser_auth_sessions", "auth_sessions", "websocket_tickets"):
                model = Base.metadata.tables[f"user.{table}"]
                actual = {
                    column["name"]: column["nullable"]
                    for column in database.get_columns(
                        table,
                        schema="user",
                    )
                }
                assert actual == {column.name: column.nullable for column in model.columns}
                assert {
                    index["name"]
                    for index in database.get_indexes(
                        table,
                        schema="user",
                    )
                    if not index.get("duplicates_constraint")
                } == {index.name for index in model.indexes}
                assert {
                    key["name"]
                    for key in database.get_foreign_keys(
                        table,
                        schema="user",
                    )
                } == {key.name for key in model.foreign_key_constraints}

        await connection.run_sync(verify)

    run_scenario(scenario)


def test_upgrade_ends_legacy_credentials_and_preserves_business_rows(migration_database):
    require_db_tests()
    config = Config(str(APP_ROOT / "alembic.ini"))
    try:
        command.downgrade(
            config,
            PREVIOUS_REVISION,
        )
        run_database(seed_legacy)
        before = run_database(business_snapshot)
        command.upgrade(
            config,
            "head",
        )

        async def verify(connection):
            assert await business_snapshot(connection) == before
            for table in ("auth_sessions", "websocket_tickets"):
                rows = (
                    await connection.execute(
                        text(
                            f"""
                            SELECT
                                p.revoked_at,
                                c.user_id = p.user_id AS same_owner
                            FROM "user".{table} c
                            LEFT JOIN "user".browser_auth_sessions p ON p.id = c.browser_session_id
                            """
                        )
                    )
                ).all()
                assert rows
                assert all(row.revoked_at is not None and row.same_owner for row in rows)
                indexes = (
                    (
                        await connection.execute(
                            text(
                                """
                                SELECT indexdef
                                FROM pg_indexes
                                WHERE schemaname = 'user'
                                    AND tablename = :table
                                """
                            ),
                            {
                                "table": table,
                            },
                        )
                    )
                    .scalars()
                    .all()
                )
                assert any("(browser_session_id)" in item for item in indexes)
            assert (
                await connection.scalar(
                    text('SELECT count(*) FROM "user".auth_sessions WHERE revoked_at IS NULL')
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text('SELECT count(*) FROM "user".websocket_tickets WHERE used_at IS NULL')
                )
                == 0
            )

        run_database(verify)
    finally:
        command.upgrade(
            config,
            "head",
        )


@pytest.mark.parametrize(
    "table",
    ["auth_sessions", "websocket_tickets"],
)
def test_new_credentials_require_matching_parent(table):
    async def scenario(connection):
        owner = uuid4()
        parent = uuid4()
        await connection.execute(
            text(
                """
                INSERT INTO "user".browser_auth_sessions (
                    id,
                    user_id,
                    expires_at
                )
                VALUES (
                    :id,
                    :owner,
                    now() + interval '1 day'
                )
                """
            ),
            {
                "id": parent,
                "owner": owner,
            },
        )
        extra_columns = ",\n                layer_id" if table == "websocket_tickets" else ""
        extra_values = ",\n                :layer" if table == "websocket_tickets" else ""
        hash_column = "ticket_hash" if table == "websocket_tickets" else "session_token_hash"
        statement = text(
            f"""
            INSERT INTO "user".{table} (
                id,
                {hash_column},
                user_id,
                expires_at,
                browser_session_id{extra_columns}
            )
            VALUES (
                :id,
                :hash,
                :owner,
                now() + interval '1 day',
                :parent{extra_values}
            )
            """
        )
        for parent_id, user_id in ((None, owner), (uuid4(), owner), (parent, uuid4())):
            with pytest.raises(IntegrityError):
                async with connection.begin_nested():
                    await connection.execute(
                        statement,
                        {
                            "id": uuid4(),
                            "hash": uuid4().hex,
                            "owner": user_id,
                            "parent": parent_id,
                            "layer": uuid4(),
                        },
                    )
        await connection.execute(
            statement,
            {
                "id": uuid4(),
                "hash": uuid4().hex,
                "owner": owner,
                "parent": parent,
                "layer": uuid4(),
            },
        )

    run_scenario(scenario)


def test_downgrade_does_not_reactivate_legacy_credentials():
    require_db_tests()
    config = Config(str(APP_ROOT / "alembic.ini"))

    async def seed_active(connection):
        owner, parent = uuid4(), uuid4()
        await connection.execute(
            text(
                """
                INSERT INTO "user".browser_auth_sessions (
                    id,
                    user_id,
                    expires_at
                )
                VALUES (
                    :id,
                    :owner,
                    now() + interval '1 day'
                )
                """
            ),
            {
                "id": parent,
                "owner": owner,
            },
        )
        for revoked_at in (None, OLD_REVOCATION):
            await connection.execute(
                text(
                    """
                    INSERT INTO "user".auth_sessions (
                        id,
                        session_token_hash,
                        user_id,
                        expires_at,
                        revoked_at,
                        browser_session_id
                    )
                    VALUES (
                        :id,
                        :hash,
                        :owner,
                        now() + interval '1 day',
                        :revoked,
                        :parent
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "hash": uuid4().hex,
                    "owner": owner,
                    "parent": parent,
                    "revoked": revoked_at,
                },
            )
        await connection.execute(
            text(
                """
                INSERT INTO "user".websocket_tickets (
                    id,
                    ticket_hash,
                    user_id,
                    layer_id,
                    expires_at,
                    browser_session_id
                )
                VALUES (
                    :id,
                    :hash,
                    :owner,
                    :layer,
                    now() + interval '1 day',
                    :parent
                )
                """
            ),
            {
                "id": uuid4(),
                "hash": uuid4().hex,
                "owner": owner,
                "parent": parent,
                "layer": uuid4(),
            },
        )

    async def verify(connection):
        assert (
            await connection.scalar(
                text('SELECT count(*) FROM "user".auth_sessions WHERE revoked_at IS NULL')
            )
            == 0
        )
        assert (
            await connection.scalar(
                text('SELECT count(*) FROM "user".websocket_tickets WHERE used_at IS NULL')
            )
            == 0
        )
        assert (
            await connection.scalar(
                text('SELECT count(*) FROM "user".auth_sessions WHERE revoked_at = :revoked'),
                {
                    "revoked": OLD_REVOCATION,
                },
            )
            >= 1
        )

    try:
        run_database(seed_active)
        before = run_database(business_snapshot)
        command.downgrade(
            config,
            PREVIOUS_REVISION,
        )
        run_database(verify)
        assert run_database(business_snapshot) == before
        command.upgrade(
            config,
            "head",
        )
        run_database(verify)
    finally:
        command.upgrade(
            config,
            "head",
        )
