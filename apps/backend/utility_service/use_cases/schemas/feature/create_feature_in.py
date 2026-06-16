from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.geojson.geojson import FeatureGeometry, FeatureProperties


class CreateFeatureIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    geometry: FeatureGeometry
    properties: FeatureProperties = Field(default_factory=dict)
