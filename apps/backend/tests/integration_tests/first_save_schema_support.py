"""SQL fixtures for the first-save schema, independent of its future ORM models."""

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from tests.integration_tests.network_db_support import require_db_tests


BASELINE = "LINESTRING(65.520 44.820,65.525 44.8205,65.530 44.820)"
MOVED = "LINESTRING(65.520 44.820,65.525 44.8215,65.530 44.820)"


def run_committed_scenario(scenario: Callable[[AsyncEngine], Awaitable[None]]) -> None:
    """Exercise real commit boundaries; data lives only in the disposable test DB."""
    require_db_tests()

    async def run() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            await scenario(engine)
        finally:
            await engine.dispose()

    asyncio.run(run())


def run_scenario(scenario: Callable[[AsyncConnection], Awaitable[None]]) -> None:
    require_db_tests()

    async def run() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                try:
                    await scenario(connection)
                finally:
                    if transaction.is_active:
                        await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())


async def seed_context(
    connection: AsyncConnection,
    **overrides: UUID,
) -> dict[str, UUID]:
    ids = {
        name: uuid4()
        for name in (
            "work_order_id",
            "default_state_id",
            "edit_version_id",
            "feature_id",
            "actor_user_id",
            "aoi_id",
            "network_state_id",
            "junction_id",
            "association_id",
        )
    }
    ids.update(overrides)
    params = {
        **ids,
        "code": str(ids["work_order_id"]),
        "baseline": BASELINE,
    }
    statements = [
        """
        INSERT INTO work_order.aois (
            id,
            name,
            geometry
        )
        VALUES (
            :aoi_id,
            :code,
            ST_GeomFromText('POLYGON((65.5 44.8,65.55 44.8,65.55 44.85,65.5 44.85,65.5 44.8))',4326)
        )
        """,
        """INSERT INTO work_order.work_orders
        (
            id,
            code,
            title,
            aoi_id,
            assignee_user_id,
            created_by_user_id
        )
        VALUES (
            :work_order_id,
            :code,
            'Schema fixture',
            :aoi_id,
            :actor_user_id,
            :actor_user_id
        )""",
        """INSERT INTO utility_network.network_states (
            id,
            name
        )
        VALUES (
            :network_state_id,
            :code
        )""",
        """INSERT INTO utility_network.default_states (
            id,
            work_order_id,
            network_state_id
        )
        VALUES (
            :default_state_id,
            :work_order_id,
            :network_state_id
        )""",
        """INSERT INTO utility_network.default_state_features
        (
            default_state_id,
            feature_id,
            asset_code,
            feature_type,
            geometry,
            properties
        )
        VALUES (
            :default_state_id,
            :feature_id,
            'L-003',
            'line',
            ST_GeomFromText(:baseline,4326),
            '{"keep":"baseline"}'::jsonb
        ), (
            :default_state_id,
            :junction_id,
            'J-001',
            'junction',
            ST_GeomFromText('POINT(65.520 44.820)',4326),
            '{}'::jsonb
        )""",
        """INSERT INTO utility_network.default_state_associations
        (
            default_state_id,
            association_id,
            association_type,
            from_feature_id,
            to_feature_id
        )
        VALUES (
            :default_state_id,
            :association_id,
            'connectivity',
            :junction_id,
            :feature_id
        )""",
        """INSERT INTO work_order.edit_versions
        (
            id,
            work_order_id,
            default_state_id,
            owner_user_id
        )
        VALUES (
            :edit_version_id,
            :work_order_id,
            :default_state_id,
            :actor_user_id
        )""",
        """INSERT INTO work_order.edit_version_features
        (
            edit_version_id,
            feature_id,
            asset_code,
            feature_type,
            geometry,
            properties,
            network_version
        )
        SELECT
            :edit_version_id,
            feature_id,
            asset_code,
            feature_type,
            geometry,
            properties,
            network_version
        FROM utility_network.default_state_features
        WHERE default_state_id=:default_state_id""",
        """INSERT INTO work_order.edit_version_associations
        (
            edit_version_id,
            association_id,
            association_type,
            from_feature_id,
            to_feature_id
        )
        VALUES (
            :edit_version_id,
            :association_id,
            'connectivity',
            :junction_id,
            :feature_id
        )""",
    ]
    for statement in statements:
        await connection.execute(
            text(statement),
            params,
        )
    return ids


async def snapshot_context(
    connection: AsyncConnection,
    edit_version_id: UUID,
) -> dict[str, Any]:
    result = await connection.execute(
        text(
            """
        SELECT
            to_jsonb(v) - 'draft_revision' AS version,
            (
                SELECT jsonb_agg(to_jsonb(f) ORDER BY f.feature_id)
                FROM work_order.edit_version_features f
                WHERE f.edit_version_id=v.id
            ) AS features,
            (
                SELECT jsonb_agg(to_jsonb(a) ORDER BY a.association_id)
                FROM work_order.edit_version_associations a
                WHERE a.edit_version_id=v.id
            ) AS associations,
            (
                SELECT jsonb_agg(to_jsonb(b) ORDER BY b.feature_id)
                FROM utility_network.default_state_features b
                WHERE b.default_state_id=v.default_state_id
            ) AS baseline
        FROM work_order.edit_versions v
        WHERE v.id=:id
    """
        ),
        {
            "id": edit_version_id,
        },
    )
    return dict(result.mappings().one())


