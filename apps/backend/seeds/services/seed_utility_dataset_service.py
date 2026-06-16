import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeedUtilityDatasetResult:
    feeder_id: UUID
    created: bool


class SeedUtilityDatasetService:
    def __init__(
        self,
        session: AsyncSession,
        repository: SeedUtilityDatasetRepository,
    ):
        self.session = session
        self.repository = repository

    async def ensure_utility_dataset(self) -> SeedUtilityDatasetResult:
        async with self.session.begin():
            existing = await self.repository.get_feeder_by_code(UTILITY_FEEDER_CODE)
            if existing is not None:
                logger.info(
                    "Utility dataset уже существует; startup seed не изменяет агрегат.",
                    extra={
                        "feeder_id": str(existing.id),
                        "feeder_code": existing.code,
                    },
                )
                return SeedUtilityDatasetResult(
                    feeder_id=existing.id,
                    created=False,
                )

            feeder = await self.repository.create_dataset(UTILITY_DATASET_SPEC)
            logger.info(
                "Utility dataset создан.",
                extra={
                    "feeder_id": str(feeder.id),
                    "feeder_code": feeder.code,
                },
            )
            return SeedUtilityDatasetResult(feeder_id=feeder.id, created=True)


async def run_seed_utility_dataset() -> SeedUtilityDatasetResult:
    from utility_service.infrastructure.postgresql.session import SessionFactory

    async with SessionFactory() as session:
        service = SeedUtilityDatasetService(
            session,
            SeedUtilityDatasetRepository(session),
        )
        return await service.ensure_utility_dataset()
