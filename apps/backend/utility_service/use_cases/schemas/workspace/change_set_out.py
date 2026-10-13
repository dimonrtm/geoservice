from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.geojson.geojson import GeoJSONLineString


class WorkspaceChangeSetOut(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    feature_id: UUID = Field(alias="featureId")
    vertex_index: int = Field(
        alias="vertexIndex",
        ge=1,
    )
    baseline_geometry: GeoJSONLineString = Field(alias="baselineGeometry")
    operation: Literal["updated"]
