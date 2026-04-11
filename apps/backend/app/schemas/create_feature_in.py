from pydantic import BaseModel, ConfigDict, Field

from .geojson import FeatureGeometry, FeatureProperties


class CreateFeatureIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    geometry: FeatureGeometry
    properties: FeatureProperties = Field(default_factory=dict)
