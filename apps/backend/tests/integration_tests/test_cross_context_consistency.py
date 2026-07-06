from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.repositories.seed_work_order_repository import SeedWorkOrderRepository
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.services.seed_work_order_service import SeedWorkOrderService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
from seeds.specs.seed_utility_dataset_specs import UTILITY_DATASET_SPEC
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC
from tests.integration_tests.network_db_support import run_in_rollback_transaction
from utility_service.infrastructure.postgresql.consistency import (
    CrossContextConsistencyChecker,
    CrossContextConsistencyIssue,
    CrossContextConsistencyReport,
)
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    DefaultStateStatus,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    AOI,
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    WorkOrder,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import (
    UserRepository,
)
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.services.edit_version_service import EditVersionService


async def remove_cross_context_seed_state(session: AsyncSession) -> None:
    await session.execute(delete(EditVersionAssociation))
    await session.execute(delete(EditVersionFeature))
    await session.execute(delete(EditVersion))
    await session.execute(delete(DefaultStateAssociation))
    await session.execute(delete(DefaultStateFeature))
    await session.execute(delete(DefaultState))
    await session.execute(delete(WorkOrder))
    await session.execute(delete(AOI))
    await session.execute(
        delete(NetworkAssociation).where(
            NetworkAssociation.feeder_id == UTILITY_DATASET_SPEC.feeder.id
        )
    )
    await session.execute(
        delete(NetworkFeature).where(NetworkFeature.feeder_id == UTILITY_DATASET_SPEC.feeder.id)
    )
    await session.execute(delete(Feeder).where(Feeder.id == UTILITY_DATASET_SPEC.feeder.id))
    await session.execute(
        delete(User).where(User.email.in_([spec.email for spec in SEED_DEMO_USER_SPECS]))
    )
    await session.commit()


async def ensure_seed_chain(session: AsyncSession) -> None:
    await SeedDemoUserService(
        session,
        SeedUserRepository(session),
    ).ensure_demo_users()
    await SeedUtilityDatasetService(
        session,
        SeedUtilityDatasetRepository(session),
    ).ensure_utility_dataset()
    await SeedWorkOrderService(
        session,
        SeedWorkOrderRepository(session),
        SeedUserRepository(session),
        SeedUtilityDatasetRepository(session),
    ).ensure_work_order()


async def ensure_clean_seed_chain(session: AsyncSession) -> None:
    await remove_cross_context_seed_state(session)
    await ensure_seed_chain(session)


async def ensure_open_seed_edit_version(session: AsyncSession) -> EditVersion:
    await ensure_clean_seed_chain(session)
    assignee_id = next(
        spec.id
        for spec in SEED_DEMO_USER_SPECS
        if spec.email == SEED_WORK_ORDER_SPEC.assignee_email
    )
    result = await EditVersionService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
        DefaultStateRepository(session),
    ).open_for_work_order(SEED_WORK_ORDER_SPEC.id, assignee_id)
    return result.edit_version


def issue_by_name(
    report: CrossContextConsistencyReport,
    check_name: str,
) -> CrossContextConsistencyIssue:
    matching = [issue for issue in report.issues if issue.check_name == check_name]
    assert len(matching) == 1, report.issues
    return matching[0]


def test_seeded_database_has_consistent_cross_context_links() -> None:
    async def scenario(session: AsyncSession) -> None:
        await ensure_clean_seed_chain(session)

        report = await CrossContextConsistencyChecker(session).run()

        assert report.ok is True
        assert report.error_count == 0
        assert report.warning_count == 0
        assert report.issues == []

    run_in_rollback_transaction(scenario)


def test_checker_reports_orphan_edit_version_owner_user() -> None:
    async def scenario(session: AsyncSession) -> None:
        edit_version = await ensure_open_seed_edit_version(session)
        missing_user_id = uuid4()
        edit_version.owner_user_id = missing_user_id
        await session.flush()

        report = await CrossContextConsistencyChecker(session).run(
            ["edit_version_owner_user_exists"]
        )

        assert report.ok is False
        issue = issue_by_name(report, "edit_version_owner_user_exists")
        assert issue.count == 1
        assert issue.sample_rows == [
            {
                "editVersionId": str(edit_version.id),
                "ownerUserId": str(missing_user_id),
            }
        ]

    run_in_rollback_transaction(scenario)


def test_checker_reports_edit_version_default_state_work_order_mismatch() -> None:
    async def scenario(session: AsyncSession) -> None:
        edit_version = await ensure_open_seed_edit_version(session)
        original_default_state = await session.scalar(
            select(DefaultState).where(DefaultState.id == edit_version.default_state_id)
        )
        assert original_default_state is not None
        mismatched_work_order_id = uuid4()
        mismatched_default_state = DefaultState(
            work_order_id=mismatched_work_order_id,
            network_state_id=original_default_state.network_state_id,
            base_network_revision=original_default_state.base_network_revision,
            status=DefaultStateStatus.ACTIVE,
        )
        session.add(mismatched_default_state)
        await session.flush()
        edit_version.default_state_id = mismatched_default_state.id
        await session.flush()

        report = await CrossContextConsistencyChecker(session).run(
            ["edit_version_default_state_matches_work_order"]
        )

        assert report.ok is False
        issue = issue_by_name(report, "edit_version_default_state_matches_work_order")
        assert issue.count == 1
        assert issue.sample_rows == [
            {
                "editVersionId": str(edit_version.id),
                "editVersionWorkOrderId": str(edit_version.work_order_id),
                "defaultStateId": str(mismatched_default_state.id),
                "defaultStateWorkOrderId": str(mismatched_work_order_id),
            }
        ]

    run_in_rollback_transaction(scenario)
