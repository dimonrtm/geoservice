from dataclasses import replace

import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.edit_geometry_repository_support import (
    read_context,
    seed_repository_context,
    snapshot_repository_state,
    prepare_change,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
)


def test_write_changes_only_target_and_revert_restores_exact_baseline():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            for table, key in (
                (
                    "utility_network.default_state_features",
                    "default_state_id",
                ),
                (
                    "work_order.edit_version_features",
                    "edit_version_id",
                ),
            ):
                await connection.execute(
                    text(
                        f"""
                        UPDATE {table}
                        SET geometry = ST_GeomFromText(
                            'LINESTRING(65.5200000499 44.8200000501,65.5250000499 44.8205000501,65.5300000501 44.8200000499)',
                            4326
                        )
                        WHERE {key} = :{key}
                            AND feature_id = :feature_id
                        """
                    ),
                    ids,
                )
            before = await snapshot_repository_state(
                connection,
                ids,
            )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            change = await prepare_change(
                repository,
                context,
            )
            result = await repository.write_current(change)
            assert result.changed and result.operation == "updated"
            assert session.in_transaction()
        async with engine.connect() as connection:
            after = await snapshot_repository_state(
                connection,
                ids,
            )
            for key in before.keys() - {"features"}:
                assert after[key] == before[key]
            for old, new in zip(
                before["features"],
                after["features"],
                strict=True,
            ):
                if old["feature_id"] == str(ids["feature_id"]):
                    assert new["operation"] == "updated"
                    assert old["geometry"] != new["geometry"]
                    assert {
                        k: v
                        for k, v in old.items()
                        if k
                        not in (
                            "geometry",
                            "operation",
                        )
                    } == {
                        k: v
                        for k, v in new.items()
                        if k
                        not in (
                            "geometry",
                            "operation",
                        )
                    }
                else:
                    assert old == new
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            result = await repository.write_current(
                await prepare_change(
                    repository,
                    context,
                    revert=True,
                )
            )
            assert result.changed and result.operation == "unchanged"
            assert result.after_ewkb == context.baseline.geometry_ewkb
        async with engine.connect() as connection:
            assert (
                await snapshot_repository_state(
                    connection,
                    ids,
                )
                == before
            )

    run_committed_scenario(scenario)


def test_noop_has_no_update_and_consumes_old_contexts():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
        updates = []

        def observe(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            if statement.lstrip().upper().startswith("UPDATE"):
                updates.append(statement)

        event.listen(
            engine.sync_engine,
            "before_cursor_execute",
            observe,
        )
        try:
            async with AsyncSession(engine) as session, session.begin():
                repository, context = await read_context(
                    session,
                    ids,
                )
                other = await repository.read_context(
                    context.root,
                    feature_id=ids["feature_id"],
                )
                change = await prepare_change(
                    repository,
                    context,
                    revert=True,
                )
                result = await repository.write_current(change)
                assert not result.changed
                assert updates == []
                with pytest.raises(RepositoryProtocolError):
                    await repository.write_current(change)
                with pytest.raises(RepositoryProtocolError):
                    repository.prepare_candidate(
                        other,
                        None,
                    )
                fresh = await repository.read_context(
                    context.root,
                    feature_id=ids["feature_id"],
                )
                assert (
                    await prepare_change(
                        repository,
                        fresh,
                    )
                ).is_noop is False
        finally:
            event.remove(
                engine.sync_engine,
                "before_cursor_execute",
                observe,
            )

    run_committed_scenario(scenario)


def test_write_rollback_and_provenance():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            before = await snapshot_repository_state(
                connection,
                ids,
            )
        async with AsyncSession(engine) as session:
            with pytest.raises(
                RuntimeError,
                match="injected",
            ):
                async with session.begin():
                    repository, context = await read_context(
                        session,
                        ids,
                    )
                    change = await prepare_change(
                        repository,
                        context,
                    )
                    with pytest.raises(RepositoryProtocolError):
                        await repository.write_current(
                            replace(
                                change,
                                after_ewkb=b"other",
                            )
                        )
                    async with AsyncSession(engine) as second, second.begin():
                        from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
                            EditVersionRepository,
                        )

                        with pytest.raises(RepositoryProtocolError):
                            await EditVersionRepository(second).write_current(change)
                    await repository.write_current(change)
                    async with engine.connect() as observer:
                        assert (
                            await snapshot_repository_state(
                                observer,
                                ids,
                            )
                            == before
                        )
                    raise RuntimeError("injected")
            async with session.begin():
                with pytest.raises(RepositoryProtocolError):
                    await repository.write_current(change)
        async with engine.connect() as connection:
            assert (
                await snapshot_repository_state(
                    connection,
                    ids,
                )
                == before
            )

    run_committed_scenario(scenario)


