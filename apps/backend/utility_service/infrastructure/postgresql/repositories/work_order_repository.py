from pathlib import Path
from uuid import UUID

from sqlalchemy import Integer, String, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    geometry_to_geojson,
)

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
    WorkspaceAoiRow,
    WorkspaceEditVersionRow,
    WorkspaceWorkOrderRow,
)


WORKSPACE_AGGREGATE_SQL_PATH = (
    Path(__file__).resolve().parents[1] / "sql" / "workspace_aggregate.sql"
)

WORKSPACE_AGGREGATE_SQL = text(WORKSPACE_AGGREGATE_SQL_PATH.read_text(encoding="utf-8")).columns(
    work_order_id=PGUUID(as_uuid=True),
    work_order_code=String(),
    work_order_title=String(),
    work_order_description=String(),
    work_order_status=String(),
    work_order_assignee_user_id=PGUUID(as_uuid=True),
    edit_version_id=PGUUID(as_uuid=True),
    edit_version_status=String(),
    edit_version_base_network_revision=Integer(),
    aoi_id=PGUUID(as_uuid=True),
    aoi_name=String(),
    aoi_description=String(),
    aoi_geometry_data=JSONB(),
    aoi_extent=JSONB(),
    features_data=JSONB(),
    associations_data=JSONB(),
)


class WorkOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, work_order_id: UUID) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
        return result.scalars().one_or_none()

    async def get_by_id_for_update(self, work_order_id: UUID) -> WorkOrder | None:
        result = await self.session.execute(
            select(WorkOrder).where(WorkOrder.id == work_order_id).with_for_update()
        )
        return result.scalars().one_or_none()

    async def get_by_code(self, code: str) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.code == code))
        return result.scalars().one_or_none()

    async def list_assigned_to_user(self, user_id: UUID) -> list[WorkOrder]:
        result = await self.session.execute(
            select(WorkOrder)
            .where(WorkOrder.assignee_user_id == user_id)
            .order_by(WorkOrder.updated_at.desc(), WorkOrder.code.asc())
        )
        return list(result.scalars().all())

    async def save(self, work_order: WorkOrder) -> None:
        self.session.add(work_order)
        await self.session.flush()

    async def get_workspace_aggregate(
        self,
        *,
        work_order_id: UUID,
        edit_version_id: UUID,
    ) -> WorkspaceAggregateRow | None:
        result = await self.session.execute(
            WORKSPACE_AGGREGATE_SQL,
            {
                "work_order_id": work_order_id,
                "edit_version_id": edit_version_id,
            },
        )
        row = result.mappings().one_or_none()
        if row is None:
            return None
        return WorkspaceAggregateRow(
            work_order=WorkspaceWorkOrderRow(
                id=row["work_order_id"],
                code=row["work_order_code"],
                title=row["work_order_title"],
                description=row["work_order_description"],
                status=WorkOrderStatus(row["work_order_status"]),
                assignee_user_id=row["work_order_assignee_user_id"],
            ),
            edit_version=WorkspaceEditVersionRow(
                id=row["edit_version_id"],
                status=EditVersionStatus(row["edit_version_status"]),
                base_network_revision=row["edit_version_base_network_revision"],
            ),
            aoi=WorkspaceAoiRow(
                id=row["aoi_id"],
                name=row["aoi_name"],
                description=row["aoi_description"],
                geometry_data=row["aoi_geometry_data"],
                extent=row["aoi_extent"],
            ),
            features_data=[
                {
                    **{key: value for key, value in feature.items() if key != "geometry_ewkb"},
                    "geometry_data": geometry_to_geojson(
                        decode_geometry(bytes.fromhex(feature["geometry_ewkb"]))
                    ),
                }
                for feature in row["features_data"]
            ],
            associations_data=row["associations_data"],
        )
