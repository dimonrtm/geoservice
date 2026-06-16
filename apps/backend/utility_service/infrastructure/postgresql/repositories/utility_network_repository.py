from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import cast, func, literal, select
from sqlalchemy.dialects.postgresql import JSONB, aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)


@dataclass(frozen=True)
class FeederAggregateRow:
    id: UUID
    code: str
    name: str
    is_active: bool
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]
    aois_data: list[dict[str, Any]]


class UtilityNetworkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feeder_aggregate(
        self,
        feeder_id: UUID,
    ) -> FeederAggregateRow | None:
        empty_array = cast(literal("[]"), JSONB)

        feature_json = func.jsonb_build_object(
            "id",
            NetworkFeature.id,
            "asset_code",
            NetworkFeature.asset_code,
            "feature_type",
            NetworkFeature.feature_type,
            "name",
            NetworkFeature.name,
            "description",
            NetworkFeature.description,
            "properties",
            NetworkFeature.properties,
            "version",
            NetworkFeature.version,
            "geometry_data",
            cast(func.ST_AsGeoJSON(NetworkFeature.geometry), JSONB),
        )
        features_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            feature_json,
                            NetworkFeature.asset_code,
                            NetworkFeature.id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(NetworkFeature.feeder_id == Feeder.id)
            .correlate(Feeder)
            .scalar_subquery()
        )

        association_json = func.jsonb_build_object(
            "id",
            NetworkAssociation.id,
            "from_feature_id",
            NetworkAssociation.from_feature_id,
            "to_feature_id",
            NetworkAssociation.to_feature_id,
            "association_type",
            NetworkAssociation.association_type,
            "version",
            NetworkAssociation.version,
        )
        associations_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            association_json,
                            NetworkAssociation.from_feature_id,
                            NetworkAssociation.to_feature_id,
                            NetworkAssociation.association_type,
                            NetworkAssociation.id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(NetworkAssociation.feeder_id == Feeder.id)
            .correlate(Feeder)
            .scalar_subquery()
        )

        intersecting_feature_exists = (
            select(literal(1))
            .select_from(NetworkFeature)
            .where(
                NetworkFeature.feeder_id == Feeder.id,
                func.ST_Intersects(AOI.geometry, NetworkFeature.geometry),
            )
            .correlate(Feeder, AOI)
            .exists()
        )
        aoi_json = func.jsonb_build_object(
            "id",
            AOI.id,
            "name",
            AOI.name,
            "description",
            AOI.description,
            "geometry_data",
            cast(func.ST_AsGeoJSON(AOI.geometry), JSONB),
        )
        aois_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            aoi_json,
                            AOI.name,
                            AOI.id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(intersecting_feature_exists)
            .correlate(Feeder)
            .scalar_subquery()
        )

        result = await self.session.execute(
            select(
                Feeder.id,
                Feeder.code,
                Feeder.name,
                Feeder.is_active,
                features_data.label("features_data"),
                associations_data.label("associations_data"),
                aois_data.label("aois_data"),
            ).where(Feeder.id == feeder_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return FeederAggregateRow(
            id=row.id,
            code=row.code,
            name=row.name,
            is_active=row.is_active,
            features_data=row.features_data,
            associations_data=row.associations_data,
            aois_data=row.aois_data,
        )
