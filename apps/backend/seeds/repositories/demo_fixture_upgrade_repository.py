from uuid import UUID

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from seeds.contracts.demo_fixture_upgrade import (
    DemoFixtureCopySource,
    DemoFixtureEditVersionSnapshot,
    DemoFixtureFeatureSnapshot,
    DemoFixtureGeometryUpdate,
    DemoFixtureHierarchy,
    DemoFixtureUpgradeError,
)
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_EDITABLE_LINE_ASSET_CODE,
    UTILITY_FEEDER_CODE,
)
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC
from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultState,
    DefaultStateFeature,
    Feeder,
    NetworkFeature,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionFeature,
    WorkOrder,
)


class DemoFixtureUpgradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_hierarchy_for_update(self) -> DemoFixtureHierarchy:
        feeder_id = await self._session.scalar(
            select(Feeder.id).where(Feeder.code == UTILITY_FEEDER_CODE).with_for_update()
        )
        feeder_feature = (
            await self._load_feeder_feature(feeder_id) if feeder_id is not None else None
        )

        work_order_id = await self._session.scalar(
            select(WorkOrder.id)
            .where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
            .with_for_update()
        )
        default_state_id = None
        default_feature = None
        edit_versions: tuple[DemoFixtureEditVersionSnapshot, ...] = ()
        if work_order_id is not None:
            default_state_id = await self._session.scalar(
                select(DefaultState.id)
                .where(DefaultState.work_order_id == work_order_id)
                .with_for_update()
            )
            if default_state_id is not None:
                default_feature = await self._load_default_state_feature(default_state_id)
            edit_versions = await self._load_edit_versions(work_order_id)

        return DemoFixtureHierarchy(
            feeder_id=feeder_id,
            feeder_feature=feeder_feature,
            work_order_id=work_order_id,
            default_state_id=default_state_id,
            default_feature=default_feature,
            edit_versions=edit_versions,
        )

    async def _load_feeder_feature(
        self,
        feeder_id: UUID,
    ) -> DemoFixtureFeatureSnapshot | None:
        row = (
            await self._session.execute(
                select(
                    NetworkFeature.feeder_id.label("owner_id"),
                    func.ST_AsText(NetworkFeature.geometry).label("geometry_wkt"),
                    func.GeometryType(NetworkFeature.geometry).label("geometry_type"),
                    func.ST_NPoints(NetworkFeature.geometry).label("vertex_count"),
                    NetworkFeature.version.label("network_version"),
                )
                .where(
                    NetworkFeature.feeder_id == feeder_id,
                    NetworkFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
                )
                .with_for_update()
            )
        ).one_or_none()
        if row is None:
            return None
        return DemoFixtureFeatureSnapshot(
            owner_id=row.owner_id,
            geometry_wkt=row.geometry_wkt,
            geometry_type=row.geometry_type,
            vertex_count=row.vertex_count,
            network_version=row.network_version,
        )

    async def _load_default_state_feature(
        self,
        default_state_id: UUID,
    ) -> DemoFixtureFeatureSnapshot | None:
        row = (
            await self._session.execute(
                select(
                    DefaultStateFeature.default_state_id.label("owner_id"),
                    func.ST_AsText(DefaultStateFeature.geometry).label("geometry_wkt"),
                    func.GeometryType(DefaultStateFeature.geometry).label("geometry_type"),
                    func.ST_NPoints(DefaultStateFeature.geometry).label("vertex_count"),
                    DefaultStateFeature.network_version.label("network_version"),
                )
                .where(
                    DefaultStateFeature.default_state_id == default_state_id,
                    DefaultStateFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
                )
                .with_for_update()
            )
        ).one_or_none()
        if row is None:
            return None
        return DemoFixtureFeatureSnapshot(
            owner_id=row.owner_id,
            geometry_wkt=row.geometry_wkt,
            geometry_type=row.geometry_type,
            vertex_count=row.vertex_count,
            network_version=row.network_version,
        )

    async def _load_edit_versions(
        self,
        work_order_id: UUID,
    ) -> tuple[DemoFixtureEditVersionSnapshot, ...]:
        edit_versions = tuple(
            (
                await self._session.execute(
                    select(EditVersion.id, EditVersion.default_state_id)
                    .where(EditVersion.work_order_id == work_order_id)
                    .order_by(EditVersion.id)
                    .with_for_update()
                )
            ).all()
        )
        snapshots: list[DemoFixtureEditVersionSnapshot] = []
        for edit_version_id, default_state_id in edit_versions:
            snapshots.append(
                DemoFixtureEditVersionSnapshot(
                    edit_version_id=edit_version_id,
                    default_state_id=default_state_id,
                    feature=await self._load_edit_version_feature(edit_version_id),
                )
            )
        return tuple(snapshots)

    async def _load_edit_version_feature(
        self,
        edit_version_id: UUID,
    ) -> DemoFixtureFeatureSnapshot | None:
        row = (
            await self._session.execute(
                select(
                    EditVersionFeature.edit_version_id.label("owner_id"),
                    func.ST_AsText(EditVersionFeature.geometry).label("geometry_wkt"),
                    func.GeometryType(EditVersionFeature.geometry).label("geometry_type"),
                    func.ST_NPoints(EditVersionFeature.geometry).label("vertex_count"),
                    EditVersionFeature.network_version.label("network_version"),
                    EditVersionFeature.operation,
                )
                .where(
                    EditVersionFeature.edit_version_id == edit_version_id,
                    EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
                )
                .with_for_update()
            )
        ).one_or_none()
        if row is None:
            return None
        return DemoFixtureFeatureSnapshot(
            owner_id=row.owner_id,
            geometry_wkt=row.geometry_wkt,
            geometry_type=row.geometry_type,
            vertex_count=row.vertex_count,
            network_version=row.network_version,
            operation=row.operation,
        )

    async def update_geometry(
        self,
        update_request: DemoFixtureGeometryUpdate,
    ) -> None:
        if update_request.source is DemoFixtureCopySource.FEEDER:
            model = NetworkFeature
            owner_column = NetworkFeature.feeder_id
        elif update_request.source is DemoFixtureCopySource.DEFAULT_STATE:
            model = DefaultStateFeature
            owner_column = DefaultStateFeature.default_state_id
        else:
            model = EditVersionFeature
            owner_column = EditVersionFeature.edit_version_id

        result = await self._session.execute(
            update(model)
            .where(
                owner_column == update_request.owner_id,
                model.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
            .values(
                geometry=WKTElement(
                    update_request.geometry_wkt,
                    srid=4326,
                )
            )
        )
        if result.rowcount != 1:
            raise DemoFixtureUpgradeError(
                f"L-003: update {update_request.source.value} copy "
                f"owner={update_request.owner_id} изменил rows={result.rowcount}, "
                "ожидалась ровно одна строка."
            )
