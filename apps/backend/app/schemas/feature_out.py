from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .geojson import FeatureGeometry, FeatureProperties


class FeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    type: Literal["Feature"] = "Feature"
    version: int
    geometry: FeatureGeometry
    properties: FeatureProperties = Field(default_factory=dict)
