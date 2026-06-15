from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.geojson import FeatureGeometry


class UtilityGeoJSONFeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: Literal["Feature"] = "Feature"
    geometry: FeatureGeometry
    properties: dict[str, Any] = Field(default_factory=dict)
