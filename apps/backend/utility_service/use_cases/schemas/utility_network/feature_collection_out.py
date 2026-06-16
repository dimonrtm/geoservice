from typing import Literal

from pydantic import BaseModel, ConfigDict

from utility_service.use_cases.schemas.utility_network.geojson_feature_out import (
    UtilityGeoJSONFeatureOut,
)


class UtilityFeatureCollectionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[UtilityGeoJSONFeatureOut]
