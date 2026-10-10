from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.edit_geometry_repository_support import (
    read_context,
    seed_repository_context,
)
from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    encode_geometry,
)
from utility_service.infrastructure.postgresql.repositories.edit_geometry_validation import (
    check_context,
)


def test_context_invariants_and_eligibility():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
        async with AsyncSession(engine) as session, session.begin():
            _, context = await read_context(
                session,
                ids,
            )
            assert check_context(context) is None
            for operation in (
                "created",
                "deleted",
            ):
                value = replace(
                    context,
                    current=replace(
                        context.current,
                        operation=operation,
                    ),
                    baseline=None,
                )
                assert check_context(value).code == "FEATURE_NOT_EDITABLE"
            point = replace(
                context.current,
                feature_type="junction",
            )
            assert (
                check_context(
                    replace(
                        context,
                        current=point,
                    )
                ).code
                == "FEATURE_NOT_EDITABLE"
            )
            for value in (
                replace(
                    context,
                    baseline=None,
                ),
                replace(
                    context,
                    default_state=None,
                ),
                replace(
                    context,
                    aoi_ewkb=None,
                ),
                replace(
                    context,
                    default_state=replace(
                        context.default_state,
                        work_order_id=uuid4(),
                    ),
                ),
                replace(
                    context,
                    default_state=replace(
                        context.default_state,
                        base_network_revision=2,
                    ),
                ),
                replace(
                    context,
                    baseline=replace(
                        context.baseline,
                        feature_type="junction",
                    ),
                ),
                replace(
                    context,
                    current=replace(
                        context.current,
                        operation="updated",
                    ),
                ),
                replace(
                    context,
                    current=replace(
                        context.current,
                        geometry_ewkb=b"bad",
                    ),
                ),
            ):
                assert check_context(value).code == "WORK_ORDER_CONTEXT_INVALID"
            baseline = decode_geometry(context.baseline.geometry_ewkb)
            two = replace(
                baseline,
                coordinates=(
                    baseline.coordinates[0],
                    baseline.coordinates[-1],
                ),
            )
            short = replace(
                context,
                current=replace(
                    context.current,
                    geometry_ewkb=encode_geometry(two),
                ),
                baseline=replace(
                    context.baseline,
                    geometry_ewkb=encode_geometry(two),
                ),
            )
            assert check_context(short).code == "FEATURE_NOT_EDITABLE"
            endpoint = replace(
                baseline,
                coordinates=(
                    (
                        Decimal("65.519"),
                        Decimal("44.820"),
                    ),
                    *baseline.coordinates[1:],
                ),
            )
            broken = replace(
                context,
                current=replace(
                    context.current,
                    geometry_ewkb=encode_geometry(endpoint),
                    operation="updated",
                ),
            )
            assert check_context(broken).code == "WORK_ORDER_CONTEXT_INVALID"
            assert (
                check_context(
                    replace(
                        context,
                        current=replace(
                            context.current,
                            geometry_ewkb=encode_geometry(two),
                        ),
                    )
                ).code
                == "WORK_ORDER_CONTEXT_INVALID"
            )
            longer = replace(
                baseline,
                coordinates=(
                    *baseline.coordinates[:2],
                    (
                        Decimal("65.528"),
                        Decimal("44.821"),
                    ),
                    baseline.coordinates[-1],
                ),
            )
            both = replace(
                longer,
                coordinates=(
                    longer.coordinates[0],
                    (
                        Decimal("65.526"),
                        Decimal("44.822"),
                    ),
                    (
                        Decimal("65.529"),
                        Decimal("44.822"),
                    ),
                    longer.coordinates[-1],
                ),
            )
            value = replace(
                context,
                baseline=replace(
                    context.baseline,
                    geometry_ewkb=encode_geometry(longer),
                ),
                current=replace(
                    context.current,
                    operation="updated",
                    geometry_ewkb=encode_geometry(both),
                ),
            )
            assert check_context(value).code == "WORK_ORDER_CONTEXT_INVALID"
            one = replace(
                longer,
                coordinates=(
                    *longer.coordinates[:2],
                    (
                        Decimal("65.529"),
                        Decimal("44.822"),
                    ),
                    longer.coordinates[-1],
                ),
            )
            assert (
                check_context(
                    replace(
                        value,
                        current=replace(
                            value.current,
                            geometry_ewkb=encode_geometry(one),
                        ),
                    )
                )
                is None
            )

    run_committed_scenario(scenario)


def test_prepare_uses_persisted_policy_and_preserves_rejection():
    from sqlalchemy import text

    async def scenario(engine):
        # Policy is immutable: create a new version with the desired policy in the fixture.
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            await connection.execute(
                text("DELETE FROM work_order.edit_version_associations WHERE edit_version_id=:id"),
                {"id": ids["edit_version_id"]},
            )
            await connection.execute(
                text("DELETE FROM work_order.edit_versions WHERE id=:id"),
                {"id": ids["edit_version_id"]},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO work_order.edit_versions (
                        id,
                        work_order_id,
                        default_state_id,
                        owner_user_id,
                        geometry_xy_resolution,
                        geometry_rounding_mode,
                        geometry_policy_version
                    ) VALUES (
                        :edit_version_id,
                        :work_order_id,
                        :default_state_id,
                        :actor_user_id,
                        0.00000025,
                        'ROUND_HALF_AWAY_FROM_ZERO',
                        1
                    )
                    """
                ),
                ids,
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO work_order.edit_version_features (
                        edit_version_id,
                        feature_id,
                        asset_code,
                        feature_type,
                        geometry
                    )
                    SELECT
                        :edit_version_id,
                        feature_id,
                        asset_code,
                        feature_type,
                        geometry
                    FROM utility_network.default_state_features
                    WHERE default_state_id = :default_state_id
                    """
                ),
                ids,
            )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            baseline = decode_geometry(context.baseline.geometry_ewkb)
            request = replace(
                baseline,
                coordinates=(
                    baseline.coordinates[0],
                    (
                        Decimal("0.000000375"),
                        baseline.coordinates[1][1],
                    ),
                    baseline.coordinates[-1],
                ),
            )
            result = repository.prepare_candidate(
                context,
                request,
            )
            assert result.prepared.geometry.coordinates[1][0] == Decimal("0.0000005")
            wrong = GeometryValue(
                "LineString",
                (
                    baseline.coordinates[0],
                    baseline.coordinates[-1],
                ),
            )
            assert (
                repository.prepare_candidate(
                    context,
                    wrong,
                ).prepared.rejection_code
                == "GEOMETRY_STRUCTURE_CHANGED"
            )

    run_committed_scenario(scenario)
