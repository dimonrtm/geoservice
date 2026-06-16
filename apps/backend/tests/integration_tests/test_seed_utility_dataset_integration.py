from dataclasses import replace

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
)
from tests.integration_tests.network_db_support import run_in_rollback_transaction


async def remove_canonical_dataset(session: AsyncSession) -> None:
    feeder_id = UTILITY_DATASET_SPEC.feeder.id
    await session.execute(
        delete(NetworkAssociation).where(NetworkAssociation.feeder_id == feeder_id)
    )
    await session.execute(delete(NetworkFeature).where(NetworkFeature.feeder_id == feeder_id))
    await session.execute(delete(Feeder).where(Feeder.id == feeder_id))
    await session.execute(delete(AOI).where(AOI.id == UTILITY_DATASET_SPEC.aoi.id))
    await session.commit()


def test_seed_persists_complete_valid_dataset() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_dataset(session)
        repository = SeedUtilityDatasetRepository(session)
        result = await SeedUtilityDatasetService(
            session,
            repository,
        ).ensure_utility_dataset()

        feature_count = await session.scalar(
            select(func.count(NetworkFeature.id)).where(
                NetworkFeature.feeder_id == result.feeder_id
            )
        )
        association_count = await session.scalar(
            select(func.count(NetworkAssociation.id)).where(
                NetworkAssociation.feeder_id == result.feeder_id
            )
        )
        aoi_count = await session.scalar(
            select(func.count(AOI.id)).where(AOI.id == UTILITY_DATASET_SPEC.aoi.id)
        )

        assert result.created is True
        assert feature_count == 19
        assert association_count == 9
        assert aoi_count == 1

    run_in_rollback_transaction(scenario)


def test_seed_rolls_back_everything_when_dataset_is_invalid() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_dataset(session)
        duplicate = replace(
            UTILITY_DATASET_SPEC.features[1],
            id=UTILITY_DATASET_SPEC.features[0].id,
        )
        invalid_spec = replace(
            UTILITY_DATASET_SPEC,
            features=(UTILITY_DATASET_SPEC.features[0], duplicate),
            associations=(),
        )
        repository = SeedUtilityDatasetRepository(session)

        with pytest.raises(IntegrityError):
            async with session.begin():
                await repository.create_dataset(invalid_spec)

        feeder = await session.scalar(select(Feeder).where(Feeder.code == UTILITY_FEEDER_CODE))
        assert feeder is None

    run_in_rollback_transaction(scenario)


def test_repeated_seed_preserves_existing_changes_and_extra_feature() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_dataset(session)
        repository = SeedUtilityDatasetRepository(session)
        service = SeedUtilityDatasetService(session, repository)
        first = await service.ensure_utility_dataset()

        feeder = await session.get(Feeder, first.feeder_id)
        feeder.name = "Измененное имя"
        existing_feature = await session.scalar(
            select(NetworkFeature).where(
                NetworkFeature.feeder_id == first.feeder_id,
                NetworkFeature.asset_code == "D-002",
            )
        )
        existing_feature.properties = {"status": "maintenance"}
        extra = NetworkFeature(
            feeder_id=first.feeder_id,
            asset_code="D-999",
            feature_type=existing_feature.feature_type,
            geometry=existing_feature.geometry,
            name="Дополнительное устройство",
            properties={"status": "temporary"},
        )
        session.add(extra)
        await session.commit()

        second = await service.ensure_utility_dataset()
        await session.refresh(feeder)
        await session.refresh(existing_feature)
        count = await session.scalar(
            select(func.count(NetworkFeature.id)).where(NetworkFeature.feeder_id == first.feeder_id)
        )

        assert second.created is False
        assert feeder.name == "Измененное имя"
        assert existing_feature.properties == {"status": "maintenance"}
        assert count == 20

    run_in_rollback_transaction(scenario)
