from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.geojson.geojson import FeatureGeometry


class WorkspaceFeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: Literal["Feature"] = "Feature"
    geometry: FeatureGeometry
    properties: dict[str, Any] = Field(default_factory=dict)


class WorkspaceFeatureCollectionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[WorkspaceFeatureOut]