def test_finished_savepoint_invalidates_locked_context():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            nested = await session.begin_nested()
            await nested.rollback()
            with pytest.raises(RepositoryProtocolError):
                await repository.read_context(
                    context.root,
                    feature_id=ids["feature_id"],
                )

    run_committed_scenario(scenario)


def test_signed_zero_noop_keeps_current_bytes_and_revert_restores_baseline():
    from decimal import Decimal
    from utility_service.domain_services.edit_geometry.types import GeometryValue
    from utility_service.infrastructure.postgresql.geometry_codec import (
        encode_geometry,
        decode_geometry,
    )

    async def scenario(engine):
        baseline = GeometryValue(
            "LineString",
            (
                (
                    Decimal("-0.0"),
                    Decimal("0"),
                ),
                (
                    Decimal("1.0000000499"),
                    Decimal("1"),
                ),
                (
                    Decimal("2"),
                    Decimal("0"),
                ),
            ),
        )
        current = replace(
            baseline,
            coordinates=(
                (
                    Decimal("0.0"),
                    Decimal("0"),
                ),
                *baseline.coordinates[1:],
            ),
        )
        baseline_bytes, current_bytes = encode_geometry(baseline), encode_geometry(
            current,
        )
        assert baseline_bytes != current_bytes
        async with engine.begin() as setup:
            ids = await seed_repository_context(setup)
            await setup.execute(
                text(
                    "UPDATE work_order.aois SET geometry=ST_GeomFromText('POLYGON((-1 -1,3 -1,3 3,-1 3,-1 -1))',4326) WHERE id=:aoi_id"
                ),
                ids,
            )
            await setup.execute(
                text(
                    """
                    UPDATE utility_network.default_state_features
                    SET geometry = ST_GeomFromEWKB(:g)
                    WHERE default_state_id = :default_state_id
                        AND feature_id = :feature_id
                    """
                ),
                {
                    **ids,
                    "g": baseline_bytes,
                },
            )
            await setup.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET geometry = ST_GeomFromEWKB(:g)
                    WHERE edit_version_id = :edit_version_id
                        AND feature_id = :feature_id
                    """
                ),
                {
                    **ids,
                    "g": current_bytes,
                },
            )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            change = await repository.validate_candidate(
                context,
                repository.prepare_candidate(
                    context,
                    baseline,
                ),
            )
            assert change.is_noop
            assert (await repository.write_current(change)).after_ewkb == current_bytes
            fresh = await repository.read_context(
                context.root,
                feature_id=ids["feature_id"],
            )
            moved = replace(
                baseline,
                coordinates=(
                    baseline.coordinates[0],
                    (
                        Decimal("1.2"),
                        Decimal("1"),
                    ),
                    baseline.coordinates[-1],
                ),
            )
            await repository.write_current(
                await repository.validate_candidate(
                    fresh,
                    repository.prepare_candidate(
                        fresh,
                        moved,
                    ),
                )
            )
            fresh = await repository.read_context(
                context.root,
                feature_id=ids["feature_id"],
            )
            result = await repository.write_current(
                await repository.validate_candidate(
                    fresh,
                    repository.prepare_candidate(
                        fresh,
                        decode_geometry(fresh.baseline.geometry_ewkb),
                    ),
                )
            )
            assert result.changed
            assert result.after_ewkb == baseline_bytes

    run_committed_scenario(scenario)


def test_successful_write_invalidates_other_prepared_context():
    async def scenario(engine):
        async with engine.begin() as setup:
            ids = await seed_repository_context(setup)
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            other = await repository.read_context(
                context.root,
                feature_id=ids["feature_id"],
            )
            first = await prepare_change(
                repository,
                context,
            )
            stale = await prepare_change(
                repository,
                other,
            )
            await repository.write_current(first)
            with pytest.raises(RepositoryProtocolError):
                await repository.write_current(stale)

    run_committed_scenario(scenario)
