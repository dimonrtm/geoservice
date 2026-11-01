from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from utility_service.infrastructure.postgresql.models.layer import Layer
from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.use_cases.domain.exceptions.version_mismatch_exception import (
    VersionMismatchException,
)
from utility_service.use_cases.schemas.feature.patch_feature_request import PatchFeatureRequest
from utility_service.use_cases.services.feature_service import FeatureService


ORIGINAL_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[[10, 10], [20, 10], [20, 20], [10, 10]]],
}
UPDATED_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[[10, 10], [25, 10], [25, 25], [10, 10]]],
}


async def seed_legacy_feature(engine):
    layer_id = uuid4()
    async with AsyncSession(engine) as session:
        async with session.begin():
            layer = Layer(
                id=layer_id,
                name=f"be02-{layer_id}",
                title="Проверка очистки свойств BE-02",
                geometry_type="Polygon",
                storage_table="feature_polygons",
            )
            session.add(layer)
            await session.flush()
            row = await LayerRepository(session).create_feature(
                layer, ORIGINAL_GEOMETRY, {"name": "Before"}
            )
            feature_id = row.id
    return layer_id, feature_id


async def read_feature(engine, layer_id, feature_id):
    async with AsyncSession(engine) as session:
        service = FeatureService(session, LayerRepository(session))
        return await service.get_feature(layer_id, feature_id)


@pytest.mark.parametrize("geometry", [None, UPDATED_GEOMETRY])
def test_legacy_patch_clear_properties_commits(geometry):
    async def scenario(engine):
        layer_id, feature_id = await seed_legacy_feature(engine)
        published_states = []

        async def observe_commit(published_layer_id, feature):
            persisted = await read_feature(engine, published_layer_id, feature.id)
            published_states.append(persisted)

        publisher = AsyncMock()
        publisher.publish_feature_updated.side_effect = observe_commit
        async with AsyncSession(engine) as session:
            service = FeatureService(session, LayerRepository(session), publisher)
            result = await service.update_feature(
                layer_id,
                feature_id,
                PatchFeatureRequest(version=1, geometry=geometry, properties={}),
            )

        persisted = await read_feature(engine, layer_id, feature_id)
        expected_geometry = ORIGINAL_GEOMETRY if geometry is None else UPDATED_GEOMETRY
        assert result.id == feature_id
        assert result.properties == {}
        assert result.version == 2
        assert result.geometry.model_dump(mode="json") == expected_geometry
        assert persisted == result
        publisher.publish_feature_updated.assert_awaited_once_with(layer_id, result)
        # Assert outside the callback: the service suppresses publisher exceptions.
        assert published_states == [result]

    run_committed_scenario(scenario)


@pytest.mark.parametrize("geometry", [None, UPDATED_GEOMETRY])
def test_legacy_patch_stale_version_keeps_state(geometry):
    async def scenario(engine):
        layer_id, feature_id = await seed_legacy_feature(engine)
        # Advance the real row to version 2; the request below still carries version 1.
        async with AsyncSession(engine) as session:
            async with session.begin():
                repository = LayerRepository(session)
                layer = await repository.get_layer_by_id(layer_id)
                row, _ = await repository.update_feature_if_version_matches(
                    layer, feature_id, None, {"name": "Before"}, 1
                )
                assert row.version == 2

        publisher = AsyncMock()
        async with AsyncSession(engine) as session:
            service = FeatureService(session, LayerRepository(session), publisher)
            with pytest.raises(VersionMismatchException):
                await service.update_feature(
                    layer_id,
                    feature_id,
                    PatchFeatureRequest(version=1, geometry=geometry, properties={}),
                )

        persisted = await read_feature(engine, layer_id, feature_id)
        assert persisted.properties == {"name": "Before"}
        assert persisted.version == 2
        assert persisted.geometry.model_dump(mode="json") == ORIGINAL_GEOMETRY
        publisher.publish_feature_updated.assert_not_awaited()

    run_committed_scenario(scenario)


@pytest.mark.parametrize("geometry", [None, UPDATED_GEOMETRY])
def test_legacy_patch_failure_after_update_rolls_back(geometry, monkeypatch):
    async def scenario(engine):
        layer_id, feature_id = await seed_legacy_feature(engine)
        publisher = AsyncMock()
        async with AsyncSession(engine) as session:
            repository = LayerRepository(session)
            real_update = repository.update_feature_if_version_matches

            async def update_then_fail(*args, **kwargs):
                row, _ = await real_update(*args, **kwargs)
                assert row.version == 2
                # Prove the update ran before the injected failure, in this transaction.
                current = await repository.get_feature(args[0], feature_id)
                assert current.properties == {}
                expected = ORIGINAL_GEOMETRY if geometry is None else UPDATED_GEOMETRY
                assert current.geometry_data == expected
                raise RuntimeError("BE-02: тестовый сбой после UPDATE")

            monkeypatch.setattr(repository, "update_feature_if_version_matches", update_then_fail)
            service = FeatureService(session, repository, publisher)
            with pytest.raises(RuntimeError, match="BE-02: тестовый сбой после UPDATE"):
                await service.update_feature(
                    layer_id,
                    feature_id,
                    PatchFeatureRequest(version=1, geometry=geometry, properties={}),
                )

        persisted = await read_feature(engine, layer_id, feature_id)
        assert persisted.properties == {"name": "Before"}
        assert persisted.version == 1
        assert persisted.geometry.model_dump(mode="json") == ORIGINAL_GEOMETRY
        publisher.publish_feature_updated.assert_not_awaited()

    run_committed_scenario(scenario)
