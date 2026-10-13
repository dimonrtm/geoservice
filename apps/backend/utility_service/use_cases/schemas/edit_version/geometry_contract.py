from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.geojson.geojson import GeoJSONLineString


class BasicValidationOut(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    geometry_status: Literal["passed"] = Field(alias="geometryStatus")
    aoi_status: Literal["passed"] = Field(alias="aoiStatus")
    positional_accuracy_status: Literal["POSITIONAL_ACCURACY_UNVERIFIED"] = Field(
        alias="positionalAccuracyStatus",
    )
    dirty_relative_to_baseline: Literal["passed"] = Field(alias="dirtyRelativeToBaseline")


class UpdatedFeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    geometry: GeoJSONLineString


class GeometrySaveResponseOut(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    command_id: UUID = Field(alias="commandId")
    command_state: Literal["succeeded"] = Field(alias="commandState")
    draft_version_token: str = Field(
        alias="draftVersionToken",
        min_length=1,
    )
    operation: Literal["unchanged", "updated"]
    has_persisted_change_set: bool = Field(alias="hasPersistedChangeSet")
    updated_feature: UpdatedFeatureOut = Field(alias="updatedFeature")
    basic_validation: BasicValidationOut | None = Field(alias="basicValidation")
