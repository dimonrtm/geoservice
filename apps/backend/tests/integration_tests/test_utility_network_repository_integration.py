import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    Feeder,
    FeatureType,
    NetworkFeature,
)
from utility_service.infrastructure.postgresql.models.work_order import AOI
from utility_service.infrastructure.postgresql.repositories.utility_network_repository import (
    UtilityNetworkRepository,
)
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_FEEDER_CODE,
    UTILITY_FEEDER_ID,
)
from tests.integration_tests.network_db_support import run_in_rollback_transaction


async def ensure_dataset(session: AsyncSession) -> None:
    await SeedUtilityDatasetService(
        session,
        SeedUtilityDatasetRepository(session),
    ).ensure_utility_dataset()


def test_repository_loads_ordered_feeder_aggregate() -> None:
    async def scenario(session: AsyncSession) -> None:
        await ensure_dataset(session)
        repository = UtilityNetworkRepository(session)

        aggregate = await repository.get_feeder_aggregate(UTILITY_FEEDER_ID)

        assert aggregate is not None
        assert aggregate.code == UTILITY_FEEDER_CODE
        assert [item["asset_code"] for item in aggregate.features_data] == sorted(
            item["asset_code"] for item in aggregate.features_data
        )
        assert len(aggregate.features_data) == 19
        assert len(aggregate.associations_data) == 9
        assert not hasattr(aggregate, "aois_data")

    run_in_rollback_transaction(scenario)


def repository_returns_each_intersecting_aoi_once_legacy_coverage() -> None:
    async def scenario(session: AsyncSession) -> None:
        await ensure_dataset(session)
        session.add_all(
            [
                AOI(
                    name="Район-2",
                    geometry=WKTElement(
                        "POLYGON ((65.519 44.819, 65.521 44.819, "
                        "65.521 44.821, 65.519 44.821, 65.519 44.819))",
                        srid=4326,
                    ),
                ),
                AOI(
                    name="Внешний район",
                    geometry=WKTElement(
                        "POLYGON ((66 45, 66.1 45, 66.1 45.1, 66 45.1, 66 45))",
                        srid=4326,
                    ),
                ),
            ]
        )
        await session.flush()

        aggregate = await UtilityNetworkRepository(session).get_feeder_aggregate(UTILITY_FEEDER_ID)

        assert aggregate is not None
        assert not hasattr(aggregate, "aois_data")

    run_in_rollback_transaction(scenario)


def test_repository_returns_empty_collections_and_none_for_unknown_feeder() -> None:
    async def scenario(session: AsyncSession) -> None:
        outside_feeder = Feeder(code="outside-feeder", name="Внешний фидер")
        session.add(outside_feeder)
        await session.flush()
        session.add(
            NetworkFeature(
                feeder_id=outside_feeder.id,
                asset_code="J-OUT",
                feature_type=FeatureType.JUNCTION,
                geometry=WKTElement("POINT (66.5 45.5)", srid=4326),
                name="Внешний узел",
            )
        )
        await session.flush()
        repository = UtilityNetworkRepository(session)

        aggregate = await repository.get_feeder_aggregate(outside_feeder.id)

        assert aggregate is not None
        assert len(aggregate.features_data) == 1
        assert aggregate.associations_data == []
        assert not hasattr(aggregate, "aois_data")
        assert await repository.get_feeder_aggregate(uuid4()) is None

    run_in_rollback_transaction(scenario)


def test_repository_executes_one_statement() -> None:
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.one_or_none.return_value = None
    session.execute.return_value = result_mock
    repository = UtilityNetworkRepository(session)

    result = asyncio.run(repository.get_feeder_aggregate(uuid4()))

    assert result is None
    session.execute.assert_awaited_once()
