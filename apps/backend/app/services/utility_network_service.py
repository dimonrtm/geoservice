from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions.utility_network_api_error import UtilityNetworkApiError
from repositories.utility_network_repository import UtilityNetworkRepository
from schemas.utility_network import (
    UtilityAssociationOut,
    UtilityFeatureCollectionOut,
    UtilityFeederOut,
    UtilityGeoJSONFeatureOut,
)


class UtilityNetworkService:
    def __init__(
        self,
        session: AsyncSession,
        repository: UtilityNetworkRepository,
    ):
        self.session = session
        self.repository = repository

    async def get_feeder(self, feeder_id: UUID) -> UtilityFeederOut:
        aggregate = await self.repository.get_feeder_aggregate(feeder_id)
        if aggregate is None:
            raise UtilityNetworkApiError(
                404,
                "FEEDER_NOT_FOUND",
                "Фидер не найден.",
            )

        try:
            feature_ids = {UUID(str(feature["id"])) for feature in aggregate.features_data}
            if any(
                UUID(str(association["from_feature_id"])) not in feature_ids
                or UUID(str(association["to_feature_id"])) not in feature_ids
                for association in aggregate.associations_data
            ):
                raise self.invalid_dataset_error()

            network_features = [
                UtilityGeoJSONFeatureOut(
                    id=feature["id"],
                    geometry=feature["geometry_data"],
                    properties=self.network_properties(feature),
                )
                for feature in aggregate.features_data
            ]
            aoi_features = [
                UtilityGeoJSONFeatureOut(
                    id=aoi["id"],
                    geometry=aoi["geometry_data"],
                    properties={
                        "name": aoi["name"],
                        "description": aoi["description"],
                    },
                )
                for aoi in aggregate.aois_data
            ]
            return UtilityFeederOut(
                id=aggregate.id,
                code=aggregate.code,
                name=aggregate.name,
                is_active=aggregate.is_active,
                aois=UtilityFeatureCollectionOut(features=aoi_features),
                network=UtilityFeatureCollectionOut(features=network_features),
                associations=[
                    UtilityAssociationOut(**association)
                    for association in aggregate.associations_data
                ],
            )
        except UtilityNetworkApiError:
            raise
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise self.invalid_dataset_error() from exc

    def network_properties(self, feature: dict[str, Any]) -> dict[str, Any]:
        stored_properties = dict(feature["properties"])
        return {
            **stored_properties,
            "assetCode": feature["asset_code"],
            "featureType": feature["feature_type"],
            "name": feature["name"],
            "description": feature["description"],
            "version": feature["version"],
        }

    def invalid_dataset_error(self) -> UtilityNetworkApiError:
        return UtilityNetworkApiError(
            500,
            "UTILITY_DATASET_INVALID",
            "Utility dataset поврежден и не может быть прочитан.",
        )
