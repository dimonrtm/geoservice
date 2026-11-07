from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.edit_version.geometry_contract import BasicValidationOut


class ChangedVertexOut(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    feature_id: UUID = Field(alias="featureId")
    vertex_index: int = Field(
        alias="vertexIndex",
        ge=1,
    )
    operation: Literal["updated"]


class VersionChangeSetOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    draft_version_token: str = Field(
        alias="draftVersionToken",
        min_length=1,
    )
    has_persisted_change_set: bool = Field(alias="hasPersistedChangeSet")
    basic_validation: BasicValidationOut | None = Field(alias="basicValidation")
    change_set: ChangedVertexOut | None = Field(alias="changeSet")
