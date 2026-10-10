from dataclasses import replace
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.edit_geometry_repository_support import (
    read_context,
    seed_repository_context,
)
from utility_service.infrastructure.postgresql.geometry_codec import decode_geometry
from utility_service.infrastructure.postgresql.repositories.edit_geometry_validation import (
    inspect_spatial,
)


SQUARE = "POLYGON((0 0,4 0,4 4,0 4,0 0))"
HOLE = "POLYGON((0 0,4 0,4 4,0 4,0 0),(1 1,1 3,3 3,3 1,1 1))"
MULTI = "MULTIPOLYGON(((0 0,1 0,1 1,0 1,0 0)),((3 0,4 0,4 1,3 1,3 0)))"


@pytest.mark.parametrize(
    "line,aoi,valid,simple,segments,covered",
    [
        (
            "LINESTRING(0 0,1 1,2 0)",
            SQUARE,
            True,
            True,
            True,
            True,
        ),
        (
            "LINESTRING(0 0,2 2,0 2,2 0)",
            SQUARE,
            True,
            False,
            True,
            False,
        ),
        (
            "LINESTRING(0 0,0 0,2 0)",
            SQUARE,
            True,
            True,
            False,
            False,
        ),
        (
            "LINESTRING(0 0,0 0)",
            SQUARE,
            False,
            True,
            False,
            False,
        ),
        (
            "LINESTRING(0 0,2 0,4 0)",
            SQUARE,
            True,
            True,
            True,
            True,
        ),
        (
            "LINESTRING(0.5 2,3.5 2)",
            HOLE,
            True,
            True,
            True,
            False,
        ),
        (
            "LINESTRING(0.2 0.2,0.8 0.8)",
            MULTI,
            True,
            True,
            True,
            True,
        ),
        (
            "LINESTRING(0.2 0.2,3.8 0.8)",
            MULTI,
            True,
            True,
            True,
            False,
        ),
        (
            "LINESTRING(0.5 3,3.5 3)",
            "POLYGON((0 0,4 0,4 4,3 4,3 1,1 1,1 4,0 4,0 0))",
            True,
            True,
            True,
            False,
        ),
    ],
)
def test_spatial_predicates(
    line,
    aoi,
    valid,
    simple,
    segments,
    covered,
):
    async def scenario(engine):
        async with AsyncSession(engine) as session, session.begin():
            values = (
                await session.execute(
                    text(
                        "SELECT ST_AsEWKB(ST_GeomFromText(:line,4326)), ST_AsEWKB(ST_GeomFromText(:aoi,4326))"
                    ),
                    {
                        "line": line,
                        "aoi": aoi,
                    },
                )
            ).one()
            verdict = await inspect_spatial(
                session,
                geometry_ewkb=values[0],
                aoi_ewkb=values[1],
            )
            assert (
                verdict.valid,
                verdict.simple,
                verdict.no_zero_segments,
                verdict.aoi_covered,
            ) == (
                valid,
                simple,
                segments,
                covered,
            )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "line,aoi,srid,shape,aoi_valid",
    [
        (
            "LINESTRING(0 0,1 1)",
            SQUARE,
            3857,
            False,
            False,
        ),
        (
            "LINESTRING Z(0 0 0,1 1 0)",
            SQUARE,
            4326,
            False,
            True,
        ),
        (
            "LINESTRING(0 0,181 1)",
            SQUARE,
            4326,
            False,
            True,
        ),
        (
            "LINESTRING(0 0,1 1)",
            "POLYGON((0 0,4 4,4 0,0 4,0 0))",
            4326,
            True,
            False,
        ),
    ],
)
def test_spatial_rejects_wrong_dimensions_srid_range_and_invalid_aoi(
    line,
    aoi,
    srid,
    shape,
    aoi_valid,
):
    async def scenario(engine):
        async with AsyncSession(engine) as session, session.begin():
            values = (
                await session.execute(
                    text(
                        "SELECT ST_AsEWKB(ST_GeomFromText(:line,:srid)),ST_AsEWKB(ST_GeomFromText(:aoi,:srid))"
                    ),
                    {
                        "line": line,
                        "aoi": aoi,
                        "srid": srid,
                    },
                )
            ).one()
            verdict = await inspect_spatial(
                session,
                geometry_ewkb=values[0],
                aoi_ewkb=values[1],
            )
            assert verdict.shape_ok is shape
            assert verdict.aoi_valid is aoi_valid
            assert verdict.aoi_covered is False
            assert await session.scalar(text("SELECT 1")) == 1

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "kind,expected",
    [
        (
            "zero",
            "GEOMETRY_INVALID",
        ),
        (
            "outside",
            "GEOMETRY_OUTSIDE_AOI",
        ),
        (
            "other",
            "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED",
        ),
    ],
)
def test_candidate_rejection_leaves_transaction_usable(
    kind,
    expected,
):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            if kind == "other":
                await connection.execute(
                    text(
                        """
                        UPDATE work_order.edit_version_features
                        SET
                            operation = 'updated',
                            geometry = ST_GeomFromText('POINT(0 0)',4326)
                        WHERE edit_version_id = :edit_version_id
                            AND feature_id = :junction_id
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
            middle = (
                (
                    baseline.coordinates[0][0] + Decimal("0.00000001"),
                    baseline.coordinates[0][1],
                )
                if kind == "zero"
                else (
                    Decimal("65.526"),
                    Decimal("44.9" if kind == "outside" else "44.821"),
                )
            )
            candidate = replace(
                baseline,
                coordinates=(
                    baseline.coordinates[0],
                    middle,
                    baseline.coordinates[-1],
                ),
            )
            prepared = repository.prepare_candidate(
                context,
                candidate,
            )
            result = await repository.validate_candidate(
                context,
                prepared,
            )
            assert result.code == expected
            assert await session.scalar(text("SELECT 1")) == 1
            current = await session.scalar(
                text(
                    """
                    SELECT ST_AsEWKB(geometry)
                    FROM work_order.edit_version_features
                    WHERE edit_version_id = :edit_version_id
                        AND feature_id = :feature_id
                    """
                ),
                ids,
            )
            assert current == context.current.geometry_ewkb

    run_committed_scenario(scenario)


def test_non_simple_current_is_context_invalid():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            # Baseline and current differ at one inner vertex; current overlaps itself.
            await connection.execute(
                text(
                    """
                    UPDATE utility_network.default_state_features
                    SET geometry = ST_GeomFromText(
                        'LINESTRING(65.51 44.81,65.52 44.82,65.53 44.81,65.54 44.81)',
                        4326
                    )
                    WHERE default_state_id = :default_state_id
                        AND feature_id = :feature_id
                    """
                ),
                ids,
            )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET
                        operation = 'updated',
                        geometry = ST_GeomFromText(
                            'LINESTRING(65.51 44.81,65.535 44.81,65.53 44.81,65.54 44.81)',
                            4326
                        )
                    WHERE edit_version_id = :edit_version_id
                        AND feature_id = :feature_id
                    """
                ),
                ids,
            )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            prepared = repository.prepare_candidate(
                context,
                decode_geometry(context.baseline.geometry_ewkb),
            )
            assert (
                await repository.validate_candidate(
                    context,
                    prepared,
                )
            ).code == "WORK_ORDER_CONTEXT_INVALID"

    run_committed_scenario(scenario)
