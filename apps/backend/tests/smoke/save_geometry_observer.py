"""Independent, read-only persistence evidence for the live geometry smoke."""

import asyncio
import os
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.smoke.full_path_workspace_smoke import SmokeFailure


async def begin_read_only(connection):
    await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))


async def read_snapshot(
    engine, *, work_order_id: str, edit_version_id: str, feature_id: str
) -> dict:
    params = {
        "work_order_id": UUID(work_order_id),
        "edit_version_id": UUID(edit_version_id),
        "feature_id": UUID(feature_id),
    }
    async with engine.connect() as connection, connection.begin():
        await begin_read_only(connection)
        snapshot = await connection.scalar(
            text(
                """
                SELECT jsonb_build_object(
                    'work_order_id', v.work_order_id, 'edit_version_id', v.id,
                    'feature_id', f.feature_id, 'default_state_id', v.default_state_id,
                    'owner', v.owner_user_id, 'revision', v.draft_revision,
                    'geometry', ST_AsGeoJSON(f.geometry, 15)::jsonb,
                    'geometryBytes', encode(ST_AsEWKB(f.geometry), 'hex'),
                    'operation', f.operation,
                    'baseline', ST_AsGeoJSON(b.geometry, 15)::jsonb,
                    'baselineBytes', encode(ST_AsEWKB(b.geometry), 'hex')
                )
                FROM work_order.edit_versions v
                JOIN work_order.work_orders w ON w.id=v.work_order_id
                JOIN utility_network.default_states d
                    ON d.id=v.default_state_id AND d.work_order_id=w.id
                JOIN work_order.edit_version_features f ON f.edit_version_id=v.id
                JOIN utility_network.default_state_features b
                    ON b.default_state_id=d.id AND b.feature_id=f.feature_id
                WHERE v.id=:edit_version_id AND w.id=:work_order_id AND f.feature_id=:feature_id
                """
            ),
            params,
        )
        if snapshot is None:
            raise SmokeFailure("SQL observer: target linkage не найден")
        snapshot["commands"] = await connection.scalar(
            text(
                """SELECT coalesce(jsonb_agg(to_jsonb(c) ORDER BY c.command_id), '[]'::jsonb)
                FROM work_order.edit_version_commands c WHERE edit_version_id=:edit_version_id"""
            ),
            params,
        )
        snapshot["events"] = await connection.scalar(
            text(
                """SELECT coalesce(jsonb_agg(
                    (to_jsonb(e) - 'before_geometry' - 'after_geometry') || jsonb_build_object(
                        'beforeBytes', encode(ST_AsEWKB(e.before_geometry), 'hex'),
                        'afterBytes', encode(ST_AsEWKB(e.after_geometry), 'hex')
                    ) ORDER BY e.draft_revision_after), '[]'::jsonb)
                FROM work_order.edit_version_change_events e WHERE edit_version_id=:edit_version_id"""
            ),
            params,
        )
        return snapshot


def snapshot_save_state(*, work_order_id: str, edit_version_id: str, feature_id: str) -> dict:
    async def run():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            return await read_snapshot(
                engine,
                work_order_id=work_order_id,
                edit_version_id=edit_version_id,
                feature_id=feature_id,
            )
        finally:
            await engine.dispose()

    return asyncio.run(run())
