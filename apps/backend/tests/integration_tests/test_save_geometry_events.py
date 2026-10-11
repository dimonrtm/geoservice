from dataclasses import replace
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import (
    BASELINE,
    MOVED,
    call_save,
    request,
    seed_save_context,
    snapshot_save_state,
)
from utility_service.infrastructure.postgresql.geometry_codec import encode_geometry
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    geometry_to_geojson,
)
from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.fingerprint import command_fingerprint
from utility_service.domain_services.edit_geometry.types import FingerprintContext
from utility_service.use_cases.schemas.edit_version.geometry_save_out import (
    build_geometry_save_payload,
)
from tests.integration_tests.edit_geometry_repository_support import read_context


def test_save_save_revert_event_chain_and_replay():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            before = await snapshot_save_state(
                connection,
                ids,
            )
        await call_save(
            engine,
            ids,
            request(BASELINE),
        )
        a = request()
        first = await call_save(
            engine,
            ids,
            a,
        )
        b_geometry = replace(
            MOVED,
            coordinates=(
                MOVED.coordinates[0],
                (Decimal("65.525"), Decimal("44.822")),
                MOVED.coordinates[2],
            ),
        )
        await call_save(
            engine,
            ids,
            request(
                b_geometry,
                "2",
            ),
        )
        await call_save(
            engine,
            ids,
            request(
                b_geometry,
                "3",
            ),
        )
        revert = request(
            BASELINE,
            "3",
        )
        cleared = await call_save(
            engine,
            ids,
            revert,
        )
        assert cleared.payload["operation"] == "unchanged"
        assert cleared.payload["hasPersistedChangeSet"] is False
        assert cleared.payload["basicValidation"] is None
        assert (
            await call_save(
                engine,
                ids,
                a,
            )
        ).payload == first.payload
        async with engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        text(
                            """
                            SELECT
                                *,
                                ST_AsEWKB(before_geometry) AS before_ewkb,
                                ST_AsEWKB(after_geometry) AS after_ewkb
                            FROM work_order.edit_version_change_events
                            WHERE edit_version_id = :edit_version_id
                            ORDER BY draft_revision_after
                            """
                        ),
                        ids,
                    )
                )
                .mappings()
                .all()
            )
            state = await snapshot_save_state(
                connection,
                ids,
            )
        assert len(rows) == 3
        assert [r["event_type"] for r in rows] == [
            "change_set_persisted",
            "change_set_persisted",
            "change_set_cleared",
        ]
        geometries = [BASELINE, MOVED, b_geometry, BASELINE]
        for index, row in enumerate(rows):
            assert row["draft_revision_before"] == index + 1
            assert row["draft_revision_after"] == index + 2
            assert bytes(row["before_ewkb"]) == encode_geometry(geometries[index])
            assert bytes(row["after_ewkb"]) == encode_geometry(geometries[index + 1])
            for key in (
                "work_order_id",
                "edit_version_id",
                "default_state_id",
                "feature_id",
                "actor_user_id",
            ):
                assert row[key] == ids[key]
        assert state["features"] == before["features"]
        assert state["baseline"] == before["baseline"]
        await call_save(
            engine,
            ids,
            request(
                MOVED,
                "4",
            ),
        )
        assert (
            await call_save(
                engine,
                ids,
                revert,
            )
        ).payload == cleared.payload
        async with engine.connect() as connection:
            final = await snapshot_save_state(
                connection,
                ids,
            )
        assert final["root"]["draft_revision"] == 5
        assert len(final["events"]) == 4

    run_committed_scenario(scenario)


def test_old_revision_starts_history_without_backfill():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_versions
                    SET draft_revision = 5
                    WHERE id = :edit_version_id
                    """
                ),
                ids,
            )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET geometry = ST_GeomFromEWKB(:geometry),
                        operation = 'updated'
                    WHERE edit_version_id = :edit_version_id
                        AND feature_id = :feature_id
                    """
                ),
                {
                    **ids,
                    "geometry": encode_geometry(MOVED),
                },
            )
        old = request(token="4")
        payload = build_geometry_save_payload(
            command_id=old.command_id,
            feature_id=ids["feature_id"],
            draft_revision=5,
            operation="updated",
            geometry=geometry_to_geojson(MOVED),
        )
        # Reconstruct Day 6's committed command without calling Day 7 Save or appending history.
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            baseline = decode_geometry(context.baseline.geometry_ewkb)
            fingerprint = command_fingerprint(
                FingerprintContext(
                    ids["work_order_id"],
                    ids["edit_version_id"],
                    ids["feature_id"],
                    ids["actor_user_id"],
                    ids["default_state_id"],
                    context.root.base_network_revision,
                    "4",
                ),
                baseline,
                context.root.policy,
                prepare_geometry(
                    MOVED,
                    baseline,
                    context.root.policy,
                ),
            )
            await repository.reserve_command(
                context.root,
                command_id=old.command_id,
                feature_id=ids["feature_id"],
                actor_id=ids["actor_user_id"],
                fingerprint=fingerprint,
            )
            await repository.complete_command(
                context.root,
                command_id=old.command_id,
                payload=payload,
            )
        async with engine.connect() as connection:
            before_replay = await snapshot_save_state(
                connection,
                ids,
            )
        assert (
            await call_save(
                engine,
                ids,
                old,
            )
        ).payload == payload
        async with engine.connect() as connection:
            assert (
                await snapshot_save_state(
                    connection,
                    ids,
                )
                == before_replay
            )
        await call_save(
            engine,
            ids,
            request(
                BASELINE,
                token="5",
            ),
        )
        async with engine.connect() as connection:
            state = await snapshot_save_state(
                connection,
                ids,
            )
        assert len(state["events"]) == 1
        assert state["events"][0]["draft_revision_before"] == 5
        assert state["events"][0]["draft_revision_after"] == 6
        assert state["events"][0]["command_id"] != old.command_id
        assert (
            await call_save(
                engine,
                ids,
                old,
            )
        ).payload == payload
        async with engine.connect() as connection:
            assert (
                await snapshot_save_state(
                    connection,
                    ids,
                )
                == state
            )

    run_committed_scenario(scenario)
