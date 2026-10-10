from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from tests.integration_tests.first_save_schema_support import seed_context


async def seed_repository_context(connection: AsyncConnection):
    ids = await seed_context(connection)
    await connection.execute(
        text("UPDATE work_order.work_orders SET status='in_progress' WHERE id=:id"),
        {"id": ids["work_order_id"]},
    )
    return ids


async def read_context(
    session: AsyncSession,
    ids,
):
    from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
        EditVersionRepository,
    )

    repository = EditVersionRepository(session)
    root = await repository.lock_version(
        work_order_id=ids["work_order_id"],
        edit_version_id=ids["edit_version_id"],
    )
    return repository, await repository.read_context(
        root,
        feature_id=ids["feature_id"],
    )


async def snapshot_repository_state(
    connection,
    ids,
):
    queries = {
        "root": "SELECT to_jsonb(v) FROM work_order.edit_versions v WHERE id=:edit_version_id",
        "aoi": "SELECT to_jsonb(a) FROM work_order.aois a WHERE id=:aoi_id",
        "baseline_root": "SELECT to_jsonb(b) FROM utility_network.default_states b WHERE id=:default_state_id",
        "baseline": """
            SELECT jsonb_agg(to_jsonb(f) ORDER BY feature_id)
            FROM utility_network.default_state_features f
            WHERE default_state_id = :default_state_id
            """,
        "baseline_associations": """
            SELECT jsonb_agg(to_jsonb(a) ORDER BY association_id)
            FROM utility_network.default_state_associations a
            WHERE default_state_id = :default_state_id
            """,
        "features": """
            SELECT jsonb_agg(to_jsonb(f) ORDER BY feature_id)
            FROM work_order.edit_version_features f
            WHERE edit_version_id = :edit_version_id
            """,
        "associations": """
            SELECT jsonb_agg(to_jsonb(a) ORDER BY association_id)
            FROM work_order.edit_version_associations a
            WHERE edit_version_id = :edit_version_id
            """,
    }
    return {
        name: await connection.scalar(
            text(query),
            ids,
        )
        for name, query in queries.items()
    }


async def prepare_change(
    repository,
    context,
    *,
    revert=False,
):
    from dataclasses import replace
    from decimal import Decimal
    from utility_service.infrastructure.postgresql.geometry_codec import decode_geometry

    baseline = decode_geometry(context.baseline.geometry_ewkb)
    request = (
        baseline
        if revert
        else replace(
            baseline,
            coordinates=(
                baseline.coordinates[0],
                (
                    Decimal("65.526"),
                    Decimal("44.821"),
                ),
                *baseline.coordinates[2:],
            ),
        )
    )
    return await repository.validate_candidate(
        context,
        repository.prepare_candidate(
            context,
            request,
        ),
    )
