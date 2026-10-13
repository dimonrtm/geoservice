from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.edit_version.geometry_contract import BasicValidationOut
from utility_service.use_cases.schemas.workspace.change_set_out import WorkspaceChangeSetOut

from utility_service.use_cases.schemas.workspace.association_out import (
    WorkspaceAssociationOut,
)
from utility_service.use_cases.schemas.workspace.feature_out import (
    WorkspaceFeatureCollectionOut,
)


class WorkspaceEditVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: UUID
    status: str
    base_network_revision: int = Field(serialization_alias="baseNetworkRevision")
    draft_version_token: str = Field(
        alias="draftVersionToken",
        min_length=1,
    )
    has_persisted_change_set: bool = Field(alias="hasPersistedChangeSet")
    basic_validation: BasicValidationOut | None = Field(alias="basicValidation")
    change_set: WorkspaceChangeSetOut | None = Field(alias="changeSet")
    features: WorkspaceFeatureCollectionOut
    associations: list[WorkspaceAssociationOut]