async def insert_running_command(
    connection: AsyncConnection,
    context: dict[str, UUID],
    command_id: UUID,
) -> None:
    await connection.execute(
        text(
            """
        INSERT INTO work_order.edit_version_commands
        (
            command_id,
            edit_version_id,
            feature_id,
            actor_user_id,
            request_fingerprint,
            state
        )
        VALUES (
            :command_id,
            :edit_version_id,
            :feature_id,
            :actor_user_id,
            'fixture-fingerprint',
            'running'
        )
    """
        ),
        {
            **context,
            "command_id": command_id,
        },
    )


async def finish_command(
    connection: AsyncConnection,
    command_id: UUID,
    *,
    state: str,
    retry_on_access_change: bool = False,
) -> None:
    payload = None
    if state == "succeeded":
        row = (
            (
                await connection.execute(
                    text(
                        """
            SELECT
                c.feature_id,
                v.draft_revision,
                f.operation,
                ST_AsGeoJSON(f.geometry)::jsonb AS geometry
            FROM work_order.edit_version_commands c
            JOIN work_order.edit_versions v ON v.id=c.edit_version_id
            JOIN work_order.edit_version_features f
              ON (f.edit_version_id,f.feature_id)=(c.edit_version_id,c.feature_id)
            WHERE c.command_id=:id
        """
                    ),
                    {
                        "id": command_id,
                    },
                )
            )
            .mappings()
            .one()
        )
        payload = json.dumps(
            {
                "commandId": str(command_id),
                "commandState": "succeeded",
                "draftVersionToken": str(row["draft_revision"]),
                "operation": row["operation"],
                "hasPersistedChangeSet": row["operation"] == "updated",
                "updatedFeature": {
                    "id": str(row["feature_id"]),
                    "geometry": row["geometry"],
                },
                "basicValidation": {
                    "geometryStatus": "passed",
                    "aoiStatus": "passed",
                    "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
                    "dirtyRelativeToBaseline": "passed",
                },
            }
        )
    await connection.execute(
        text(
            """
        UPDATE work_order.edit_version_commands
        SET
            state=:state,
            response_status=:status,
            response_payload=CAST(:payload AS jsonb),
            rejection_code=:code,
            rejection_message=:message,
            retry_on_access_change=:retry,
            completed_at=now()
        WHERE command_id=:id
    """
        ),
        {
            "id": command_id,
            "state": state,
            "payload": payload,
            "status": 200 if state == "succeeded" else (404 if retry_on_access_change else 422),
            "code": (
                None
                if state == "succeeded"
                else ("EDIT_VERSION_NOT_FOUND" if retry_on_access_change else "GEOMETRY_INVALID")
            ),
            "message": None if state == "succeeded" else "Сохранение отклонено.",
            "retry": retry_on_access_change,
        },
    )


async def insert_event(
    connection: AsyncConnection,
    context: dict[str, UUID],
    command_id: UUID,
    **overrides: Any,
) -> None:
    params = {
        **context,
        "command_id": command_id,
        "event_type": "change_set_persisted",
        "before_geometry": BASELINE,
        "after_geometry": MOVED,
        "before_srid": 4326,
        "after_srid": 4326,
        "base_network_revision": 1,
        "draft_revision_before": 1,
        "draft_revision_after": 2,
        **overrides,
    }
    await connection.execute(
        text(
            """
        INSERT INTO work_order.edit_version_change_events
        (
            command_id,
            edit_version_id,
            work_order_id,
            default_state_id,
            feature_id,
            actor_user_id,
            event_type,
            before_geometry,
            after_geometry,
            base_network_revision,
            draft_revision_before,
            draft_revision_after
        )
        VALUES (
            :command_id,
            :edit_version_id,
            :work_order_id,
            :default_state_id,
            :feature_id,
            :actor_user_id,
            :event_type,
            ST_GeomFromText(:before_geometry,:before_srid),
            ST_GeomFromText(:after_geometry,:after_srid),
            :base_network_revision,
            :draft_revision_before,
            :draft_revision_after
        )
    """
        ),
        params,
    )


async def persist_sql_change(
    connection: AsyncConnection,
    context: dict[str, UUID],
    command_id: UUID,
    *,
    emit_event: bool = True,
) -> None:
    await insert_running_command(
        connection,
        context,
        command_id,
    )
    await connection.execute(
        text(
            """
        UPDATE work_order.edit_versions
        SET draft_revision=draft_revision+1
        WHERE id=:edit_version_id
    """
        ),
        context,
    )
    await connection.execute(
        text(
            """
        UPDATE work_order.edit_version_features
        SET
            geometry=ST_GeomFromText(:moved,4326),
            operation='updated'
        WHERE edit_version_id=:edit_version_id
            AND feature_id=:feature_id
    """
        ),
        {
            **context,
            "moved": MOVED,
        },
    )
    await finish_command(
        connection,
        command_id,
        state="succeeded",
    )
    if emit_event:
        await insert_event(
            connection,
            context,
            command_id,
        )
