from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)
from seeds.specs.seed_utility_dataset_specs import SeedUtilityDatasetSpec


class SeedUtilityDatasetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feeder_by_code(self, code: str) -> Feeder | None:
        result = await self.session.execute(select(Feeder).where(Feeder.code == code))
        return result.scalars().one_or_none()

    async def create_dataset(self, spec: SeedUtilityDatasetSpec) -> Feeder:
        feeder = Feeder(
            id=spec.feeder.id,
            code=spec.feeder.code,
            name=spec.feeder.name,
            description=spec.feeder.description,
            is_active=spec.feeder.is_active,
        )
        features = [
            NetworkFeature(
                id=feature.id,
                feeder_id=spec.feeder.id,
                asset_code=feature.asset_code,
                feature_type=feature.feature_type,
                geometry=WKTElement(feature.geometry_wkt, srid=4326),
                name=feature.name,
                description=feature.description,
                properties=feature.properties,
            )
            for feature in spec.features
        ]
        self.session.add_all([feeder, *features])
        await self.session.flush()

        associations = [
            NetworkAssociation(
                id=association.id,
                feeder_id=spec.feeder.id,
                from_feature_id=association.from_feature_id,
                to_feature_id=association.to_feature_id,
                association_type=association.association_type,
            )
            for association in spec.associations
        ]
        self.session.add_all(associations)
        await self.session.flush()
        return feeder
