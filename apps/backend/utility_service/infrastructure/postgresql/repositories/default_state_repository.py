from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from geoalchemy2.elements import WKTElement
from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultStateStatus,
)
from utility_service.infrastructure.postgresql.models.utility_network.network_association import (
    AssociationType,
)
from utility_service.infrastructure.postgresql.models.utility_network.network_feature import (
    FeatureType,
)


DEFAULT_STATE_AGGREGATE_SQL_PATH = (
    Path(__file__).resolve().parents[1] / "sql" / "default_state_aggregate.sql"
)


@dataclass(frozen=True)
class DefaultStateCopy:
    id: UUID
    work_order_id: UUID
    network_state_id: UUID
    base_network_revision: int
    status: DefaultStateStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DefaultStateFeatureCopy:
    default_state_id: UUID
    feature_id: UUID
    asset_code: str
    feature_type: FeatureType
    geometry: WKTElement
    properties: dict[str, Any]
    network_version: int


@dataclass(frozen=True)
class DefaultStateAssociationCopy:
    default_state_id: UUID
    association_id: UUID
    association_type: AssociationType
    from_feature_id: UUID
    to_feature_id: UUID
    properties: dict[str, Any]
    network_version: int


@dataclass(frozen=True)
class DefaultStateAggregate:
    state: DefaultStateCopy
    features: list[DefaultStateFeatureCopy]
    associations: list[DefaultStateAssociationCopy]


DEFAULT_STATE_AGGREGATE_SQL = text(
    DEFAULT_STATE_AGGREGATE_SQL_PATH.read_text(encoding="utf-8")
).columns(
    id=PGUUID(as_uuid=True),
    work_order_id=PGUUID(as_uuid=True),
    network_state_id=PGUUID(as_uuid=True),
    base_network_revision=Integer(),
    status=String(),
    created_at=DateTime(timezone=True),
    updated_at=DateTime(timezone=True),
    features=JSONB(),
    associations=JSONB(),
)


class DefaultStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_aggregate_by_work_order_id(
        self, work_order_id: UUID
    ) -> DefaultStateAggregate | None:
        result = await self.session.execute(
            DEFAULT_STATE_AGGREGATE_SQL,
            {
                "work_order_id": work_order_id,
                "active_status": DefaultStateStatus.ACTIVE.value,
            },
        )
        row = result.mappings().one_or_none()
        if row is None:
            return None

        state = DefaultStateCopy(
            id=row["id"],
            work_order_id=row["work_order_id"],
            network_state_id=row["network_state_id"],
            base_network_revision=row["base_network_revision"],
            status=DefaultStateStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        features = [
            DefaultStateFeatureCopy(
                default_state_id=_as_uuid(feature["default_state_id"]),
                feature_id=_as_uuid(feature["feature_id"]),
                asset_code=feature["asset_code"],
                feature_type=FeatureType(feature["feature_type"]),
                geometry=WKTElement(feature["geometry_ewkt"], extended=True),
                properties=feature["properties"],
                network_version=feature["network_version"],
            )
            for feature in row["features"]
        ]
        associations = [
            DefaultStateAssociationCopy(
                default_state_id=_as_uuid(association["default_state_id"]),
                association_id=_as_uuid(association["association_id"]),
                association_type=AssociationType(association["association_type"]),
                from_feature_id=_as_uuid(association["from_feature_id"]),
                to_feature_id=_as_uuid(association["to_feature_id"]),
                properties=association["properties"],
                network_version=association["network_version"],
            )
            for association in row["associations"]
        ]
        return DefaultStateAggregate(
            state=state,
            features=features,
            associations=associations,
        )


def _as_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(value)
