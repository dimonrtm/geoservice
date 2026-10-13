from pathlib import Path
from uuid import UUID

from sqlalchemy import Integer, String, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionStatus,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repository_rows.workspace import (
    WorkspaceAggregateRow,
    WorkspaceAoiRow,
    WorkspaceBaselineStateRow,
    WorkspaceDraftFeaturePairRow,
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
    edit_version_draft_revision=Integer(),
    edit_version_default_state_id=PGUUID(as_uuid=True),
    baseline_state_id=PGUUID(as_uuid=True),
    baseline_work_order_id=PGUUID(as_uuid=True),
    baseline_base_network_revision=Integer(),
    baseline_status=String(),
    draft_feature_pairs=JSONB(),
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
                draft_revision=row["edit_version_draft_revision"],
                default_state_id=row["edit_version_default_state_id"],
            ),
            aoi=(
                WorkspaceAoiRow(
                    id=row["aoi_id"],
                    name=row["aoi_name"],
                    description=row["aoi_description"],
                    geometry_data=row["aoi_geometry_data"],
                    extent=row["aoi_extent"],
                )
                if row["aoi_id"] is not None
                else None
            ),
            baseline_state=(
                WorkspaceBaselineStateRow(
                    id=row["baseline_state_id"],
                    work_order_id=row["baseline_work_order_id"],
                    base_network_revision=row["baseline_base_network_revision"],
                    status=row["baseline_status"],
                )
                if row["baseline_state_id"] is not None
                else None
            ),
            draft_feature_pairs=tuple(
                WorkspaceDraftFeaturePairRow(
                    **{
                        **pair,
                        "feature_id": UUID(pair["feature_id"]),
                    },
                )
                for pair in row["draft_feature_pairs"]
            ),
            features_data=row["features_data"],
            associations_data=row["associations_data"],
        )
