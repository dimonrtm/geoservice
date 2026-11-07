from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.geojson.geojson import GeoJSONLineString


class FeatureBaselineOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    feature_id: UUID = Field(alias="featureId")
    baseline_geometry: GeoJSONLineString = Field(alias="baselineGeometry")
