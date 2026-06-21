import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from seeds.services.seed_work_order_service import (
    SeedWorkOrderDependencyError,
    SeedWorkOrderService,
)
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_AOI_SPEC, SEED_WORK_ORDER_SPEC


class FakeSession:
    def __init__(self) -> None:
        self.begin_calls = 0

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        yield self


def dependency_objects() -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace]:
    user = SimpleNamespace(id="user-id", email=SEED_WORK_ORDER_SPEC.assignee_email)
    feeder = SimpleNamespace(id="feeder-id", code=SEED_WORK_ORDER_SPEC.feeder_code)
    aoi = SimpleNamespace(id=SEED_WORK_ORDER_AOI_SPEC.id, name=SEED_WORK_ORDER_AOI_SPEC.name)
    return user, feeder, aoi


def test_seed_creates_work_order_when_absent_and_dependencies_exist() -> None:
    session = FakeSession()
    user, feeder, aoi = dependency_objects()
    created = SimpleNamespace(id=SEED_WORK_ORDER_SPEC.id, code=SEED_WORK_ORDER_SPEC.code)
    work_order_repository = AsyncMock()
    work_order_repository.get_work_order_by_code.return_value = None
    work_order_repository.ensure_aoi.return_value = aoi
    work_order_repository.create_work_order.return_value = created
    work_order_repository.ensure_default_state_for_work_order.return_value = SimpleNamespace(
        id="default-state-id"
    )
    user_repository = AsyncMock()
    user_repository.get_by_email.return_value = user
    utility_dataset_repository = AsyncMock()
    utility_dataset_repository.get_feeder_by_code.return_value = feeder
    service = SeedWorkOrderService(
        session,
        work_order_repository,
        user_repository,
        utility_dataset_repository,
    )

    result = asyncio.run(service.ensure_work_order())

    assert result.created is True
    assert result.work_order_id == SEED_WORK_ORDER_SPEC.id
    assert session.begin_calls == 1
    user_repository.get_by_email.assert_awaited_once_with(SEED_WORK_ORDER_SPEC.assignee_email)
    utility_dataset_repository.get_feeder_by_code.assert_awaited_once_with(
        SEED_WORK_ORDER_SPEC.feeder_code
    )
    work_order_repository.ensure_aoi.assert_awaited_once_with()
    work_order_repository.create_work_order.assert_awaited_once_with(
        SEED_WORK_ORDER_SPEC,
        aoi_id=aoi.id,
        assignee_user_id=user.id,
        created_by_user_id=user.id,
    )
    work_order_repository.ensure_default_state_for_work_order.assert_awaited_once_with(
        work_order_id=created.id,
        feeder_id=feeder.id,
    )


def test_seed_is_noop_when_work_order_already_exists() -> None:
    session = FakeSession()
    _, feeder, aoi = dependency_objects()
    existing = SimpleNamespace(id=SEED_WORK_ORDER_SPEC.id, code=SEED_WORK_ORDER_SPEC.code)
    work_order_repository = AsyncMock()
    work_order_repository.get_work_order_by_code.return_value = existing
    work_order_repository.ensure_aoi.return_value = aoi
    work_order_repository.ensure_default_state_for_work_order.return_value = SimpleNamespace(
        id="default-state-id"
    )
    user_repository = AsyncMock()
    utility_dataset_repository = AsyncMock()
    utility_dataset_repository.get_feeder_by_code.return_value = feeder
    service = SeedWorkOrderService(
        session,
        work_order_repository,
        user_repository,
        utility_dataset_repository,
    )

    result = asyncio.run(service.ensure_work_order())

    assert result.created is False
    assert result.work_order_id == existing.id
    user_repository.get_by_email.assert_not_awaited()
    utility_dataset_repository.get_feeder_by_code.assert_awaited_once_with(
        SEED_WORK_ORDER_SPEC.feeder_code
    )
    work_order_repository.ensure_aoi.assert_awaited_once_with()
    work_order_repository.create_work_order.assert_not_awaited()
    work_order_repository.ensure_default_state_for_work_order.assert_awaited_once_with(
        work_order_id=existing.id,
        feeder_id=utility_dataset_repository.get_feeder_by_code.return_value.id,
    )


def test_seed_fails_with_clear_message_when_existing_work_order_feeder_is_missing() -> None:
    session = FakeSession()
    existing = SimpleNamespace(id=SEED_WORK_ORDER_SPEC.id, code=SEED_WORK_ORDER_SPEC.code)
    work_order_repository = AsyncMock()
    work_order_repository.get_work_order_by_code.return_value = existing
    user_repository = AsyncMock()
    utility_dataset_repository = AsyncMock()
    utility_dataset_repository.get_feeder_by_code.return_value = None
    service = SeedWorkOrderService(
        session,
        work_order_repository,
        user_repository,
        utility_dataset_repository,
    )

    with pytest.raises(SeedWorkOrderDependencyError) as exc_info:
        asyncio.run(service.ensure_work_order())

    assert str(exc_info.value) == (
        f"Не найден feeder для seed WorkOrder: {SEED_WORK_ORDER_SPEC.feeder_code}"
    )
    user_repository.get_by_email.assert_not_awaited()
    work_order_repository.ensure_aoi.assert_not_awaited()
    work_order_repository.create_work_order.assert_not_awaited()
    work_order_repository.ensure_default_state_for_work_order.assert_not_awaited()


@pytest.mark.parametrize(
    ("missing_dependency", "expected_message"),
    [
        (
            "user",
            f"Не найден assignee для seed WorkOrder: {SEED_WORK_ORDER_SPEC.assignee_email}",
        ),
        (
            "feeder",
            f"Не найден feeder для seed WorkOrder: {SEED_WORK_ORDER_SPEC.feeder_code}",
        ),
    ],
)
def test_seed_fails_when_required_dependency_is_missing(
    missing_dependency: str,
    expected_message: str,
) -> None:
    session = FakeSession()
    user, feeder, aoi = dependency_objects()
    work_order_repository = AsyncMock()
    work_order_repository.get_work_order_by_code.return_value = None
    work_order_repository.ensure_aoi.return_value = aoi
    work_order_repository.ensure_default_state_for_work_order.return_value = None
    user_repository = AsyncMock()
    user_repository.get_by_email.return_value = None if missing_dependency == "user" else user
    utility_dataset_repository = AsyncMock()
    utility_dataset_repository.get_feeder_by_code.return_value = (
        None if missing_dependency == "feeder" else feeder
    )
    service = SeedWorkOrderService(
        session,
        work_order_repository,
        user_repository,
        utility_dataset_repository,
    )

    with pytest.raises(SeedWorkOrderDependencyError) as exc_info:
        asyncio.run(service.ensure_work_order())

    assert expected_message in str(exc_info.value)
    work_order_repository.ensure_aoi.assert_not_awaited()
    work_order_repository.create_work_order.assert_not_awaited()
