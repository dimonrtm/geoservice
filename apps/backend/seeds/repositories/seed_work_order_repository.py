from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    NetworkAssociation,
    NetworkFeature,
    NetworkState,
)
from utility_service.infrastructure.postgresql.models.work_order import WorkOrder
from seeds.specs.seed_work_order_specs import SeedWorkOrderSpec


DEFAULT_NETWORK_STATE_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0501")


class SeedWorkOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_work_order_by_code(self, code: str) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.code == code))
        return result.scalars().one_or_none()

    async def create_work_order(
        self,
        spec: SeedWorkOrderSpec,
        *,
        assignee_user_id: UUID,
        created_by_user_id: UUID,
    ) -> WorkOrder:
        work_order = WorkOrder(
            id=spec.id,
            code=spec.code,
            title=spec.title,
            description=spec.description,
            status=spec.status,
            assignee_user_id=assignee_user_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(work_order)
        await self.session.flush()
        return work_order

    async def ensure_default_state_for_work_order(
        self,
        *,
        work_order_id: UUID,
        feeder_id: UUID,
    ) -> DefaultState:
        existing = await self.session.scalar(
            select(DefaultState).where(DefaultState.work_order_id == work_order_id)
        )
        if existing is not None:
            return existing

        network_state = await self.session.scalar(
            select(NetworkState).where(NetworkState.name == "default")
        )
        if network_state is None:
            network_state = NetworkState(
                id=DEFAULT_NETWORK_STATE_ID,
                name="default",
                current_revision=1,
            )
            self.session.add(network_state)
            await self.session.flush()

        default_state = DefaultState(
            work_order_id=work_order_id,
            network_state_id=network_state.id,
            base_network_revision=network_state.current_revision,
        )
        self.session.add(default_state)
        await self.session.flush()

        features = await self.session.scalars(
            select(NetworkFeature).where(NetworkFeature.feeder_id == feeder_id)
        )
        self.session.add_all(
            [
                DefaultStateFeature(
                    default_state_id=default_state.id,
                    feature_id=feature.id,
                    asset_code=feature.asset_code,
                    feature_type=feature.feature_type,
                    geometry=feature.geometry,
                    properties=dict(feature.properties),
                    network_version=feature.version,
                )
                for feature in features
            ]
        )
        await self.session.flush()

        associations = await self.session.scalars(
            select(NetworkAssociation).where(NetworkAssociation.feeder_id == feeder_id)
        )
        self.session.add_all(
            [
                DefaultStateAssociation(
                    default_state_id=default_state.id,
                    association_id=association.id,
                    association_type=association.association_type,
                    from_feature_id=association.from_feature_id,
                    to_feature_id=association.to_feature_id,
                    network_version=association.version,
                )
                for association in associations
            ]
        )
        await self.session.flush()
        return default_state
