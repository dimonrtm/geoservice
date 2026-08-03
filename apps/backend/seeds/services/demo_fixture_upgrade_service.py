import logging
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from seeds.contracts.demo_fixture_upgrade import (
    DemoFixtureCopySource,
    DemoFixtureFeatureSnapshot,
    DemoFixtureGeometryUpdate,
    DemoFixtureHierarchy,
    DemoFixtureUpgradeError,
    DemoFixtureUpgradeResult,
)
from seeds.specs.seed_utility_dataset_specs import UTILITY_EDITABLE_LINE_SPEC
from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import (
    EditVersionOperationState,
)


logger = logging.getLogger(__name__)


class DemoFixtureUpgradeRepositoryPort(Protocol):
    async def load_hierarchy_for_update(self) -> DemoFixtureHierarchy: ...

    async def update_geometry(self, update: DemoFixtureGeometryUpdate) -> None: ...


class DemoFixtureUpgradeService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DemoFixtureUpgradeRepositoryPort,
    ) -> None:
        self._session = session
        self._repository = repository

    async def upgrade_demo_fixture(self) -> DemoFixtureUpgradeResult:
        async with self._session.begin():
            hierarchy = await self._repository.load_hierarchy_for_update()
            updates = self._plan_updates(hierarchy)
            for update in updates:
                await self._repository.update_geometry(update)
        return DemoFixtureUpgradeResult(updates=updates)

    @staticmethod
    def _plan_updates(
        hierarchy: DemoFixtureHierarchy,
    ) -> tuple[DemoFixtureGeometryUpdate, ...]:
        feeder, default, edit_features = DemoFixtureUpgradeService._require_hierarchy(hierarchy)
        DemoFixtureUpgradeService._validate_copy(
            feeder,
            DemoFixtureCopySource.FEEDER,
        )
        DemoFixtureUpgradeService._validate_copy(
            default,
            DemoFixtureCopySource.DEFAULT_STATE,
        )
        for edit_feature in edit_features:
            DemoFixtureUpgradeService._validate_copy(
                edit_feature,
                DemoFixtureCopySource.EDIT_VERSION,
            )

        updates: list[DemoFixtureGeometryUpdate] = []

        feeder_target = feeder.geometry_wkt
        if feeder.vertex_count == 2:
            feeder_target = UTILITY_EDITABLE_LINE_SPEC.geometry_wkt
            updates.append(
                DemoFixtureGeometryUpdate(
                    source=DemoFixtureCopySource.FEEDER,
                    owner_id=feeder.owner_id,
                    geometry_wkt=feeder_target,
                )
            )

        default_target = default.geometry_wkt
        if default.vertex_count == 2:
            default_target = feeder_target
            updates.append(
                DemoFixtureGeometryUpdate(
                    source=DemoFixtureCopySource.DEFAULT_STATE,
                    owner_id=default.owner_id,
                    geometry_wkt=default_target,
                )
            )

        for edit_feature in edit_features:
            if edit_feature.vertex_count == 2:
                updates.append(
                    DemoFixtureGeometryUpdate(
                        source=DemoFixtureCopySource.EDIT_VERSION,
                        owner_id=edit_feature.owner_id,
                        geometry_wkt=default_target,
                    )
                )

        return tuple(updates)

    @staticmethod
    def _require_hierarchy(
        hierarchy: DemoFixtureHierarchy,
    ) -> tuple[
        DemoFixtureFeatureSnapshot,
        DemoFixtureFeatureSnapshot,
        tuple[DemoFixtureFeatureSnapshot, ...],
    ]:
        required_values = (
            ("feeder", hierarchy.feeder_id),
            ("feeder copy", hierarchy.feeder_feature),
            ("work order", hierarchy.work_order_id),
            ("default state", hierarchy.default_state_id),
            ("default state copy", hierarchy.default_feature),
        )
        for label, value in required_values:
            if value is None:
                raise DemoFixtureUpgradeError(
                    f"L-003: отсутствует обязательный demo fixture node: {label}."
                )

        edit_features: list[DemoFixtureFeatureSnapshot] = []
        for edit_version in sorted(
            hierarchy.edit_versions,
            key=lambda item: item.edit_version_id,
        ):
            if edit_version.default_state_id != hierarchy.default_state_id:
                raise DemoFixtureUpgradeError(
                    "L-003: edit_version copy имеет неверный default_state_id: "
                    f"owner={edit_version.edit_version_id}, "
                    f"actual={edit_version.default_state_id}, "
                    f"expected={hierarchy.default_state_id}."
                )
            if edit_version.feature is None:
                raise DemoFixtureUpgradeError(
                    "L-003: отсутствует обязательная edit_version copy "
                    f"owner={edit_version.edit_version_id}."
                )
            edit_features.append(edit_version.feature)

        return (
            hierarchy.feeder_feature,
            hierarchy.default_feature,
            tuple(edit_features),
        )

    @staticmethod
    def _validate_copy(
        snapshot: DemoFixtureFeatureSnapshot,
        source: DemoFixtureCopySource,
    ) -> None:
        error_prefix = f"L-003: недопустимая {source.value} copy owner={snapshot.owner_id}:"
        if snapshot.geometry_type.strip().upper() != "LINESTRING":
            raise DemoFixtureUpgradeError(
                f"{error_prefix} geometry_type={snapshot.geometry_type!r}."
            )
        if snapshot.vertex_count not in {2, 3}:
            raise DemoFixtureUpgradeError(
                f"{error_prefix} vertex_count={snapshot.vertex_count}; " "ожидалось 2 или 3."
            )
        if (
            source is DemoFixtureCopySource.EDIT_VERSION
            and snapshot.vertex_count == 2
            and snapshot.operation is not EditVersionOperationState.UNCHANGED
        ):
            operation = snapshot.operation.value if snapshot.operation is not None else None
            raise DemoFixtureUpgradeError(
                f"{error_prefix} двухвершинная copy имеет operation={operation!r}, "
                "ожидалось 'unchanged'."
            )


async def run_upgrade_demo_fixture() -> DemoFixtureUpgradeResult:
    from seeds.repositories.demo_fixture_upgrade_repository import (
        DemoFixtureUpgradeRepository,
    )
    from utility_service.infrastructure.postgresql.session import SessionFactory

    async with SessionFactory() as session:
        result = await DemoFixtureUpgradeService(
            session,
            DemoFixtureUpgradeRepository(session),
        ).upgrade_demo_fixture()
        logger.info(
            "Demo fixture upgrade завершён.",
            extra={
                "updated_copy_count": result.updated_copy_count,
                "updated_sources": [source.value for source in result.updated_sources],
            },
        )
        return result
