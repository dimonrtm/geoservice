import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.specs.seed_utility_dataset_specs import UTILITY_DATASET_SPEC


class FakeSession:
    def __init__(self) -> None:
        self.begin_calls = 0

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        yield self


def test_seed_creates_complete_dataset_when_feeder_is_absent() -> None:
    session = FakeSession()
    repository = AsyncMock()
    repository.get_feeder_by_code.return_value = None
    repository.create_dataset.return_value = SimpleNamespace(
        id=UTILITY_DATASET_SPEC.feeder.id,
        code=UTILITY_DATASET_SPEC.feeder.code,
    )
    service = SeedUtilityDatasetService(session, repository)

    result = asyncio.run(service.ensure_utility_dataset())

    assert result.created is True
    assert result.feeder_id == UTILITY_DATASET_SPEC.feeder.id
    assert session.begin_calls == 1
    repository.create_dataset.assert_awaited_once_with(UTILITY_DATASET_SPEC)


def test_utility_dataset_spec_no_longer_contains_aoi() -> None:
    assert not hasattr(UTILITY_DATASET_SPEC, "aoi")


def test_seed_is_noop_when_feeder_already_exists() -> None:
    session = FakeSession()
    existing = SimpleNamespace(
        id=UTILITY_DATASET_SPEC.feeder.id,
        code=UTILITY_DATASET_SPEC.feeder.code,
    )
    repository = AsyncMock()
    repository.get_feeder_by_code.return_value = existing
    service = SeedUtilityDatasetService(session, repository)

    result = asyncio.run(service.ensure_utility_dataset())

    assert result.created is False
    assert result.feeder_id == existing.id
    repository.create_dataset.assert_not_awaited()
